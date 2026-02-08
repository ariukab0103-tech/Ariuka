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
        fy_end_month = int(request.form.get("fy_end_month", "3"))
        if fy_end_month not in (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12):
            fy_end_month = 3
        try:
            market_cap_phase = int(request.form.get("market_cap_phase", "1"))
        except (ValueError, TypeError):
            market_cap_phase = 1

        if not title or not entity_name or not fiscal_year:
            flash("All fields are required.", "danger")
        else:
            assessment = Assessment(
                title=title,
                entity_name=entity_name,
                fiscal_year=fiscal_year,
                fy_end_month=fy_end_month,
                market_cap_phase=market_cap_phase,
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
    fy_end_month_str = request.form.get("fy_end_month", "3").strip()
    try:
        fy_end_month = int(fy_end_month_str)
    except (ValueError, TypeError):
        fy_end_month = 3
    market_cap_phase_str = request.form.get("market_cap_phase", "1").strip()
    try:
        market_cap_phase = int(market_cap_phase_str)
    except (ValueError, TypeError):
        market_cap_phase = 1

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
    if getattr(assessment, "fy_end_month", 3) != fy_end_month:
        assessment.fy_end_month = fy_end_month
        changed.append("FY end month")
    if getattr(assessment, "market_cap_phase", 1) != market_cap_phase:
        assessment.market_cap_phase = market_cap_phase
        changed.append("market cap phase")

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


@assessment_bp.route("/<int:assessment_id>/download-report")
@login_required
def download_report(assessment_id):
    """Combined report download — renders selected sections into one printable page."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    # Which sections were requested (checkboxes from modal)
    sections = request.args.getlist("s")
    if not sections:
        sections = ["gap"]  # default

    all_responses = assessment.responses.all()
    responses = {r.criterion_id: r for r in all_responses}
    criteria_by_pillar = get_criteria_by_pillar()
    pillar_scores = assessment.pillar_scores()
    category_scores = assessment.category_scores()

    # Gap analysis data
    gaps = []
    for r in all_responses:
        if r.score is not None and r.score < 3:
            criterion = next((c for c in SSBJ_CRITERIA if c["id"] == r.criterion_id), None)
            if criterion:
                gaps.append({"response": r, "criterion": criterion})

    # Roadmap data (also needed for exec summary)
    roadmap_data = None
    if "roadmap" in sections or "exec" in sections:
        from app.roadmap import generate_roadmap
        scored = [r for r in all_responses if r.score is not None]
        if scored:
            roadmap_data = generate_roadmap(assessment, scored)

    # Executive summary
    exec_data = None
    if "exec" in sections:
        from app.executive_summary import generate_executive_summary
        exec_data = generate_executive_summary(assessment, responses, pillar_scores, roadmap_data)

    # RACI data
    raci_data = None
    if "raci" in sections:
        from app.raci import generate_raci, DEPARTMENTS
        raci_data = generate_raci(assessment, responses)
        raci_data["departments"] = DEPARTMENTS

    # Relief advisor data
    relief_data = None
    if "relief" in sections:
        from app.relief_advisor import generate_relief_plan
        relief_data = generate_relief_plan(assessment, responses)

    # Audit simulator data
    sim_data = None
    if "audit" in sections:
        from app.assurance_simulator import generate_simulation
        sim_data = generate_simulation(assessment, responses)

    # Project execution checklist data
    checklist_data = None
    if "checklist" in sections:
        from app.project_checklist import generate_checklist
        checklist_data = generate_checklist(
            assessment, responses,
            roadmap_data=roadmap_data,
            raci_data=raci_data,
            relief_data=relief_data,
        )

    return render_template(
        "assessment/download_report.html",
        assessment=assessment,
        sections=sections,
        criteria_by_pillar=criteria_by_pillar,
        responses=responses,
        pillar_scores=pillar_scores,
        category_scores=category_scores,
        gaps=gaps,
        exec_summary=exec_data,
        roadmap=roadmap_data,
        raci=raci_data,
        relief=relief_data,
        sim=sim_data,
        checklist_data=checklist_data,
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

    from app.analyzer import extract_text_from_file, clear_cache

    # Invalidate assessment cache — document set is changing
    clear_cache()

    files = request.files.getlist("files")
    if not files or all(f.filename == "" for f in files):
        flash("No files selected.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    uploaded_count = 0
    failed_files = []
    for file in files:
        if file.filename == "" or not _allowed_file(file.filename):
            continue

        stored_name, original_name, file_size = _save_uploaded_file(file)
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], stored_name)

        # Extract text
        extracted = extract_text_from_file(filepath)

        # Detect extraction problems and give user feedback
        if extracted == "[ENCRYPTED_PDF]":
            failed_files.append(f"{original_name} (password-protected — please decrypt and re-upload)")
            extracted = ""
        elif extracted == "[SCANNED_PDF]":
            failed_files.append(f"{original_name} (scanned/image PDF — no extractable text. Please use a text-based PDF or DOCX)")
            extracted = ""

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

    if failed_files:
        flash(f"Could not extract text from: {'; '.join(failed_files)}", "warning")
    success_count = uploaded_count - len(failed_files)
    if success_count > 0:
        flash(f"{success_count} document(s) uploaded successfully. Click 'Auto-Assess' to analyze.", "success")
    elif not failed_files:
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


@assessment_bp.route("/<int:assessment_id>/auto-assess-stream")
@login_required
def auto_assess_stream(assessment_id):
    """SSE endpoint — streams batch-by-batch assessment progress.

    The frontend connects via EventSource.  Events:
      start, pass1_start, pass1_done, pass2_start,
      batch_done (×5), done, saved
    Supports retry of failed batches via ?batches=2,4 query param.
    """
    from flask import Response, stream_with_context
    import json as _json

    assessment = db.session.get(Assessment, assessment_id)
    if not assessment or not assessment.user_can(current_user, "edit"):
        return jsonify({"error": "Access denied"}), 403

    docs = assessment.documents.all()
    if not docs:
        return jsonify({"error": "No documents uploaded. Please upload documents first."}), 400

    combined_text = "\n\n".join(d.extracted_text for d in docs if d.extracted_text)
    if not combined_text.strip():
        return jsonify({"error": "No extractable text in documents."}), 400

    # Optional: retry specific batch indices (0-indexed)
    retry_param = request.args.get("batches", "")
    batch_indices = None
    if retry_param:
        try:
            batch_indices = [int(x) for x in retry_param.split(",") if x.strip()]
        except ValueError:
            pass

    # Pre-load response objects so we can update DB inside the generator
    response_map = {r.criterion_id: r for r in assessment.responses.all()}

    def generate():
        from app.analyzer import ai_assess_all_streaming

        results_to_save = None

        for event in ai_assess_all_streaming(combined_text, batch_indices):
            if event["type"] == "done":
                results_to_save = event.pop("results", {})
                yield f"data: {_json.dumps(event)}\n\n"
            elif event["type"] == "pass1_progress":
                # Lightweight keepalive — SSE comment + small data event
                yield f": keepalive {event.get('elapsed', 0)}s\n"
                yield f"data: {_json.dumps(event)}\n\n"
            else:
                yield f"data: {_json.dumps(event)}\n\n"

        # Persist results to database
        if results_to_save:
            updated = 0
            for cid, (score, evidence, notes) in results_to_save.items():
                resp = response_map.get(cid)
                if resp and score > 0:
                    resp.score = score
                    resp.evidence = evidence
                    resp.notes = notes
                    updated += 1
            if assessment.status in ("draft", "completed", "under_review", "reviewed"):
                assessment.status = "in_progress"
            db.session.commit()
            yield f"data: {_json.dumps({'type': 'saved', 'updated': updated})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


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

    from app.analyzer import clear_cache
    clear_cache()

    flash("Document deleted.", "success")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/ai-assess/<string:criterion_id>", methods=["POST"])
@login_required
def ai_assess_criterion(assessment_id, criterion_id):
    """AI re-assess a single criterion using its attached docs + evidence text."""
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

    criterion = next((c for c in SSBJ_CRITERIA if c["id"] == criterion_id), None)
    if not criterion:
        flash("Unknown criterion.", "danger")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        flash("AI assessment requires ANTHROPIC_API_KEY. Using keyword fallback is not supported for per-criterion assessment.", "warning")
        return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))

    # Gather evidence: criterion attachments + evidence text + assessment-level docs
    evidence_parts = []

    # 1. User-typed evidence (prefer current form text over saved DB value)
    current_evidence = request.form.get("current_evidence", "").strip()
    current_notes = request.form.get("current_notes", "").strip()
    user_evidence = current_evidence or (response.evidence or "")
    if user_evidence:
        evidence_parts.append(f"USER EVIDENCE:\n{user_evidence}")
    if current_notes:
        evidence_parts.append(f"USER NOTES:\n{current_notes}")

    # Also save the current typed text so it's not lost
    if current_evidence:
        response.evidence = current_evidence
    if current_notes:
        response.notes = current_notes
    if current_evidence or current_notes:
        db.session.commit()

    # 2. Per-criterion attached files
    from app.analyzer import extract_text_from_file
    for att in response.attachments.all():
        filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], att.filename)
        if os.path.exists(filepath):
            text = extract_text_from_file(filepath)
            if text:
                evidence_parts.append(f"ATTACHED FILE ({att.original_name}):\n{text[:5000]}")

    # 3. Assessment-level documents (for broader context)
    for doc in assessment.documents.all():
        if doc.extracted_text:
            evidence_parts.append(f"ASSESSMENT DOC ({doc.original_name}):\n{doc.extracted_text[:3000]}")

    combined_evidence = "\n\n---\n\n".join(evidence_parts)
    if not combined_evidence.strip():
        flash("No evidence found. Upload documents or type evidence in the documentation box first.", "warning")
        return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))

    # Truncate to reasonable size
    combined_evidence = combined_evidence[:12000]

    try:
        import anthropic
        from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeout

        system_prompt = f"""You are an SSBJ/ISSB sustainability auditor assessing ONE specific criterion.

Criterion: {criterion['id']} — {criterion['category']}
Pillar: {criterion['pillar']}
Obligation: {criterion['obligation']}
LA Scope: {criterion['la_scope']}

REQUIREMENT:
{criterion['requirement']}

MINIMUM COMPLIANCE ACTION:
{criterion.get('minimum_action', 'N/A')}

MATURITY SCALE:
0 = No evidence at all
1 = Mentioned only, no formal processes
2 = Basic/partial processes, inconsistent
3 = Formal documented processes, consistently applied (LIMITED ASSURANCE THRESHOLD)
4 = Monitored, measured, reviewed regularly
5 = Continuous improvement, leading practice

Be STRICT: Score 3+ requires formal documented processes, specific methodologies, named responsibilities, concrete data. Vague mentions = 1-2.

Assess the provided evidence ONLY against this specific criterion. Return JSON:
{{"score": 0-5, "evidence_summary": "What the evidence shows for this criterion", "gaps": "What is missing to reach score 3+", "action_items": "Specific next steps to improve"}}
Return ONLY valid JSON."""

        user_prompt = f"""EVIDENCE FOR {criterion['id']}:

{combined_evidence}

Assess this evidence against the criterion requirement. Be specific about what the evidence demonstrates and what's missing."""

        def _call_api():
            client = anthropic.Anthropic(api_key=api_key, timeout=45.0)
            return client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1500,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_call_api)
            api_response = future.result(timeout=50)

        import json as _json
        response_text = api_response.content[0].text.strip()
        if response_text.startswith("```"):
            import re
            response_text = re.sub(r'^```(?:json)?\s*\n?', '', response_text)
            response_text = re.sub(r'\n?```\s*$', '', response_text)

        result = _json.loads(response_text)

        new_score = int(result.get("score", 0))
        evidence_summary = result.get("evidence_summary", "")
        gaps = result.get("gaps", "")
        action_items = result.get("action_items", "")

        # Update response — prepend AI assessment, keep user evidence
        old_evidence = response.evidence or ""
        ai_section = f"[AI Assessment — {criterion_id}]\nScore: {new_score}/5\n{evidence_summary}"
        if old_evidence and not old_evidence.startswith("[AI Assessment"):
            response.evidence = f"{ai_section}\n\n--- User Evidence ---\n{old_evidence}"
        else:
            response.evidence = ai_section

        response.score = new_score
        response.notes = f"{gaps}\n\nAction Items:\n{action_items}" if gaps or action_items else response.notes

        if assessment.status == "draft":
            assessment.status = "in_progress"
        db.session.commit()

        flash(f"AI assessed {criterion_id}: Score {new_score}/5. Review and adjust if needed.", "success")

    except FuturesTimeout:
        flash("AI assessment timed out. Please try again.", "warning")
    except BaseException as e:
        import logging
        logging.getLogger(__name__).warning(f"Per-criterion AI assess failed: {type(e).__name__}: {e}")
        flash(f"AI assessment failed: {e}", "danger")

    return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))


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


