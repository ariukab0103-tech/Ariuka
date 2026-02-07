import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Assessment, AssessmentAccess, Response, Attachment, AssessmentDocument, User
from app.ssbj_criteria import (
    SSBJ_CRITERIA, MATURITY_LEVELS, OBLIGATION_LABELS, LA_SCOPE_LABELS, LA_PRIORITY_LABELS,
    get_criteria_by_pillar,
)


def _require_access(assessment, required="view"):
    """Check current_user has at least `required` permission. Returns None if OK, or redirect."""
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not assessment.user_can(current_user, required):
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    return None


def _allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]


def _save_uploaded_file(file):
    """Save an uploaded file and return (stored_name, original_name, file_size)."""
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    stored_name = f"{uuid.uuid4().hex}.{ext}"

    file.save(os.path.join(upload_dir, stored_name))
    file_size = os.path.getsize(os.path.join(upload_dir, stored_name))
    return stored_name, original_name, file_size


assessment_bp = Blueprint("assessment", __name__, url_prefix="/assessments")


@assessment_bp.route("/")
@login_required
def list_assessments():
    from sqlalchemy.orm import joinedload
    if current_user.is_admin:
        assessments = Assessment.query.options(
            joinedload(Assessment.author)
        ).order_by(Assessment.updated_at.desc()).all()
        shared_assessments = []
    else:
        # Own assessments
        assessments = (
            Assessment.query.filter_by(user_id=current_user.id)
            .order_by(Assessment.updated_at.desc())
            .all()
        )
        # Assessments shared with me — single efficient query
        shared_assessments = (
            Assessment.query
            .join(AssessmentAccess, AssessmentAccess.assessment_id == Assessment.id)
            .filter(AssessmentAccess.user_id == current_user.id)
            .options(joinedload(Assessment.author))
            .order_by(Assessment.updated_at.desc())
            .all()
        )
    return render_template(
        "assessment/list.html",
        assessments=assessments,
        shared_assessments=shared_assessments,
    )


@assessment_bp.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        entity_name = request.form.get("entity_name", "").strip()
        fiscal_year = request.form.get("fiscal_year", "").strip()

        if not title or not entity_name or not fiscal_year:
            flash("All fields are required.", "danger")
        else:
            assessment = Assessment(
                title=title,
                entity_name=entity_name,
                fiscal_year=fiscal_year,
                user_id=current_user.id,
                status="draft",
            )
            db.session.add(assessment)
            db.session.flush()

            # Create response entries for all SSBJ criteria
            for criterion in SSBJ_CRITERIA:
                resp = Response(
                    assessment_id=assessment.id,
                    criterion_id=criterion["id"],
                    pillar=criterion["pillar"],
                    category=criterion["category"],
                    standard=criterion["standard"],
                )
                db.session.add(resp)

            db.session.commit()
            flash("Assessment created successfully.", "success")
            return redirect(
                url_for("assessment.view", assessment_id=assessment.id)
            )
    return render_template("assessment/create.html")


