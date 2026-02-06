from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(128), nullable=False)
    department = db.Column(db.String(128), default="")
    role = db.Column(db.String(20), nullable=False, default="assessor")
    # Roles: admin, assessor, reviewer
    must_change_password = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    assessments = db.relationship("Assessment", backref="author", lazy="dynamic")
    reviews = db.relationship("Review", backref="reviewer", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == "admin"

    @property
    def is_reviewer(self):
        return self.role in ("reviewer", "admin")


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    entity_name = db.Column(db.String(256), nullable=False)
    fiscal_year = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default="draft")
    # Status: draft, in_progress, completed, under_review, reviewed
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    responses = db.relationship(
        "Response", backref="assessment", lazy="dynamic", cascade="all, delete-orphan"
    )
    reviews = db.relationship(
        "Review", backref="assessment", lazy="dynamic", cascade="all, delete-orphan"
    )

    @property
    def completion_pct(self):
        total = self.responses.count()
        if total == 0:
            return 0
        answered = self.responses.filter(Response.score.isnot(None)).count()
        return round(answered / total * 100)

    @property
    def overall_score(self):
        responses = self.responses.filter(Response.score.isnot(None)).all()
        if not responses:
            return 0
        return round(sum(r.score for r in responses) / len(responses), 1)

    def pillar_scores(self):
        results = {}
        for resp in self.responses.filter(Response.score.isnot(None)).all():
            pillar = resp.pillar
            if pillar not in results:
                results[pillar] = {"total": 0, "count": 0}
            results[pillar]["total"] += resp.score
            results[pillar]["count"] += 1
        return {
            k: round(v["total"] / v["count"], 1) if v["count"] else 0
            for k, v in results.items()
        }

    def category_scores(self):
        results = {}
        for resp in self.responses.filter(Response.score.isnot(None)).all():
            cat = resp.category
            if cat not in results:
                results[cat] = {"total": 0, "count": 0}
            results[cat]["total"] += resp.score
            results[cat]["count"] += 1
        return {
            k: round(v["total"] / v["count"], 1) if v["count"] else 0
            for k, v in results.items()
        }


class Response(db.Model):
    __tablename__ = "responses"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False
    )
    criterion_id = db.Column(db.String(20), nullable=False)
    pillar = db.Column(db.String(50), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    standard = db.Column(db.String(50), nullable=False)
    score = db.Column(db.Integer, nullable=True)
    # Score: 0=Not started, 1=Initial/Ad-hoc, 2=Developing, 3=Defined, 4=Managed, 5=Optimized
    evidence = db.Column(db.Text, default="")
    notes = db.Column(db.Text, default="")
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False
    )
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    review_type = db.Column(db.String(50), default="limited_assurance")
    status = db.Column(db.String(20), default="pending")
    # Status: pending, in_progress, completed
    overall_opinion = db.Column(db.String(50), default="")
    # Opinion: unqualified, qualified, adverse, disclaimer
    findings = db.Column(db.Text, default="")
    recommendations = db.Column(db.Text, default="")
    created_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    review_items = db.relationship(
        "ReviewItem", backref="review", lazy="dynamic", cascade="all, delete-orphan"
    )


class ReviewItem(db.Model):
    __tablename__ = "review_items"

    id = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    criterion_id = db.Column(db.String(20), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), default="not_reviewed")
    # Status: not_reviewed, satisfactory, needs_improvement, unsatisfactory
    finding = db.Column(db.Text, default="")
    recommendation = db.Column(db.Text, default="")
    evidence_adequate = db.Column(db.Boolean, default=False)


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.Integer, primary_key=True)
    response_id = db.Column(
        db.Integer, db.ForeignKey("responses.id"), nullable=False
    )
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    response = db.relationship(
        "Response",
        backref=db.backref("attachments", lazy="dynamic", cascade="all, delete-orphan"),
    )
    uploader = db.relationship("User")


class AssessmentDocument(db.Model):
    """Assessment-level document used for bulk auto-assessment."""
    __tablename__ = "assessment_documents"

    id = db.Column(db.Integer, primary_key=True)
    assessment_id = db.Column(
        db.Integer, db.ForeignKey("assessments.id"), nullable=False
    )
    filename = db.Column(db.String(256), nullable=False)
    original_name = db.Column(db.String(256), nullable=False)
    file_size = db.Column(db.Integer, default=0)
    extracted_text = db.Column(db.Text, default="")
    uploaded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    uploaded_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    assessment = db.relationship(
        "Assessment",
        backref=db.backref("documents", lazy="dynamic", cascade="all, delete-orphan"),
    )
    uploader = db.relationship("User")
