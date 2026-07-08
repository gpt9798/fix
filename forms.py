from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, FloatField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError


class SignupForm(FlaskForm):
    role = SelectField(
        "Register as",
        choices=[("customer", "Customer"), ("professional", "Professional")],
        validators=[DataRequired()],
    )

    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])

    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Length(min=7, max=30),
            Regexp(r"^[0-9+\-\s()]+$", message="Phone number can contain digits, +, -, spaces, parentheses"),
        ],
    )

    city = StringField("City", default="Bannu", validators=[DataRequired(), Length(min=2, max=80)])

    # Location placeholders
    latitude = FloatField("Latitude (optional)", validators=[Optional()])
    longitude = FloatField("Longitude (optional)", validators=[Optional()])

    # Professional checkboxes
    plumber = BooleanField("Plumber")
    electrician = BooleanField("Electrician")

    average_rating = FloatField("Average Rating (1-5, optional)", validators=[Optional()])

    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=255)])

    def validate_average_rating(self, field):
        if field.data is None:
            return
        if field.data < 0 or field.data > 5:
            raise ValidationError("Average rating must be between 0 and 5")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6, max=255)])


class GoogleCompleteProfileForm(FlaskForm):
    phone = StringField(
        "Phone Number",
        validators=[
            DataRequired(),
            Length(min=7, max=30),
            Regexp(r"^[0-9+\-\s()]+$", message="Phone number can contain digits, +, -, spaces, parentheses"),
        ],
    )

    plumber = BooleanField("Plumber")
    electrician = BooleanField("Electrician")

    def validate(self, extra_validators=None):
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False

        if not self.plumber.data and not self.electrician.data:
            # WTForms doesn't provide a built-in multi-field error in this minimal setup,
            # so we attach it via form-level errors.
            self.services_error = ["Select at least one service (Plumber and/or Electrician)."]
            return False

        self.services_error = []
        return True