@assessment_bp.route("/<int:assessment_id>")
@login_required
def view(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    criteria_by_pillar = get_criteria_by_pillar()

    # Auto-sync: add response rows for any new criteria not yet in this assessment
    existing_ids = {r.criterion_id for r in assessment.responses.all()}
    new_criteria = [c for c in SSBJ_CRITERIA if c["id"] not in existing_ids]
    if new_criteria:
        for c in new_criteria:
            resp = Response(
                assessment_id=assessment.id,
                criterion_id=c["id"],
                pillar=c["pillar"],
                category=c["category"],
                standard=c["standard"],
            )
            db.session.add(resp)
        db.session.commit()

    # Single query for all responses (avoid N+1)
    all_responses = assessment.responses.all()
    responses = {r.criterion_id: r for r in all_responses}
    documents = assessment.documents.order_by(AssessmentDocument.uploaded_at.desc()).all()

    total_count = len(all_responses)
    scored_count = sum(1 for r in all_responses if r.score is not None)
    unanswered_count = total_count - scored_count
    ai_enabled = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    user_perm = assessment.user_permission(current_user)
    can_edit = user_perm in ("owner", "manage", "edit")
    can_manage = user_perm in ("owner", "manage")

    # Team members for sharing panel — eager-load user relationships
    team_members = []
    all_users = []
    if can_manage:
        from sqlalchemy.orm import joinedload
        team_members = assessment.team_access.options(
            joinedload(AssessmentAccess.user),
            joinedload(AssessmentAccess.grantor),
        ).all()
        all_users = User.query.filter(
            User.id != assessment.user_id
        ).order_by(User.full_name).all()

    return render_template(
        "assessment/view.html",
        assessment=assessment,
        criteria_by_pillar=criteria_by_pillar,
        responses=responses,
        documents=documents,
        total_count=total_count,
        scored_count=scored_count,
        unanswered_count=unanswered_count,
        ai_enabled=ai_enabled,
        user_perm=user_perm,
        can_edit=can_edit,
        can_manage=can_manage,
        team_members=team_members,
        all_users=all_users,
        maturity_levels=MATURITY_LEVELS,
        obligation_labels=OBLIGATION_LABELS,
        la_scope_labels=LA_SCOPE_LABELS,
        la_priority_labels=LA_PRIORITY_LABELS,
    )


@assessment_bp.route("/<int:assessment_id>/edit-settings", methods=["POST"])
@login_required
def edit_settings(assessment_id):
    """Edit assessment settings: title, entity name, fiscal year."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    title = request.form.get("title", "").strip()
    entity_name = request.form.get("entity_name", "").strip()
    fiscal_year = request.form.get("fiscal_year", "").strip()

    if not title or not entity_name or not fiscal_year:
        flash("Title, entity name, and fiscal year are required.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    changed = []
    if assessment.title != title:
        assessment.title = title
        changed.append("title")
    if assessment.entity_name != entity_name:
        assessment.entity_name = entity_name
        changed.append("entity name")
    if assessment.fiscal_year != fiscal_year:
        assessment.fiscal_year = fiscal_year
        changed.append("fiscal year")

    if changed:
        db.session.commit()
        flash(f"Updated: {', '.join(changed)}. Roadmap will reflect the new fiscal year.", "success")
    else:
        flash("No changes made.", "info")

    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/assess/<string:criterion_id>", methods=["GET", "POST"])
@login_required
def assess_criterion(assessment_id, criterion_id):
    assessment = db.session.get(Assessment, assessment_id)
    # GET=view, POST=edit
    required = "edit" if request.method == "POST" else "view"
    denied = _require_access(assessment, required)
    if denied:
        return denied

    response = Response.query.filter_by(
        assessment_id=assessment_id, criterion_id=criterion_id
    ).first()
    if not response:
        flash("Criterion not found in this assessment.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    # Find the criterion definition
    criterion = None
    for c in SSBJ_CRITERIA:
        if c["id"] == criterion_id:
            criterion = c
            break

    if request.method == "POST":
        score = request.form.get("score")
        response.score = int(score) if score and score.isdigit() else None
        response.evidence = request.form.get("evidence", "")
        response.notes = request.form.get("notes", "")

        if assessment.status == "draft":
            assessment.status = "in_progress"

        db.session.commit()
        flash(f"Response for {criterion_id} saved.", "success")

        # Navigate to next criterion
        next_criterion = _get_next_criterion(criterion_id)
        if next_criterion:
            return redirect(
                url_for(
                    "assessment.assess_criterion",
                    assessment_id=assessment_id,
                    criterion_id=next_criterion,
                )
            )
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    return render_template(
        "assessment/assess.html",
        assessment=assessment,
        criterion=criterion,
        response=response,
        maturity_levels=MATURITY_LEVELS,
        obligation_labels=OBLIGATION_LABELS,
        la_scope_labels=LA_SCOPE_LABELS,
        la_priority_labels=LA_PRIORITY_LABELS,
    )


@assessment_bp.route("/<int:assessment_id>/bulk-save", methods=["POST"])
@login_required
def bulk_save(assessment_id):
    """Save all inline score changes — supports both form POST and AJAX JSON."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        if request.is_json:
            return jsonify({"ok": False, "error": "Access denied"}), 403
        return denied

    is_ajax = request.is_json
    scores = request.get_json() if is_ajax else None

    updated = 0
    scored_count = 0
    total_count = 0
    for resp in assessment.responses.all():
        total_count += 1
        form_key = f"score_{resp.criterion_id}"
        if is_ajax:
            score_val = str(scores.get(form_key, "")) if scores else ""
        else:
            score_val = request.form.get(form_key, "")

        if score_val.isdigit():
            new_score = int(score_val)
            if resp.score != new_score:
                resp.score = new_score
                updated += 1
            scored_count += 1
        elif score_val == "" and resp.score is not None:
            resp.score = None
            updated += 1
        elif resp.score is not None:
            scored_count += 1

    if assessment.status == "draft" and updated > 0:
        assessment.status = "in_progress"

    db.session.commit()

    if is_ajax:
        pct = round(scored_count / total_count * 100) if total_count else 0
        return jsonify({
            "ok": True,
            "updated": updated,
            "scored_count": scored_count,
            "total_count": total_count,
            "completion_pct": pct,
            "overall_score": assessment.overall_score,
        })

    if updated > 0:
        flash(f"Saved {updated} score change(s).", "success")
    else:
        flash("No changes to save.", "info")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/complete", methods=["POST"])
@login_required
def complete(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    unanswered = assessment.responses.filter(Response.score.is_(None)).count()
    if unanswered > 0:
        flash(f"{unanswered} criteria still unanswered. Please complete all items.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    assessment.status = "completed"
    db.session.commit()
    flash("Assessment marked as completed.", "success")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/roadmap")
@login_required
def roadmap(assessment_id):
    """Generate backcasting compliance roadmap."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    from app.roadmap import generate_roadmap
    responses_list = assessment.responses.filter(Response.score.isnot(None)).all()

    if not responses_list:
        flash("No scored criteria yet. Complete the assessment first to generate a roadmap.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    roadmap_data = generate_roadmap(assessment, responses_list)

    return render_template(
        "assessment/roadmap.html",
        assessment=assessment,
        roadmap=roadmap_data,
    )


@assessment_bp.route("/<int:assessment_id>/report")
@login_required
def report(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    criteria_by_pillar = get_criteria_by_pillar()
    responses = {r.criterion_id: r for r in assessment.responses.all()}
    pillar_scores = assessment.pillar_scores()
    category_scores = assessment.category_scores()

    # Identify gaps (score < 3 = below "Defined" maturity)
    gaps = []
    for r in assessment.responses.filter(Response.score.isnot(None)).all():
        if r.score < 3:
            criterion = None
            for c in SSBJ_CRITERIA:
                if c["id"] == r.criterion_id:
                    criterion = c
                    break
            if criterion:
                gaps.append({"response": r, "criterion": criterion})

    return render_template(
        "assessment/report.html",
        assessment=assessment,
        criteria_by_pillar=criteria_by_pillar,
        responses=responses,
        pillar_scores=pillar_scores,
        category_scores=category_scores,
        gaps=gaps,
        maturity_levels=MATURITY_LEVELS,
        obligation_labels=OBLIGATION_LABELS,
        la_scope_labels=LA_SCOPE_LABELS,
        la_priority_labels=LA_PRIORITY_LABELS,
    )


# =========================================================================
# Bulk document upload + auto-assessment
# =========================================================================

@assessment_bp.route("/<int:assessment_id>/bulk-upload", methods=["POST"])
@login_required
def bulk_upload(assessment_id):
    """Upload documents at the assessment level."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    from app.analyzer import extract_text_from_file

    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        flash("No files selected.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    uploaded_count = 0
    for file in files:
        if file.filename == "" or not _allowed_file(file.filename):
            continue

        stored_name, original_name, file_size = _save_uploaded_file(file)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)

        # Extract text
        extracted = extract_text_from_file(filepath)

        doc = AssessmentDocument(
            assessment_id=assessment.id,
            filename=stored_name,
            original_name=original_name,
            file_size=file_size,
            extracted_text=extracted,
            uploaded_by=current_user.id,
        )
        db.session.add(doc)
        uploaded_count += 1

    db.session.commit()
    flash(f"{uploaded_count} document(s) uploaded. Click 'Auto-Assess' to analyze.", "success")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/auto-assess", methods=["GET", "POST"])
@login_required
def auto_assess(assessment_id):
    """Run auto-assessment on all uploaded documents."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    # GET requests redirect back to assessment view
    if request.method == "GET":
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    try:
        from app.analyzer import auto_assess_all

        # Combine text from all assessment documents
        docs = assessment.documents.all()
        if not docs:
            flash("No documents uploaded. Please upload documents first.", "warning")
            return redirect(url_for("assessment.view", assessment_id=assessment_id))

        combined_text = "\n\n".join(d.extracted_text for d in docs if d.extracted_text)
        if not combined_text.strip():
            flash("Could not extract text from uploaded documents. Try PDF, DOCX, XLSX, CSV, or TXT files.", "warning")
            return redirect(url_for("assessment.view", assessment_id=assessment_id))

        # Run auto-assessment (AI if API key set, otherwise keyword fallback)
        results, method, ai_error = auto_assess_all(combined_text)

        # Update responses
        updated = 0
        for resp in assessment.responses.all():
            if resp.criterion_id in results:
                score, evidence, notes = results[resp.criterion_id]
                if score > 0:  # Only update if we found something
                    resp.score = score
                    resp.evidence = evidence
                    resp.notes = notes
                    updated += 1

        if assessment.status in ("draft", "completed", "under_review", "reviewed"):
            assessment.status = "in_progress"

        db.session.commit()

        if method == "ai":
            flash(f"AI assessment complete. {updated} of {len(SSBJ_CRITERIA)} criteria scored by Claude AI. Review and adjust scores as needed.", "success")
        elif ai_error:
            flash(f"AI assessment FAILED: {ai_error}", "danger")
            flash(f"Fell back to keyword-based scoring. {updated} of {len(SSBJ_CRITERIA)} criteria scored. Fix the API issue and try again for accurate AI analysis.", "warning")
        else:
            flash(f"Keyword-based assessment complete. {updated} of {len(SSBJ_CRITERIA)} criteria scored. Set ANTHROPIC_API_KEY for AI-powered analysis.", "warning")

    except Exception as e:
        import traceback
        current_app.logger.error(f"Auto-assess error: {traceback.format_exc()}")
        flash(f"Auto-assessment error: {e}", "danger")

    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/delete-doc/<int:doc_id>", methods=["POST"])
@login_required
def delete_document(assessment_id, doc_id):
    """Delete an assessment-level document."""
    doc = db.session.get(AssessmentDocument, doc_id)
    if not doc:
        flash("Document not found.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], doc.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(doc)
    db.session.commit()
    flash("Document deleted.", "success")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


# =========================================================================
# Per-criterion file upload
# =========================================================================

@assessment_bp.route("/<int:assessment_id>/upload/<string:criterion_id>", methods=["POST"])
@login_required
def upload_file(assessment_id, criterion_id):
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    response = Response.query.filter_by(
        assessment_id=assessment_id, criterion_id=criterion_id
    ).first()
    if not response:
        flash("Criterion not found.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    if "file" not in request.files:
        flash("No file selected.", "warning")
        return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))

    file = request.files["file"]
    if file.filename == "":
        flash("No file selected.", "warning")
        return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))

    if not _allowed_file(file.filename):
        allowed = ", ".join(current_app.config["ALLOWED_EXTENSIONS"])
        flash(f"File type not allowed. Accepted: {allowed}", "danger")
        return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))

    stored_name, original_name, file_size = _save_uploaded_file(file)

    attachment = Attachment(
        response_id=response.id,
        filename=stored_name,
        original_name=original_name,
        file_size=file_size,
        uploaded_by=current_user.id,
    )
    db.session.add(attachment)
    db.session.commit()

    flash(f"File '{original_name}' uploaded.", "success")
    return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))


@assessment_bp.route("/download/<int:attachment_id>")
@login_required
def download_file(attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        flash("File not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir, attachment.filename, download_name=attachment.original_name
    )


@assessment_bp.route("/download-doc/<int:doc_id>")
@login_required
def download_document(doc_id):
    doc = db.session.get(AssessmentDocument, doc_id)
    if not doc:
        flash("File not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    return send_from_directory(
        upload_dir, doc.filename, download_name=doc.original_name
    )


@assessment_bp.route("/<int:assessment_id>/delete-file/<int:attachment_id>", methods=["POST"])
@login_required
def delete_file(assessment_id, attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        flash("File not found.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "edit")
    if denied:
        return denied

    criterion_id = attachment.response.criterion_id

    # Delete physical file
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], attachment.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(attachment)
    db.session.commit()
    flash("File deleted.", "success")
    return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))


# =========================================================================
# Team sharing
# =========================================================================

@assessment_bp.route("/<int:assessment_id>/share", methods=["POST"])
@login_required
def share_assessment(assessment_id):
    """Add or update a team member's access."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "manage")
    if denied:
        return denied

    user_id = request.form.get("user_id", type=int)
    permission = request.form.get("permission", "view")
    if permission not in ("view", "edit", "manage"):
        permission = "view"

    if not user_id:
        flash("Please select a user.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    if user_id == assessment.user_id:
        flash("The owner already has full access.", "info")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    target_user = db.session.get(User, user_id)
    if not target_user:
        flash("User not found.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    # Update existing or create new
    existing = AssessmentAccess.query.filter_by(
        assessment_id=assessment_id, user_id=user_id
    ).first()
    if existing:
        existing.permission = permission
        flash(f"Updated {target_user.full_name}'s access to '{permission}'.", "success")
    else:
        access = AssessmentAccess(
            assessment_id=assessment_id,
            user_id=user_id,
            permission=permission,
            granted_by=current_user.id,
        )
        db.session.add(access)
        flash(f"Shared with {target_user.full_name} ({permission} access).", "success")

    db.session.commit()
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/unshare/<int:access_id>", methods=["POST"])
@login_required
def unshare_assessment(assessment_id, access_id):
    """Remove a team member's access."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "manage")
    if denied:
        return denied

    access = db.session.get(AssessmentAccess, access_id)
    if access and access.assessment_id == assessment_id:
        name = access.user.full_name
        db.session.delete(access)
        db.session.commit()
        flash(f"Removed {name}'s access.", "success")

    return redirect(url_for("assessment.view", assessment_id=assessment_id))


def _get_next_criterion(current_id):
    """Get the next criterion ID in sequence."""
    ids = [c["id"] for c in SSBJ_CRITERIA]
    try:
        idx = ids.index(current_id)
        if idx + 1 < len(ids):
            return ids[idx + 1]
    except ValueError:
        pass
    return None


# =========================================================================
# Consultant Report Review (AI-Powered with Keyword Fallback)
# =========================================================================


def _ai_analyze_consultant_report(consultant_text, criteria_map, responses_map, roadmap_data):
    """Use Claude AI to analyze consultant report against SSBJ requirements and our assessment.

    Returns (results, all_matched_ids, comparison) or None if AI unavailable.
    Runs the API call in a separate thread to prevent Gunicorn worker crashes.
    """
    import json as _json
    import re
    import logging
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

    logger = logging.getLogger(__name__)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None

    try:
        import anthropic
    except ImportError:
        return None

    # Build context: criteria + our scores (compact format to reduce token count)
    criteria_context = []
    for c in SSBJ_CRITERIA:
        resp = responses_map.get(c["id"])
        score = resp.score if resp and resp.score is not None else None
        score_str = f"{score}/5" if score is not None else "N/A"
        criteria_context.append(
            f"{c['id']}|{c['pillar']}|{c['category']}|{c['obligation']}|{c['la_scope']}|Score:{score_str}"
        )
    criteria_text = "\n".join(criteria_context)

    # Build roadmap context
    roadmap_context = ""
    if roadmap_data:
        la_critical = roadmap_data.get("gaps", {}).get("la_critical", [])
        la_ids = [g["id"] for g in la_critical]
        roadmap_context = (
            f"Timeline: {roadmap_data.get('months_remaining', '?')} months remaining | "
            f"Urgency: {roadmap_data.get('urgency', '?')} | "
            f"Total gaps (score<3): {roadmap_data.get('gaps', {}).get('total_gaps', '?')} | "
            f"LA-critical gaps: {len(la_critical)} ({', '.join(la_ids)})"
        )

    # Truncate consultant text if needed
    max_chars = 15000
    truncated = consultant_text[:max_chars] if len(consultant_text) > max_chars else consultant_text

    system_prompt = """You are an expert SSBJ/ISSB sustainability auditor comparing a consultant's report against our SSBJ gap assessment results.

Key SSBJ facts:
- 25 criteria: Governance(5), Strategy(6), Risk Management(5), Metrics & Targets(9)
- Mandatory(SHALL) vs Recommended(SHOULD) vs Interpretive
- Limited assurance scope (first 2 yrs): Scope 1&2, Governance, Risk Management (ISSA 5000)
- Value chain (STR-01,02), Scope 3 all 15 categories (MET-03), GHG Intensity (MET-08), Climate Remuneration (MET-09) = MANDATORY
- Carbon offsets ≠ emission reductions. ISSA 5000 replaces ISAE 3000/3410 from Dec 2026

Classify each consultant suggestion: essential (mandatory + our gap), recommended (useful beyond minimum), already_covered (score>=3), out_of_scope, unnecessary (misleading for SSBJ)."""

    user_prompt = f"""ASSESSMENT SCORES:
{criteria_text}

ROADMAP: {roadmap_context}

CONSULTANT REPORT:
{truncated}

Return ONLY JSON:
{{"suggestions":[{{"text":"summary","verdict":"essential|recommended|already_covered|out_of_scope|unnecessary","matched_criteria":["GOV-01"],"explanation":"comparison"}}],"overall_comparison":{{"critical_observations":[{{"type":"danger|warning|success|info","title":"title","detail":"detail"}}],"differences":[{{"area":"area","our_approach":"ours","consultant_note":"theirs"}}],"missing_from_consultant":["IDs"]}}}}"""

    def _call_api():
        """Run API call in thread so Gunicorn SIGABRT can't kill the worker."""
        client = anthropic.Anthropic(api_key=api_key, timeout=60.0)
        return client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=4000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )

    try:
        # Run in separate thread with hard 60s timeout
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_api)
            response = future.result(timeout=60)

        response_text = response.content[0].text.strip()

        # Extract JSON (handle potential markdown code blocks)
        if response_text.startswith("```"):
            response_text = re.sub(r'^```(?:json)?\s*\n?', '', response_text)
            response_text = re.sub(r'\n?```\s*$', '', response_text)

        ai_result = _json.loads(response_text)

        # Convert AI results to our standard format
        results = []
        all_matched_ids = set()
        verdict_colors = {
            "essential": ("danger", "exclamation-triangle-fill"),
            "recommended": ("warning", "info-circle"),
            "already_covered": ("success", "check-circle"),
            "out_of_scope": ("secondary", "question-circle"),
            "unnecessary": ("secondary", "x-circle"),
        }

        for item in ai_result.get("suggestions", []):
            verdict = item.get("verdict", "out_of_scope")
            color, icon = verdict_colors.get(verdict, ("secondary", "question-circle"))
            matched_ids = item.get("matched_criteria", [])
            all_matched_ids.update(matched_ids)

            # Build matched criteria details
            mc_details = []
            for cid in matched_ids:
                c = criteria_map.get(cid)
                if c:
                    resp = responses_map.get(cid)
                    mc_details.append(_criterion_summary(c, resp))

            results.append({
                "text": item.get("text", ""),
                "verdict": verdict,
                "explanation": item.get("explanation", ""),
                "matched_criteria": mc_details,
                "icon": icon,
                "color": color,
            })

        # Build comparison from AI output
        overall = ai_result.get("overall_comparison", {})
        comparison = {
            "our_urgency": roadmap_data.get("urgency", "") if roadmap_data else "",
            "our_months": roadmap_data.get("months_remaining", 0) if roadmap_data else 0,
            "our_total_gaps": roadmap_data.get("gaps", {}).get("total_gaps", 0) if roadmap_data else 0,
            "our_la_critical": len(roadmap_data.get("gaps", {}).get("la_critical", [])) if roadmap_data else 0,
            "our_phases": len(roadmap_data.get("phases", [])) if roadmap_data else 0,
            "critical_observations": overall.get("critical_observations", []),
            "differences": overall.get("differences", []),
        }

        return results, all_matched_ids, comparison

    except FuturesTimeout:
        logger.warning("AI consultant analysis timed out (60s), falling back to keyword matching")
        return None
    except BaseException as e:
        # Catch BaseException to handle SystemExit from Gunicorn SIGABRT
        logger.warning(f"AI consultant analysis failed: {type(e).__name__}: {e}")
        return None


def _build_keyword_index():
    """Build keyword-to-criterion mapping for matching consultant suggestions.

    IMPORTANT: SSBJ requires disclosure across ALL four pillars even for items
    not in initial limited assurance scope. Value chain analysis, Scope 3,
    scenario analysis, etc. are ALL mandatory.
    Initial LA scope (first 2 years): Scope 1 & 2, Governance, Risk Management.
    """
    import re
    index = {}
    for c in SSBJ_CRITERIA:
        keywords = set()
        # Extract meaningful keywords from requirement, minimum_action, category
        for field in ("requirement", "minimum_action", "best_practice", "category", "guidance"):
            text = c.get(field, "")
            words = re.findall(r"[a-zA-Z]{4,}", text.lower())
            keywords.update(words)

        # Add specific domain keywords per criterion topic
        cid = c["id"]
        combined_text = (c.get("requirement", "") + " " + c.get("minimum_action", "")).lower()

        # Scope 1 keywords
        if "scope 1" in combined_text or cid == "MET-01":
            keywords.update(["scope1", "scope", "direct", "emissions", "ghg", "greenhouse",
                             "fuel", "combustion", "stationary", "mobile", "fugitive", "refrigerant"])
        # Scope 2 keywords
        if "scope 2" in combined_text or cid == "MET-02":
            keywords.update(["scope2", "indirect", "electricity", "purchased", "grid",
                             "energy", "utility", "location", "market"])
        # Scope 3 / Value chain keywords (MET-03 and STR-02 are both mandatory)
        if "scope 3" in combined_text or cid == "MET-03":
            keywords.update(["scope3", "value", "chain", "supply", "upstream", "downstream",
                             "supplier", "procurement", "logistics", "transport", "categories",
                             "purchased", "goods", "services", "travel", "commuting"])
        # Value chain analysis (STR-02 is mandatory)
        if "value chain" in combined_text or cid == "STR-02":
            keywords.update(["value", "chain", "supply", "upstream", "downstream",
                             "business", "model", "impact", "dependency", "supplier",
                             "procurement", "customer", "distribution"])
        # Risk and opportunity analysis (STR-01, RSK-01, RSK-02 are all mandatory)
        if cid in ("STR-01", "RSK-01", "RSK-02"):
            keywords.update(["risk", "opportunity", "opportunities", "risks", "identify",
                             "assessment", "materiality", "material", "register", "impact",
                             "likelihood", "prioritize", "monitor"])
        # Climate scenario analysis (STR-04 is mandatory)
        if cid == "STR-04":
            keywords.update(["scenario", "analysis", "resilience", "pathway",
                             "transition", "physical", "temperature", "paris", "degrees"])
        # Financial impact (STR-03 is mandatory)
        if cid == "STR-03":
            keywords.update(["financial", "impact", "position", "performance",
                             "cashflow", "cash", "flows", "balance", "sheet"])
        # Transition plan (STR-05)
        if cid == "STR-05":
            keywords.update(["transition", "plan", "decarbonization", "decarbonisation",
                             "target", "pathway", "roadmap", "reduction"])
        # Board oversight (GOV-01, GOV-02 are in LA scope)
        if cid in ("GOV-01", "GOV-02"):
            keywords.update(["board", "oversight", "committee", "governance", "mandate",
                             "charter", "terms", "reference", "sustainability", "esg",
                             "director", "directors", "responsible", "supervisory"])
        # Management role (GOV-04 is in LA scope)
        if cid == "GOV-04":
            keywords.update(["management", "role", "manager", "officer", "cso",
                             "sustainability", "responsible", "monitoring", "reporting",
                             "cross", "functional", "working", "group"])
        # Climate governance (GOV-05 is in LA scope)
        if cid == "GOV-05":
            keywords.update(["climate", "decision", "investment", "capital", "carbon", "pricing"])
        # Risk integration (RSK-03 is now in LA scope)
        if cid == "RSK-03":
            keywords.update(["integration", "integrate", "erm", "enterprise", "overall",
                             "combined", "unified", "framework", "holistic"])
        # Internal controls (RSK-05 is in LA scope)
        if cid == "RSK-05":
            keywords.update(["internal", "controls", "audit", "trail", "maker", "checker",
                             "review", "segregation", "duties", "data", "quality", "icsr"])
        # Climate risk (RSK-04 is mandatory)
        if cid == "RSK-04":
            keywords.update(["climate", "physical", "transition", "acute", "chronic",
                             "flood", "heat", "policy", "technology", "reputation"])
        # Data quality (MET-07 is in LA scope)
        if cid == "MET-07":
            keywords.update(["data", "quality", "completeness", "accuracy", "validation",
                             "governance", "lineage", "reconciliation", "error"])
        # Climate targets (MET-04 is mandatory)
        if cid == "MET-04":
            keywords.update(["target", "targets", "reduction", "base", "year",
                             "milestone", "sbti", "science", "based", "netzero", "zero"])
        # GHG emissions intensity (MET-08 is mandatory)
        if cid == "MET-08":
            keywords.update(["intensity", "ratio", "per", "unit", "revenue",
                             "output", "employee", "denominator", "normalized"])
        # Climate-related remuneration (MET-09 is mandatory)
        if cid == "MET-09":
            keywords.update(["remuneration", "compensation", "executive", "incentive",
                             "bonus", "salary", "linked", "performance", "kpi"])

        # General pillar keywords
        if c["pillar"] == "Governance":
            keywords.update(["board", "governance", "oversight", "committee"])
        if c["pillar"] == "Strategy":
            keywords.update(["strategy", "strategic"])
        if c["pillar"] == "Risk Management":
            keywords.update(["risk", "controls", "management"])
        if c["pillar"] == "Metrics & Targets":
            keywords.update(["metrics", "targets", "data", "calculation", "emissions"])

        index[c["id"]] = keywords
    return index


def _match_suggestion_to_criteria(suggestion_text, keyword_index, criteria_map):
    """Match a single suggestion to relevant SSBJ criteria.

    Returns list of (criterion_id, relevance_score) tuples.
    """
    import re
    words = set(re.findall(r"[a-zA-Z]{4,}", suggestion_text.lower()))
    # Also check for explicit criterion IDs like GOV-01, MET-03
    explicit_ids = re.findall(r"(GOV|STR|RSK|MET)-\d{2}", suggestion_text.upper())

    matches = []
    for cid, kw_set in keyword_index.items():
        overlap = len(words & kw_set)
        # Bonus for explicit criterion ID mention
        if cid in explicit_ids:
            overlap += 20
        if overlap >= 3:  # minimum threshold
            matches.append((cid, overlap))

    matches.sort(key=lambda x: x[1], reverse=True)
    return matches[:3]  # top 3 matches


def _classify_suggestion(suggestion_text, matched_criteria, criteria_map, responses_map):
    """Classify a consultant suggestion and give an opinion.

    Returns dict with:
    - verdict: "essential" / "recommended" / "already_covered" / "out_of_scope" / "unnecessary"
    - explanation: why
    - matched_criteria: list of matched criterion details
    """
    import re
    text_lower = suggestion_text.lower()

    # Check for truly unnecessary items — only flag things NOT required by SSBJ
    # IMPORTANT: Scope 3, value chain analysis, and risk/opportunity assessments
    # are ALL mandatory under SSBJ even if not in initial limited assurance scope.
    # Do NOT flag those as unnecessary.
    unnecessary_patterns = [
        (r"blockchain|nft|web3", "Blockchain/NFT technology is not required for SSBJ compliance. This is a common consultant upsell. Standard databases and spreadsheets with audit trails are fully sufficient for assurance purposes."),
        (r"real.?time\s+dashboard", "Real-time dashboards are nice-to-have but not required. SSBJ requires annual disclosure, not real-time monitoring. Consultants may suggest this to increase project scope and fees."),
        (r"carbon\s+offset|carbon\s+credit|offset\s+purchase", "Carbon offsets/credits are NOT part of Scope 1 & 2 emission reporting under SSBJ. Purchasing offsets does not reduce your reported emissions. If a consultant suggests this for SSBJ compliance, they are confusing emission reporting with carbon neutrality claims."),
        (r"cdp.*report|sustainability\s+rating|esg\s+rating|sustainalytics|msci\s+esg", "ESG ratings and CDP reporting are separate from SSBJ mandatory disclosure. While useful, they are NOT required for SSBJ compliance. Consultants may bundle these to increase project scope."),
    ]
    for pattern, reason in unnecessary_patterns:
        if re.search(pattern, text_lower):
            return {
                "verdict": "unnecessary",
                "explanation": reason,
                "matched_criteria": [],
                "icon": "x-circle",
                "color": "secondary",
            }

    # Items that are legitimate SSBJ requirements but worth noting context
    # These are NOT unnecessary — they map to mandatory criteria — but may need
    # prioritization guidance relative to initial LA scope
    context_patterns = [
        (r"ai.?powered|machine\s+learning|artificial\s+intelligence",
         "AI/ML tools are not required for SSBJ compliance but not harmful. Manual processes with proper controls are fully acceptable. Evaluate cost-benefit before committing."),
        (r"comprehensive\s+esg\s+platform|all.in.one\s+esg|esg\s+software\s+suite",
         "A comprehensive ESG platform may be useful but is not required. For initial compliance, controlled spreadsheets can satisfy assurance requirements. Consider phasing in software after first year."),
    ]
    for pattern, note in context_patterns:
        if re.search(pattern, text_lower):
            # Don't return "unnecessary" — continue to normal matching with added context
            # This will be handled by normal matching below
            break

    if not matched_criteria:
        return {
            "verdict": "out_of_scope",
            "explanation": "This suggestion does not clearly map to any SSBJ disclosure requirement. It may be general consulting advice rather than SSBJ-specific.",
            "matched_criteria": [],
            "icon": "question-circle",
            "color": "secondary",
        }

    # Get the best-matching criterion
    best_id = matched_criteria[0][0]
    best_c = criteria_map.get(best_id, {})
    resp = responses_map.get(best_id)

    # Check if already covered (score >= 3)
    if resp and resp.score is not None and resp.score >= 3:
        return {
            "verdict": "already_covered",
            "explanation": f"Your assessment already scores {best_c.get('category', best_id)} at {resp.score}/5. This suggestion may be redundant — you've already met the minimum threshold.",
            "matched_criteria": [_criterion_summary(best_c, resp)],
            "icon": "check-circle",
            "color": "success",
        }

    # Determine necessity based on obligation and LA scope
    # IMPORTANT: SSBJ mandates disclosure across all pillars. Items not in initial
    # LA scope are still mandatory for disclosure — they just won't be assured in
    # the first year. Value chain analysis, Scope 3, scenario analysis, etc. are
    # all mandatory even though initial LA covers Scope 1 & 2, Governance, and Risk Mgmt.
    obligation = best_c.get("obligation", "")
    la_scope = best_c.get("la_scope", "")

    if obligation == "mandatory" and la_scope == "in_scope":
        verdict = "essential"
        explanation = (
            f"ESSENTIAL — HIGHEST PRIORITY. This maps to {best_id} ({best_c.get('category', '')}) "
            f"which is mandatory AND in limited assurance scope. Your auditor will directly examine this. "
            f"Address this before anything else."
        )
        color = "danger"
        icon = "exclamation-triangle-fill"
    elif obligation == "mandatory" and la_scope == "supporting":
        verdict = "essential"
        explanation = (
            f"ESSENTIAL for compliance. This maps to {best_id} ({best_c.get('category', '')}) "
            f"which is mandatory under SSBJ and supports assurance readiness. "
            f"Not directly assured in year 1 but required for disclosure and may be assured later."
        )
        color = "danger"
        icon = "exclamation-triangle"
    elif obligation == "mandatory":
        # Mandatory but not_in_initial_scope — still required for disclosure!
        verdict = "essential"
        explanation = (
            f"ESSENTIAL — mandatory disclosure requirement. This maps to {best_id} ({best_c.get('category', '')}). "
            f"Not in initial limited assurance scope (first 2 years: Scope 1 & 2, Governance, Risk Mgmt) but IS required for SSBJ-compliant disclosure. "
            f"SSBJ allows proportionality in first year but you must address it."
        )
        color = "danger"
        icon = "exclamation-triangle"
    elif la_scope == "in_scope":
        verdict = "essential"
        explanation = (
            f"ESSENTIAL. While the obligation level is '{obligation}', this is in limited assurance scope. "
            f"Auditors will look at it."
        )
        color = "danger"
        icon = "exclamation-triangle"
    elif obligation == "recommended":
        verdict = "recommended"
        explanation = (
            f"RECOMMENDED but not strictly required (SHOULD, not SHALL). Maps to {best_id} ({best_c.get('category', '')}). "
            f"Good practice but you could defer this if budget/time is tight."
        )
        color = "warning"
        icon = "info-circle"
    else:
        verdict = "recommended"
        explanation = (
            f"NICE TO HAVE. Maps to {best_id} ({best_c.get('category', '')}). "
            f"Interpretive requirement — implement if resources allow."
        )
        color = "info"
        icon = "lightbulb"

    # Add score context
    if resp and resp.score is not None:
        explanation += f" Current score: {resp.score}/5."
        if resp.score < 2:
            explanation += " Significant work needed."
        elif resp.score < 3:
            explanation += " Getting close to threshold."

    criterion_details = [_criterion_summary(best_c, resp)]
    # Add secondary matches
    for cid, _ in matched_criteria[1:]:
        c2 = criteria_map.get(cid, {})
        r2 = responses_map.get(cid)
        criterion_details.append(_criterion_summary(c2, r2))

    return {
        "verdict": verdict,
        "explanation": explanation,
        "matched_criteria": criterion_details,
        "icon": icon,
        "color": color,
    }


def _criterion_summary(criterion, response):
    """Build a summary dict for display."""
    return {
        "id": criterion.get("id", ""),
        "category": criterion.get("category", ""),
        "pillar": criterion.get("pillar", ""),
        "obligation": criterion.get("obligation", ""),
        "la_scope": criterion.get("la_scope", ""),
        "la_priority": criterion.get("la_priority", ""),
        "minimum_action": criterion.get("minimum_action", ""),
        "score": response.score if response and response.score is not None else None,
    }


def _check_missing_essentials(criteria_map, responses_map, matched_ids):
    """Find SSBJ essential items NOT covered by any consultant suggestion."""
    missing = []
    for c in SSBJ_CRITERIA:
        if c["id"] in matched_ids:
            continue
        resp = responses_map.get(c["id"])
        score = resp.score if resp and resp.score is not None else None
        # Only flag if mandatory or in LA scope AND below threshold
        if (c["obligation"] == "mandatory" or c["la_scope"] == "in_scope") and (score is None or score < 3):
            missing.append({
                "id": c["id"],
                "category": c["category"],
                "pillar": c["pillar"],
                "obligation": c["obligation"],
                "la_scope": c["la_scope"],
                "minimum_action": c.get("minimum_action", ""),
                "score": score,
            })
    return missing


@assessment_bp.route("/<int:assessment_id>/review-consultant", methods=["GET", "POST"])
@login_required
def review_consultant(assessment_id):
    """Review external consultant report/proposal against SSBJ requirements using AI analysis."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    results = None
    consultant_text = ""
    summary = None
    roadmap_comparison = None
    analysis_method = "none"

    if request.method == "POST":
      try:
        consultant_text = request.form.get("consultant_text", "").strip()

        # Handle file upload — extract text from uploaded document
        uploaded_file = request.files.get("consultant_file")
        if uploaded_file and uploaded_file.filename:
            try:
                from app.analyzer import extract_text_from_file
                stored_name, original_name, file_size = _save_uploaded_file(uploaded_file)
                filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)
                extracted = extract_text_from_file(filepath)
                if extracted:
                    consultant_text = (consultant_text + "\n\n" + extracted).strip()
                # Clean up temp file
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                flash(f"Could not extract text from uploaded file: {e}", "warning")

        if not consultant_text:
            flash("Please paste text or upload a document with the consultant's suggestions.", "warning")
        else:
            import re
            criteria_map = {c["id"]: c for c in SSBJ_CRITERIA}
            responses_map = {r.criterion_id: r for r in assessment.responses.all()}

            # Generate our roadmap for comparison context
            from app.roadmap import generate_roadmap
            our_roadmap = None
            responses_list = assessment.responses.filter(Response.score.isnot(None)).all()
            if responses_list:
                our_roadmap = generate_roadmap(assessment, responses_list)

            # Try AI-powered analysis first
            ai_result = _ai_analyze_consultant_report(
                consultant_text, criteria_map, responses_map, our_roadmap
            )

            if ai_result is not None:
                # AI analysis succeeded
                results, all_matched_ids, roadmap_comparison = ai_result
                analysis_method = "ai"
            else:
                # Fallback to keyword matching
                analysis_method = "keyword"
                keyword_index = _build_keyword_index()

                # Parse suggestions (split by newlines, numbered items, or bullet points)
                lines = re.split(r"\n+", consultant_text)
                suggestions = []
                for line in lines:
                    cleaned = re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip()
                    if len(cleaned) > 10:
                        suggestions.append(cleaned)

                results = []
                all_matched_ids = set()
                for suggestion in suggestions:
                    matches = _match_suggestion_to_criteria(suggestion, keyword_index, criteria_map)
                    classification = _classify_suggestion(suggestion, matches, criteria_map, responses_map)
                    results.append({
                        "text": suggestion,
                        **classification,
                    })
                    for cid, _ in matches:
                        all_matched_ids.add(cid)

                if our_roadmap:
                    roadmap_comparison = _compare_with_roadmap(our_roadmap, results, all_matched_ids, criteria_map)

            # Find missing essentials (works for both AI and keyword)
            missing = _check_missing_essentials(criteria_map, responses_map, all_matched_ids)

            # Summary statistics
            verdicts = [r["verdict"] for r in results]
            summary = {
                "total": len(results),
                "essential": verdicts.count("essential"),
                "recommended": verdicts.count("recommended"),
                "already_covered": verdicts.count("already_covered"),
                "out_of_scope": verdicts.count("out_of_scope"),
                "unnecessary": verdicts.count("unnecessary"),
                "missing_essentials": missing,
                "coverage_pct": round(
                    (len(all_matched_ids) / len(SSBJ_CRITERIA)) * 100
                ) if SSBJ_CRITERIA else 0,
                "total_criteria": len(SSBJ_CRITERIA),
                "analysis_method": analysis_method,
            }
      except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).error(f"Consultant review error: {e}\n{traceback.format_exc()}")
        flash(f"Analysis error: {type(e).__name__}: {e}", "danger")

    return render_template(
        "assessment/review_consultant.html",
        assessment=assessment,
        results=results,
        summary=summary,
        consultant_text=consultant_text,
        roadmap_comparison=roadmap_comparison,
    )


def _compare_with_roadmap(our_roadmap, consultant_results, matched_ids, criteria_map):
    """Compare consultant suggestions against our generated roadmap.

    Returns a comparison dict highlighting differences and critical analysis.
    """
    comparison = {
        "our_urgency": our_roadmap["urgency"],
        "our_months": our_roadmap["months_remaining"],
        "our_total_gaps": our_roadmap["gaps"]["total_gaps"],
        "our_la_critical": len(our_roadmap["gaps"]["la_critical"]),
        "our_phases": len(our_roadmap["phases"]),
        "differences": [],
        "critical_observations": [],
    }

    consultant_essential = [r for r in consultant_results if r["verdict"] == "essential"]
    consultant_unnecessary = [r for r in consultant_results if r["verdict"] in ("unnecessary", "out_of_scope")]
    consultant_already = [r for r in consultant_results if r["verdict"] == "already_covered"]

    # Critical observation: consultant suggesting unnecessary items
    if consultant_unnecessary:
        comparison["critical_observations"].append({
            "type": "warning",
            "title": "Unnecessary / Out-of-Scope Suggestions",
            "detail": f"The consultant includes {len(consultant_unnecessary)} suggestion(s) that are not required for SSBJ compliance. "
                      f"This may indicate scope creep or upselling. Ask the consultant to justify each item against specific SSBJ requirements.",
        })

    # Critical observation: already covered items
    if consultant_already:
        comparison["critical_observations"].append({
            "type": "info",
            "title": "Suggestions for Areas You've Already Addressed",
            "detail": f"{len(consultant_already)} suggestion(s) target areas where your assessment score is already at or above the threshold (score 3+). "
                      f"Ask the consultant whether these are truly necessary improvements or if they're padding the proposal.",
        })

    # Critical observation: missing LA-critical items
    la_critical_ids = {g["id"] for g in our_roadmap["gaps"]["la_critical"]}
    consultant_covers_la = la_critical_ids & matched_ids
    missed_la = la_critical_ids - matched_ids
    if missed_la:
        missed_details = [f"{cid} ({criteria_map[cid]['category']})" for cid in missed_la if cid in criteria_map]
        comparison["critical_observations"].append({
            "type": "danger",
            "title": "Consultant MISSES Limited Assurance Critical Items",
            "detail": f"The consultant's roadmap does not address {len(missed_la)} items that are in limited assurance scope and below threshold: "
                      f"{', '.join(missed_details)}. These will be directly examined by auditors. This is a significant gap in the consultant's proposal.",
        })
    elif la_critical_ids:
        comparison["critical_observations"].append({
            "type": "success",
            "title": "LA-Critical Items Covered",
            "detail": f"The consultant's suggestions cover all {len(la_critical_ids)} limited assurance critical items. Good.",
        })

    # Timeline comparison
    comparison["differences"].append({
        "area": "Timeline Approach",
        "our_approach": f"Our roadmap uses a {our_roadmap['urgency']} timeline ({our_roadmap['months_remaining']} months) with {len(our_roadmap['phases'])} dynamically compressed phases. "
                        f"Phase durations adapt to your actual deadline.",
        "consultant_note": "Check whether the consultant's timeline accounts for your specific compliance date and adjusts urgency accordingly. "
                           "Many consultants use generic 18-24 month templates regardless of actual deadline.",
    })

    # Pre-assurance comparison
    comparison["differences"].append({
        "area": "Pre-Assurance Readiness",
        "our_approach": "Our roadmap includes dedicated pre-assurance phase: when to engage providers, readiness checklist based on your actual gaps, "
                        "provider selection criteria, and engagement timeline.",
        "consultant_note": "Does the consultant address assurance provider engagement timing? Many roadmaps focus on disclosure preparation but ignore the assurance engagement process.",
    })

    # IT recommendation comparison
    if our_roadmap["gaps"]["it_needed"]:
        comparison["differences"].append({
            "area": "IT Systems",
            "our_approach": "Based on your metrics scores (<2), we recommend IT investment for GHG calculation. However, minimum viable approach is well-controlled spreadsheets.",
            "consultant_note": "If the consultant recommends expensive GHG/ESG software, verify this is proportionate to your needs. "
                               "For initial LA scope (Scope 1 & 2, Governance, Risk Mgmt), controlled Excel workbooks can satisfy assurance requirements at fraction of the cost.",
        })

    # Prioritization comparison
    comparison["differences"].append({
        "area": "Prioritization",
        "our_approach": f"Our roadmap prioritizes {our_roadmap['gaps']['total_gaps']} gaps with {len(our_roadmap['gaps']['la_critical'])} LA-critical items first for assurance readiness, "
                        f"while ensuring ALL mandatory items across all four pillars are addressed for disclosure compliance.",
        "consultant_note": "ALL four SSBJ pillars (Governance, Strategy, Risk Management, Metrics & Targets) are mandatory for disclosure. "
                           "Check that the consultant covers all pillars, including value chain analysis (STR-02), Scope 3 (MET-03), scenario analysis (STR-04), "
                           "and risk/opportunity assessment (STR-01, RSK-01-04). LA-scope items need earliest attention for assurance readiness, but "
                           "no mandatory criterion should be skipped.",
    })

    # Value chain & Scope 3 comparison
    comparison["differences"].append({
        "area": "Value Chain & Scope 3",
        "our_approach": "SSBJ mandates value chain analysis (STR-02) and Scope 3 disclosure (MET-03). "
                        "These are NOT in initial limited assurance scope but ARE required for compliant disclosure. "
                        "SSBJ provides proportionality relief for first-year Scope 3 reporting.",
        "consultant_note": "If the consultant includes value chain analysis and Scope 3, this is CORRECT — it is mandatory under SSBJ/IFRS S1 & S2. "
                           "However, verify the scope is proportionate: SSBJ allows phasing in Scope 3 categories over time. "
                           "Full coverage of all 15 categories is not required in year 1.",
    })

    return comparison
