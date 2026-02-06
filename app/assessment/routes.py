import os
import uuid

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_from_directory, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import db
from app.models import Assessment, Response, Attachment
from app.ssbj_criteria import SSBJ_CRITERIA, MATURITY_LEVELS, get_criteria_by_pillar


def _allowed_file(filename):
    return "." in filename and \
        filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"]

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

    return render_template(
        "assessment/view.html",
        assessment=assessment,
        criteria_by_pillar=criteria_by_pillar,
        responses=responses,
        maturity_levels=MATURITY_LEVELS,
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
    )


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
    )


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

    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)

    original_name = secure_filename(file.filename)
    ext = original_name.rsplit(".", 1)[1].lower() if "." in original_name else ""
    stored_name = f"{uuid.uuid4().hex}.{ext}"

    file.save(os.path.join(upload_dir, stored_name))
    file_size = os.path.getsize(os.path.join(upload_dir, stored_name))

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
