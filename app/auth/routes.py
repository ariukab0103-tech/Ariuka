import re

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user

from app import db
from app.models import User

auth_bp = Blueprint("auth", __name__)

MIN_PASSWORD_LENGTH = 8


def _validate_password(password):
    """Check password meets minimum strength requirements."""
    if len(password) < MIN_PASSWORD_LENGTH:
        return f"Password must be at least {MIN_PASSWORD_LENGTH} characters."
    if not re.search(r'[A-Za-z]', password):
        return "Password must contain at least one letter."
    if not re.search(r'[0-9]', password):
        return "Password must contain at least one number."
    return None


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("dashboard.index"))
        flash("Invalid username or password.", "danger")
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/data-security")
@login_required
def data_security():
    """Data security and privacy information page."""
    import os
    ai_enabled = bool(os.environ.get("ANTHROPIC_API_KEY", ""))
    return render_template("auth/data_security.html", ai_enabled=ai_enabled)


@auth_bp.route("/users")
@login_required
def user_list():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("auth/user_list.html", users=users)


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allow users to change their password (required for default accounts)."""
    if request.method == "POST":
        current_pw = request.form.get("current_password", "")
        new_pw = request.form.get("new_password", "")
        confirm_pw = request.form.get("confirm_password", "")

        if not current_user.check_password(current_pw):
            flash("Current password is incorrect.", "danger")
        elif new_pw != confirm_pw:
            flash("New passwords do not match.", "danger")
        else:
            pw_error = _validate_password(new_pw)
            if pw_error:
                flash(pw_error, "danger")
            else:
                current_user.set_password(new_pw)
                current_user.must_change_password = False
                db.session.commit()
                flash("Password changed successfully.", "success")
                return redirect(url_for("dashboard.index"))
    return render_template("auth/change_password.html")


@auth_bp.route("/users/create", methods=["GET", "POST"])
@login_required
def create_user():
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        full_name = request.form.get("full_name", "").strip()
        department = request.form.get("department", "").strip()
        role = request.form.get("role", "assessor")
        password = request.form.get("password", "")

        if User.query.filter_by(username=username).first():
            flash("Username already exists.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("Email already exists.", "danger")
        elif not username or not email or not password or not full_name:
            flash("All required fields must be filled.", "danger")
        else:
            pw_error = _validate_password(password)
            if pw_error:
                flash(pw_error, "danger")
            else:
                user = User(
                    username=username,
                    email=email,
                    full_name=full_name,
                    department=department,
                    role=role,
                    must_change_password=True,
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                flash(f"User '{username}' created. They will be asked to change their password on first login.", "success")
                return redirect(url_for("auth.user_list"))
    return render_template("auth/create_user.html")


@auth_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash("Access denied.", "danger")
        return redirect(url_for("dashboard.index"))
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.user_list"))
    if request.method == "POST":
        user.email = request.form.get("email", user.email).strip()
        user.full_name = request.form.get("full_name", user.full_name).strip()
        user.department = request.form.get("department", "").strip()
        user.role = request.form.get("role", user.role)
        new_password = request.form.get("password", "").strip()
        if new_password:
            pw_error = _validate_password(new_password)
            if pw_error:
                flash(pw_error, "danger")
                return render_template("auth/edit_user.html", user=user)
            user.set_password(new_password)
            user.must_change_password = True
        db.session.commit()
        flash(f"User '{user.username}' updated.", "success")
        return redirect(url_for("auth.user_list"))
    return render_template("auth/edit_user.html", user=user)
