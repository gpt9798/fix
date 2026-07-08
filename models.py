from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin


db = SQLAlchemy()


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    # Login identity
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)

    # Role selection
    role = db.Column(db.String(20), nullable=False)  # "customer" | "professional"

    # Profile fields
    name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(30), nullable=False)
    city = db.Column(db.String(80), nullable=False, default="Bannu")

    # Location placeholders (for later real-time tracking)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    # Auth provider fields
    google_sub = db.Column(db.String(120), unique=True, nullable=True, index=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    professional = db.relationship(
        "Professional",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class Professional(db.Model):
    __tablename__ = "professionals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    # Checkbox selection
    plumber = db.Column(db.Boolean, nullable=False, default=False)
    electrician = db.Column(db.Boolean, nullable=False, default=False)

    # Average rating placeholder (1-5 stars)
    # You can later compute this from a ratings table.
    average_rating = db.Column(db.Float, nullable=False, default=0.0)

    # Location placeholders too (optional redundancy for quick access)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User", back_populates="professional")


class ProfessionalRating(db.Model):
    """Optional future extension: store individual ratings.
    For now, not required by your UI, but the model enables computing average_rating.
    """

    __tablename__ = "professional_ratings"

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False, index=True)

    stars = db.Column(db.Integer, nullable=False)  # 1..5
    comment = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # (No relationships wired to keep migration minimal for this step.)


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)

    customer_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    professional_id = db.Column(
        db.Integer,
        db.ForeignKey("professionals.id"),
        nullable=False,
        index=True,
    )

    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String(500), nullable=True)


class Message(db.Model):
    """Simple message model between a customer and a professional."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)

    from_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    to_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)

    text = db.Column(db.String(2000), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Optional future: read receipts, conversation threading, etc.


class Admin(db.Model, UserMixin):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)


class Report(db.Model):
    """User reports another user (e.g., fake/bad accounts) for admin review."""

    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)

    # Who submitted the report
    reporter_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # The user being reported
    reported_user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    reason = db.Column(db.String(1000), nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

