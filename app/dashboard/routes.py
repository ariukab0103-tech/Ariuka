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

    # Aggregate pillar scores across all completed assessments
    pillar_averages = {}
    completed = [a for a in assessments if a.status in ("completed", "under_review", "reviewed")]
    for a in completed:
        for pillar, score in a.pillar_scores().items():
            if pillar not in pillar_averages:
                pillar_averages[pillar] = {"total": 0, "count": 0}
            pillar_averages[pillar]["total"] += score
            pillar_averages[pillar]["count"] += 1
    pillar_averages = {
        k: round(v["total"] / v["count"], 1) if v["count"] else 0
        for k, v in pillar_averages.items()
    }

    return render_template(
        "dashboard/index.html",
        assessments=assessments,
        stats=stats,
        pillar_averages=pillar_averages,
    )
