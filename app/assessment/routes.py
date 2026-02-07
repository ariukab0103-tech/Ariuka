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
# Consultant Roadmap Review
# =========================================================================

def _build_keyword_index():
    """Build keyword-to-criterion mapping for matching consultant suggestions."""
    import re
    index = {}
    for c in SSBJ_CRITERIA:
        keywords = set()
        # Extract meaningful keywords from requirement, minimum_action, category
        for field in ("requirement", "minimum_action", "best_practice", "category", "guidance"):
            text = c.get(field, "")
            words = re.findall(r"[a-zA-Z]{4,}", text.lower())
            keywords.update(words)
        # Add specific domain keywords per pillar/topic
        if "scope 1" in (c.get("requirement", "") + c.get("minimum_action", "")).lower():
            keywords.update(["scope1", "scope", "direct", "emissions", "ghg", "greenhouse"])
        if "scope 2" in (c.get("requirement", "") + c.get("minimum_action", "")).lower():
            keywords.update(["scope2", "indirect", "electricity", "purchased"])
        if "scope 3" in (c.get("requirement", "") + c.get("minimum_action", "")).lower():
            keywords.update(["scope3", "value", "chain", "supply"])
        if c["pillar"] == "Governance":
            keywords.update(["board", "governance", "oversight", "committee"])
        if c["pillar"] == "Strategy":
            keywords.update(["strategy", "scenario", "transition", "climate"])
        if c["pillar"] == "Risk Management":
            keywords.update(["risk", "controls", "internal", "management"])
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

    # Check for commonly unnecessary or over-engineered consultant suggestions
    unnecessary_patterns = [
        (r"blockchain|nft|web3", "Blockchain/NFT technology is not required for SSBJ compliance. This is a common consultant upsell. Standard databases and spreadsheets with audit trails are fully sufficient for assurance purposes."),
        (r"real.?time\s+dashboard", "Real-time dashboards are nice-to-have but not required. SSBJ requires annual disclosure, not real-time monitoring. Consultants may suggest this to increase project scope and fees."),
        (r"ai.?powered|machine\s+learning|artificial\s+intelligence", "AI/ML tools are not required for SSBJ compliance. Manual processes with proper controls are fully acceptable. This may be consultant-driven technology upselling."),
        (r"carbon\s+offset|carbon\s+credit|offset\s+purchase", "Carbon offsets/credits are NOT part of Scope 1 & 2 reporting under SSBJ. Purchasing offsets does not reduce your reported emissions. If a consultant suggests this for compliance, they may be confusing emission reporting with carbon neutrality claims."),
        (r"comprehensive\s+esg\s+platform|all.in.one\s+esg|esg\s+software\s+suite", "A comprehensive ESG platform is overkill for initial SSBJ compliance. Start with controlled spreadsheets for Scope 1 & 2, then upgrade later. Consultants often bundle expensive software into their proposals."),
        (r"scope\s*3.*full|complete\s+scope\s*3|all.*scope\s*3\s+categories", "Full Scope 3 reporting across all 15 categories is NOT required in initial SSBJ compliance. Initial limited assurance covers only Scope 1 & 2. Consultants may push comprehensive Scope 3 to extend engagement duration."),
        (r"cdp.*report|sustainability\s+rating|esg\s+rating|sustainalytics|msci\s+esg", "ESG ratings and CDP reporting are separate from SSBJ mandatory disclosure. While useful, they are NOT required for compliance. Consultants may bundle these to increase project scope."),
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
    if best_c.get("obligation") == "mandatory" and best_c.get("la_scope") == "in_scope":
        verdict = "essential"
        explanation = f"ESSENTIAL for compliance. This maps to {best_id} ({best_c.get('category', '')}) which is mandatory AND in limited assurance scope. Your auditor will examine this."
        color = "danger"
        icon = "exclamation-triangle-fill"
    elif best_c.get("obligation") == "mandatory":
        verdict = "essential"
        explanation = f"ESSENTIAL. This maps to {best_id} ({best_c.get('category', '')}) which is mandatory under SSBJ. Must be addressed."
        color = "danger"
        icon = "exclamation-triangle"
    elif best_c.get("la_scope") == "in_scope":
        verdict = "essential"
        explanation = f"ESSENTIAL. While the obligation level is '{best_c.get('obligation', '')}', this is in limited assurance scope. Auditors will look at it."
        color = "danger"
        icon = "exclamation-triangle"
    elif best_c.get("obligation") == "recommended":
        verdict = "recommended"
        explanation = f"RECOMMENDED but not strictly required. Maps to {best_id} ({best_c.get('category', '')}). Good practice but you could defer this if budget/time is tight."
        color = "warning"
        icon = "info-circle"
    else:
        verdict = "recommended"
        explanation = f"NICE TO HAVE. Maps to {best_id} ({best_c.get('category', '')}). Interpretive requirement — implement if resources allow."
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
    """Review external consultant suggestions against SSBJ minimum viable requirements."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    results = None
    consultant_text = ""
    summary = None
    roadmap_comparison = None

    if request.method == "POST":
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
            # Build matching infrastructure
            keyword_index = _build_keyword_index()
            criteria_map = {c["id"]: c for c in SSBJ_CRITERIA}
            responses_map = {r.criterion_id: r for r in assessment.responses.all()}

            # Parse suggestions (split by newlines, numbered items, or bullet points)
            lines = re.split(r"\n+", consultant_text)
            suggestions = []
            for line in lines:
                cleaned = re.sub(r"^[\s\-\*\d\.\)]+", "", line).strip()
                if len(cleaned) > 10:  # skip very short lines
                    suggestions.append(cleaned)

            # Match and classify each suggestion
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

            # Find missing essentials
            missing = _check_missing_essentials(criteria_map, responses_map, all_matched_ids)

            # Generate our roadmap for comparison
            from app.roadmap import generate_roadmap
            responses_list = assessment.responses.filter(Response.score.isnot(None)).all()
            if responses_list:
                our_roadmap = generate_roadmap(assessment, responses_list)
                # Build roadmap comparison — what our roadmap says vs consultant
                roadmap_comparison = _compare_with_roadmap(our_roadmap, results, all_matched_ids, criteria_map)

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
            }

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
                               "For initial Scope 1 & 2 only, controlled Excel workbooks can satisfy assurance requirements at fraction of the cost.",
        })

    # Prioritization comparison
    comparison["differences"].append({
        "area": "Prioritization",
        "our_approach": f"Our roadmap prioritizes {our_roadmap['gaps']['total_gaps']} gaps with {len(our_roadmap['gaps']['la_critical'])} LA-critical items first. "
                        f"Tasks are ordered by assurance impact.",
        "consultant_note": "Check if the consultant's priority matches SSBJ requirements. LA-scope items (Scope 1 & 2 GHG) must come first. "
                           "If the consultant prioritizes governance or strategy over metrics, they may not understand the limited assurance focus.",
    })

    return comparison
