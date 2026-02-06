from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from app import db
from app.models import Assessment, Response, Review, ReviewItem
from app.ssbj_criteria import (
    LIMITED_ASSURANCE_CRITERIA,
    SSBJ_CRITERIA,
    MATURITY_LEVELS,
    get_criterion_by_id,
)

review_bp = Blueprint("review", __name__, url_prefix="/reviews")


@review_bp.route("/")
@login_required
def list_reviews():
    if not current_user.is_reviewer:
        flash("Access denied. Reviewer role required.", "danger")
        return redirect(url_for("dashboard.index"))
    if current_user.is_admin:
        reviews = Review.query.order_by(Review.updated_at.desc()).all()
    else:
        reviews = (
            Review.query.filter_by(reviewer_id=current_user.id)
            .order_by(Review.updated_at.desc())
            .all()
        )
    return render_template("review/list.html", reviews=reviews)


@review_bp.route("/start/<int:assessment_id>", methods=["POST"])
@login_required
def start_review(assessment_id):
    if not current_user.is_reviewer:
        flash("Access denied. Reviewer role required.", "danger")
        return redirect(url_for("dashboard.index"))

    assessment = db.session.get(Assessment, assessment_id)
    if not assessment:
        flash("Assessment not found.", "danger")
        return redirect(url_for("review.list_reviews"))
    if assessment.status not in ("completed", "under_review"):
        flash("Assessment must be completed before review.", "warning")
        return redirect(url_for("assessment.view", assessment_id=assessment_id))

    # Check if a review already exists for this reviewer
    existing = Review.query.filter_by(
        assessment_id=assessment_id, reviewer_id=current_user.id
    ).first()
    if existing:
        return redirect(url_for("review.conduct", review_id=existing.id))

    review = Review(
        assessment_id=assessment_id,
        reviewer_id=current_user.id,
        review_type="limited_assurance",
        status="in_progress",
    )
    db.session.add(review)
    db.session.flush()

    # Create review items for limited assurance criteria
    for criterion in LIMITED_ASSURANCE_CRITERIA:
        item = ReviewItem(
            review_id=review.id,
            criterion_id=criterion["id"],
            category=criterion["category"],
        )
        db.session.add(item)

    assessment.status = "under_review"
    db.session.commit()
    flash("Limited assurance review started.", "success")
    return redirect(url_for("review.conduct", review_id=review.id))


@review_bp.route("/<int:review_id>")
@login_required
def conduct(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("review.list_reviews"))
    if not current_user.is_admin and review.reviewer_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("review.list_reviews"))

    assessment = review.assessment
    responses = {r.criterion_id: r for r in assessment.responses.all()}
    review_items = {ri.criterion_id: ri for ri in review.review_items.all()}
    pillar_scores = assessment.pillar_scores()

    return render_template(
        "review/conduct.html",
        review=review,
        assessment=assessment,
        responses=responses,
        review_items=review_items,
        la_criteria=LIMITED_ASSURANCE_CRITERIA,
        ssbj_criteria=SSBJ_CRITERIA,
        maturity_levels=MATURITY_LEVELS,
        pillar_scores=pillar_scores,
    )


@review_bp.route("/<int:review_id>/item/<string:criterion_id>", methods=["GET", "POST"])
@login_required
def review_item(review_id, criterion_id):
    review = db.session.get(Review, review_id)
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("review.list_reviews"))
    if not current_user.is_admin and review.reviewer_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("review.list_reviews"))

    item = ReviewItem.query.filter_by(
        review_id=review_id, criterion_id=criterion_id
    ).first()
    if not item:
        flash("Review item not found.", "danger")
        return redirect(url_for("review.conduct", review_id=review_id))

    criterion = get_criterion_by_id(criterion_id)
    assessment = review.assessment
    # Get related assessment responses for context
    related_responses = assessment.responses.all()

    if request.method == "POST":
        item.status = request.form.get("status", "not_reviewed")
        item.finding = request.form.get("finding", "")
        item.recommendation = request.form.get("recommendation", "")
        item.evidence_adequate = request.form.get("evidence_adequate") == "yes"
        db.session.commit()
        flash(f"Review item {criterion_id} updated.", "success")

        # Navigate to next item
        next_item = _get_next_la_criterion(criterion_id)
        if next_item:
            return redirect(
                url_for("review.review_item", review_id=review_id, criterion_id=next_item)
            )
        return redirect(url_for("review.conduct", review_id=review_id))

    return render_template(
        "review/review_item.html",
        review=review,
        item=item,
        criterion=criterion,
        assessment=assessment,
        related_responses=related_responses,
        maturity_levels=MATURITY_LEVELS,
    )


@review_bp.route("/<int:review_id>/complete", methods=["GET", "POST"])
@login_required
def complete_review(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("review.list_reviews"))
    if not current_user.is_admin and review.reviewer_id != current_user.id:
        flash("Access denied.", "danger")
        return redirect(url_for("review.list_reviews"))

    not_reviewed = review.review_items.filter_by(status="not_reviewed").count()
    if not_reviewed > 0:
        flash(f"{not_reviewed} items still not reviewed.", "warning")
        return redirect(url_for("review.conduct", review_id=review_id))

    if request.method == "POST":
        review.overall_opinion = request.form.get("overall_opinion", "")
        review.findings = request.form.get("findings", "")
        review.recommendations = request.form.get("recommendations", "")
        review.status = "completed"
        review.assessment.status = "reviewed"
        db.session.commit()
        flash("Review completed successfully.", "success")
        return redirect(url_for("review.report", review_id=review_id))

    return render_template(
        "review/complete.html",
        review=review,
        assessment=review.assessment,
    )


@review_bp.route("/<int:review_id>/report")
@login_required
def report(review_id):
    review = db.session.get(Review, review_id)
    if not review:
        flash("Review not found.", "danger")
        return redirect(url_for("review.list_reviews"))

    assessment = review.assessment
    responses = {r.criterion_id: r for r in assessment.responses.all()}
    review_items = {ri.criterion_id: ri for ri in review.review_items.all()}
    pillar_scores = assessment.pillar_scores()

    # Compute review summary statistics
    items = review.review_items.all()
    stats = {
        "total": len(items),
        "satisfactory": sum(1 for i in items if i.status == "satisfactory"),
        "needs_improvement": sum(1 for i in items if i.status == "needs_improvement"),
        "unsatisfactory": sum(1 for i in items if i.status == "unsatisfactory"),
        "evidence_adequate": sum(1 for i in items if i.evidence_adequate),
    }

    return render_template(
        "review/report.html",
        review=review,
        assessment=assessment,
        responses=responses,
        review_items=review_items,
        la_criteria=LIMITED_ASSURANCE_CRITERIA,
        pillar_scores=pillar_scores,
        stats=stats,
        maturity_levels=MATURITY_LEVELS,
    )


def _get_next_la_criterion(current_id):
    """Get the next limited assurance criterion ID."""
    ids = [c["id"] for c in LIMITED_ASSURANCE_CRITERIA]
    try:
        idx = ids.index(current_id)
        if idx + 1 < len(ids):
            return ids[idx + 1]
    except ValueError:
        pass
    return None