@assessment_bp.route("/<int:assessment_id>/delete", methods=["POST"])
@login_required
def delete_assessment(assessment_id):
    """Delete an assessment and all associated data (responses, reviews, documents, files)."""
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    # Only owner or admin can delete
    perm = assessment.user_permission(current_user)
    if perm != "owner":
        flash("Only the assessment owner or admin can delete an assessment.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    title = assessment.title

    # Delete physical files from per-criterion attachments
    for resp in assessment.responses.all():
        for att in resp.attachments.all():
            filepath = os.path.join(upload_dir, att.filename)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                except OSError:
                    pass

    # Delete physical files from assessment-level documents
    for doc in assessment.documents.all():
        filepath = os.path.join(upload_dir, doc.filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError:
                pass

    # Delete assessment — cascades handle Response, Review, AssessmentAccess,
    # Attachment (via Response), AssessmentDocument records
    db.session.delete(assessment)
    db.session.commit()

    flash(f"Assessment '{title}' and all associated data deleted.", "success")
    return redirect(url_for("assessment.list_assessments"))


@assessment_bp.route("/<int:assessment_id>/raci")
@login_required
def raci_matrix(assessment_id):
    """B1: Generate RACI matrix for the assessment."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    responses = {
        r.criterion_id: r for r in assessment.responses.all()
    }

    from app.raci import generate_raci, DEPARTMENTS
    raci_data = generate_raci(assessment, responses)

    return render_template(
        "assessment/raci.html",
        assessment=assessment,
        departments=raci_data["departments"],
        criteria=raci_data["criteria"],
        dept_workload=raci_data["dept_workload"],
        priority_actions=raci_data["priority_actions"],
        obligation_labels=OBLIGATION_LABELS,
    )


@assessment_bp.route("/<int:assessment_id>/relief-advisor")
@login_required
def relief_advisor(assessment_id):
    """B3: Transitional Relief Advisor — dynamic filtering by FY and scores."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    responses = {
        r.criterion_id: r for r in assessment.responses.all()
    }

    from app.relief_advisor import generate_relief_plan
    relief_data = generate_relief_plan(assessment, responses)

    return render_template(
        "assessment/relief_advisor.html",
        assessment=assessment,
        relief_items=relief_data["relief_items"],
        no_relief_items=relief_data.get("no_relief_items", []),
        rsk05_item=relief_data.get("rsk05_item"),
        summary=relief_data["summary"],
        japan_items=relief_data["japan_items"],
        climate_only_option=relief_data.get("climate_only_option"),
        obligation_labels=OBLIGATION_LABELS,
        la_scope_labels=LA_SCOPE_LABELS,
    )


@assessment_bp.route("/<int:assessment_id>/project-checklist")
@login_required
def project_checklist(assessment_id):
    """Project Execution Checklist — actionable task list for gap closure."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    responses = {
        r.criterion_id: r for r in assessment.responses.all()
    }

    scored = [r for r in responses.values() if r.score is not None]
    if not scored:
        flash("No scored criteria yet. Complete the assessment first.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    from app.project_checklist import generate_checklist
    checklist_data = generate_checklist(assessment, responses)

    # Fetch latest review for this assessment (if any)
    from app.models import Review
    latest_review = (
        assessment.reviews
        .order_by(Review.created_at.desc())
        .first()
    )

    return render_template(
        "assessment/project_checklist.html",
        assessment=assessment,
        phases=checklist_data["phases"],
        evidence_tracker=checklist_data["evidence_tracker"],
        budget_summary=checklist_data["budget_summary"],
        gate_reviews=checklist_data["gate_reviews"],
        year2_prep=checklist_data["year2_prep"],
        summary=checklist_data["summary"],
        latest_review=latest_review,
    )


@assessment_bp.route("/<int:assessment_id>/project-checklist/download")
@login_required
def download_checklist_excel(assessment_id):
    """Download Project Execution Checklist as Excel workbook."""
    from io import BytesIO

    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    responses = {
        r.criterion_id: r for r in assessment.responses.all()
    }

    scored = [r for r in responses.values() if r.score is not None]
    if not scored:
        flash("No scored criteria yet. Complete the assessment first.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    from app.project_checklist import generate_checklist, generate_excel
    checklist_data = generate_checklist(assessment, responses)

    # Include review findings if a completed review exists
    from app.models import Review
    review_data = None
    latest_review = assessment.reviews.order_by(Review.created_at.desc()).first()
    if latest_review and latest_review.status == "completed":
        review_data = {
            "reviewer": latest_review.reviewer.full_name,
            "date": latest_review.updated_at.strftime("%Y-%m-%d"),
            "opinion": latest_review.overall_opinion,
            "findings": latest_review.findings,
            "recommendations": latest_review.recommendations,
            "items": [
                {
                    "criterion_id": ri.criterion_id,
                    "category": ri.category,
                    "status": ri.status,
                    "evidence_adequate": ri.evidence_adequate,
                    "finding": ri.finding,
                    "recommendation": ri.recommendation,
                }
                for ri in latest_review.review_items.all()
            ],
        }

    wb = generate_excel(
        checklist_data,
        assessment_title=assessment.title,
        entity_name=assessment.entity_name,
        fiscal_year=assessment.fiscal_year,
        review_data=review_data,
    )

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    from flask import send_file
    filename = f"SSBJ_Checklist_{assessment.entity_name.replace(' ', '_')}_{assessment.fiscal_year[:6]}.xlsx"
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name=filename,
    )


@assessment_bp.route("/<int:assessment_id>/audit-simulator")
@login_required
def audit_simulator(assessment_id):
    """C3: Assurance Readiness Simulator — mock audit walkthrough."""
    assessment = db.session.get(Assessment, assessment_id)
    denied = _require_access(assessment, "view")
    if denied:
        return denied

    responses = {
        r.criterion_id: r for r in assessment.responses.all()
    }

    from app.assurance_simulator import generate_simulation
    sim_data = generate_simulation(assessment, responses)

    return render_template(
        "assessment/audit_simulator.html",
        assessment=assessment,
        ssbj_items=sim_data["ssbj_items"],
        la_items=sim_data["la_items"],
        readiness_summary=sim_data["readiness_summary"],
    )


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
