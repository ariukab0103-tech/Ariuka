import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Assessment, Response, Attachment, AssessmentDocument
from app.ssbj_criteria import (
    SSBJ_CRITERIA, MATURITY_LEVELS, OBLIGATION_LABELS, LA_SCOPE_LABELS, LA_PRIORITY_LABELS,
    get_criteria_by_pillar,
)


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
    if current_user.is_admin:
        assessments = Assessment.query.order_by(Assessment.updated_at.desc()).all()
    else:
        assessments = (
            Assessment.query.filter_by(user_id=current_user.id)
            .order_by(Assessment.updated_at.desc())
            .all()
        )
    return render_template("assessment/list.html", assessments=assessments)


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
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    criteria_by_pillar = get_criteria_by_pillar()
    responses = {r.criterion_id: r for r in assessment.responses.all()}
    documents = assessment.documents.order_by(AssessmentDocument.uploaded_at.desc()).all()

    total_count = assessment.responses.count()
    scored_count = assessment.responses.filter(Response.score.isnot(None)).count()
    unanswered_count = total_count - scored_count
    ai_enabled = bool(os.environ.get("ANTHROPIC_API_KEY", ""))

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
        maturity_levels=MATURITY_LEVELS,
        obligation_labels=OBLIGATION_LABELS,
        la_scope_labels=LA_SCOPE_LABELS,
        la_priority_labels=LA_PRIORITY_LABELS,
    )


@assessment_bp.route("/<int:assessment_id>/assess/<string:criterion_id>", methods=["GET", "POST"])
@login_required
def assess_criterion(assessment_id, criterion_id):
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

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
    """Save all inline score changes from the assessment view."""
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    updated = 0
    for resp in assessment.responses.all():
        form_key = f"score_{resp.criterion_id}"
        score_val = request.form.get(form_key, "")
        if score_val.isdigit():
            new_score = int(score_val)
            if resp.score != new_score:
                resp.score = new_score
                updated += 1
        elif score_val == "" and resp.score is not None:
            resp.score = None
            updated += 1

    if assessment.status == "draft" and updated > 0:
        assessment.status = "in_progress"

    db.session.commit()
    if updated > 0:
        flash(f"Saved {updated} score change(s).", "success")
    else:
        flash("No changes to save.", "info")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/complete", methods=["POST"])
@login_required
def complete(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    unanswered = assessment.responses.filter(Response.score.is_(None)).count()
    if unanswered > 0:
        flash(f"{unanswered} criteria still unanswered. Please complete all items.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    assessment.status = "completed"
    db.session.commit()
    flash("Assessment marked as completed.", "success")
    return redirect(url_for("assessment.view", assessment_id=assessment_id))


@assessment_bp.route("/<int:assessment_id>/report")
@login_required
def report(assessment_id):
    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

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
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

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
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

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
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

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
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("assessment.list_assessments"))
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

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
    if not current_user.is_admin and assessment.user_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("assessment.list_assessments"))

    criterion_id = attachment.response.criterion_id

    # Delete physical file
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], attachment.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(attachment)
    db.session.commit()
    flash("File deleted.", "success")
    return redirect(url_for("assessment.assess_criterion", assessment_id=assessment_id, criterion_id=criterion_id))


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
