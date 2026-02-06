from app import create_app, db
from app.models import User

app = create_app()


@app.cli.command("init-db")
def init_db():
    """Initialize the database and create admin user."""
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@example.com",
            role="admin",
            full_name="Administrator",
        )
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("Database initialized. Admin user created (admin / admin123)")
    else:
        print("Database already initialized.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username="admin").first():
            admin = User(
                username="admin",
                email="admin@example.com",
                role="admin",
                full_name="Administrator",
            )
            admin.set_password("admin123")
            db.session.add(admin)
            db.session.commit()
    app.run(debug=True, host="0.0.0.0", port=5000)
