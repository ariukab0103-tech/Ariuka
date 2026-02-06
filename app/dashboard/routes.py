from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from app.models import Assessment, User, Review

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.is_admin:
        assessments = Assessment.query.order_by(Assessment.updated_at.desc()).all()
        total_users = User.query.count()
        total_reviews = Review.query.count()
    else:
        assessments = (
            Assessment.query.filter_by(user_id=current_user.id)
            .order_by(Assessment.updated_at.desc())
            .all()
        )
        total_users = None
        total_reviews = (
            Review.query.filter_by(reviewer_id=current_user.id).count()
            if current_user.is_reviewer
            else None
        )

    # Compute summary stats
    stats = {
        "total_assessments": len(assessments),
        "draft": sum(1 for a in assessments if a.status == "draft"),
        "in_progress": sum(1 for a in assessments if a.status == "in_progress"),
        "completed": sum(1 for a in assessments if a.status in ("completed", "under_review", "reviewed")),
        "reviewed": sum(1 for a in assessments if a.status == "reviewed"),
        "total_users": total_users,
        "total_reviews": total_reviews,
    }

    # Per-assessment pillar scores (for each completed/in-progress assessment)
    scored_assessments = [
        a for a in assessments
        if a.status in ("in_progress", "completed", "under_review", "reviewed")
        and a.overall_score > 0
    ]

    assessment_details = []
    for a in scored_assessments:
        pillar_scores = a.pillar_scores()
        assessment_details.append({
            "id": a.id,
            "title": a.title,
            "entity_name": a.entity_name,
            "fiscal_year": a.fiscal_year,
            "status": a.status,
            "overall_score": a.overall_score,
            "completion_pct": a.completion_pct,
            "pillar_scores": pillar_scores,
        })

    # Collect all pillar names for consistent chart labels
    all_pillars = ["Governance", "Strategy", "Risk Management", "Metrics & Targets"]

    return render_template(
        "dashboard/index.html",
        assessments=assessments,
        stats=stats,
        assessment_details=assessment_details,
        all_pillars=all_pillars,
    )
