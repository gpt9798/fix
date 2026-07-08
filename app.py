import os
from urllib.parse import urlparse

from authlib.integrations.flask_client import OAuth
from flask import (

    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from werkzeug.security import check_password_hash, generate_password_hash

from forms import LoginForm, SignupForm, GoogleCompleteProfileForm
from models import Admin, Professional, User, Message, Review, db




def _is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(url_for('home') if target.startswith('/') else target)
    return test_url.netloc == ref_url.netloc and test_url.scheme in ('http', 'https')


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Database
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(app.root_path, 'karigar.db'),
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Flask-Login
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.session_protection = 'strong'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """Load either a customer/professional `User` or an `Admin`.

    We store admin sessions via `login_user(admin)` as well.
    """
    try:
        # `flask_login` stores the `id` as a string.
        # Admin/User primary keys share the same type, so we probe both.
        user = db.session.get(User, int(user_id))
        if user is not None:
            return user

        # `db.session.get` can take either the model class or a mapper.
        admin = db.session.get(Admin, int(user_id))
        return admin

    except Exception:
        return None



@app.before_request
def ensure_session_non_permanent():
    session.permanent = False


@app.route('/')
def home():
    return render_template('home.html', title='KarigarOnline.com - Find & Hire Professionals')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = SignupForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()

        if User.query.filter_by(email=email).first() is not None:
            flash('Email already registered. Please login.', 'error')
            return redirect(url_for('signup'))

        password_hash = generate_password_hash(form.password.data)

        user = User(
            email=email,
            password_hash=password_hash,
            role=form.role.data,
            name=form.name.data.strip(),
            phone=form.phone.data.strip(),
            city=form.city.data.strip(),
            latitude=form.latitude.data if form.latitude.data is not None else None,
            longitude=form.longitude.data if form.longitude.data is not None else None,
        )

        if form.role.data == 'professional':
            professional = Professional(
                plumber=bool(form.plumber.data),
                electrician=bool(form.electrician.data),
                average_rating=float(form.average_rating.data or 0.0),
                latitude=user.latitude,
                longitude=user.longitude,
            )
            user.professional = professional

            if not professional.plumber and not professional.electrician:
                flash('For Professional, select at least one service (Plumber/Electrician).', 'error')
                return redirect(url_for('signup'))

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('signup.html', form=form, title='Signup - KarigarOnline.com')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user is None:
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        if user.password_hash is None:
            flash('This account uses Google login. Please continue with Google.', 'error')
            return redirect(url_for('login'))

        if not check_password_hash(user.password_hash, form.password.data):
            flash('Invalid email or password.', 'error')
            return redirect(url_for('login'))

        login_user(user)
        flash('Logged in successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('login.html', form=form, title='Login - KarigarOnline.com')


@app.route('/logout')
def logout():
    logout_user()
    flash('Logged out.', 'success')
    return redirect(url_for('home'))


def _professional_needs_completion(user: User) -> bool:
    if user is None:
        return False
    if user.role != 'professional':
        return False

    if not user.phone or not user.phone.strip():
        return True

    if not user.professional:
        return True

    if not user.professional.plumber and not user.professional.electrician:
        return True

    return False


@app.route('/complete-profile', methods=['GET', 'POST'])
@login_required
def complete_profile():
    if current_user.role != 'professional':
        return redirect(url_for('dashboard'))

    # If already complete, go to dashboard
    if not _professional_needs_completion(current_user):
        return redirect(url_for('dashboard'))

    form = GoogleCompleteProfileForm()

    # Pre-fill for better UX
    if request.method == 'GET':
        form.phone.data = current_user.phone or ''
        if current_user.professional:
            form.plumber.data = bool(current_user.professional.plumber)
            form.electrician.data = bool(current_user.professional.electrician)

    if form.validate_on_submit():
        current_user.phone = form.phone.data.strip()

        if not current_user.professional:
            # Create professional row if it doesn't exist (older records)
            current_user.professional = Professional(
                plumber=False,
                electrician=False,
                average_rating=0.0,
                latitude=current_user.latitude,
                longitude=current_user.longitude,
            )

        current_user.professional.plumber = bool(form.plumber.data)
        current_user.professional.electrician = bool(form.electrician.data)
        db.session.commit()

        flash('Profile completed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('complete_profile.html', form=form, title='Complete Profile - KarigarOnline.com')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    # Admin login is separate from customer/professional login.
    if current_user.is_authenticated:
        # If an admin is already logged in, just go home.
        if getattr(current_user, 'username', None) is not None:
            return redirect(url_for('home'))
        # Otherwise, keep them on main app.
        return redirect(url_for('dashboard'))


    if request.method == 'POST':
        username = (request.form.get('username') or '').strip()
        password = request.form.get('password') or ''

        if not username or not password:
            flash('Admin username and password are required.', 'error')
            return render_template('admin_login.html', title='Admin Login - KarigarOnline.com')

        admin = Admin.query.filter_by(username=username).first()
        if admin is None:
            flash('Invalid admin username or password.', 'error')
            return render_template('admin_login.html', title='Admin Login - KarigarOnline.com')

        if not check_password_hash(admin.password_hash, password):
            flash('Invalid admin username or password.', 'error')
            return render_template('admin_login.html', title='Admin Login - KarigarOnline.com')

        login_user(admin)
        flash('Admin logged in successfully!', 'success')
        return redirect(url_for('home'))

    return render_template('admin_login.html', title='Admin Login - KarigarOnline.com')


@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    # Ensure only admins can access this route.
    if not isinstance(current_user, Admin):
        flash('Admin access required', 'error')
        return redirect(url_for('home'))

    total_users = User.query.count()
    total_professionals = Professional.query.count()

    return render_template(
        'admin_dashboard.html',
        title='Admin Dashboard - KarigarOnline.com',
        total_users=total_users,
        total_professionals=total_professionals,
        admin=current_user,
    )


@app.route('/dashboard')
@login_required
def dashboard():

    # Gate dashboard for first-time Google professionals (and any incomplete professionals)
    if _professional_needs_completion(current_user):
        return redirect(url_for('complete_profile'))

    professionals = []
    if current_user.role == 'customer':
        professionals = (
            Professional.query.order_by(Professional.average_rating.desc()).all()
        )


    return render_template('dashboard.html', current_user=current_user, professionals=professionals, title='Dashboard - KarigarOnline.com')



@app.route('/chat/<int:professional_id>', methods=['GET', 'POST'])
@login_required
def chat_with_professional(professional_id: int):
    if current_user.role != 'customer':
        return redirect(url_for('dashboard'))

    professional = Professional.query.get_or_404(professional_id)
    other_user = professional.user

    if other_user is None:
        flash('Professional not found.', 'error')
        return redirect(url_for('dashboard'))

    # Prevent chatting with yourself / invalid combos
    if other_user.id == current_user.id:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        text = (request.form.get('text') or '').strip()
        if text:
            msg = Message(
                from_user_id=current_user.id,
                to_user_id=other_user.id,
                text=text,
            )
            db.session.add(msg)
            db.session.commit()

        return redirect(url_for('chat_with_professional', professional_id=professional_id))

    messages = Message.query.filter(
        ((Message.from_user_id == current_user.id) & (Message.to_user_id == other_user.id)) |
        ((Message.from_user_id == other_user.id) & (Message.to_user_id == current_user.id))
    ).order_by(Message.created_at.asc()).all()

    return render_template(
        'customer_professional_conversation.html',
        current_user=current_user,
        other_user=other_user,
        messages=messages,
        title='Chat - KarigarOnline.com',
    )


@app.route('/report_user', methods=['POST'])
@login_required
def report_user():
    # Only customers can report other users.
    if current_user.role != 'customer':
        flash('Only customers can submit reports.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    reported_user_id_raw = request.form.get('reported_user_id')
    reason = (request.form.get('reason') or '').strip()

    if not reported_user_id_raw:
        flash('Invalid report target.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    try:
        reported_user_id = int(reported_user_id_raw)
    except (TypeError, ValueError):
        flash('Invalid report target.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    if not reason:
        flash('Please provide a reason for the report.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    if len(reason) > 1000:
        reason = reason[:1000]

    if reported_user_id == current_user.id:
        flash('You cannot report yourself.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    reported_user = User.query.get(reported_user_id)
    if reported_user is None:
        flash('User to report not found.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    report = Report(
        reporter_id=current_user.id,
        reported_user_id=reported_user.id,
        reason=reason,
    )
    db.session.add(report)
    db.session.commit()

    flash('Report submitted successfully. Thank you!', 'success')
    return redirect(request.referrer or url_for('dashboard'))


@app.route('/submit_review', methods=['POST'])
@login_required
def submit_review():

    # Only customers can submit reviews
    if current_user.role != 'customer':
        flash('Only customers can submit reviews.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    professional_id_raw = request.form.get('professional_id')
    rating_raw = request.form.get('rating')
    comment = (request.form.get('comment') or '').strip() or None

    try:
        professional_id = int(professional_id_raw)
        rating = int(rating_raw)
    except (TypeError, ValueError):
        flash('Invalid professional or rating.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    if rating < 1 or rating > 5:
        flash('Rating must be between 1 and 5.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    professional = Professional.query.get(professional_id)
    if professional is None:
        flash('Professional not found.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    # Prevent customers from reviewing their own professional profile if applicable
    if professional.user_id == current_user.id:
        flash('You cannot review yourself.', 'error')
        return redirect(request.referrer or url_for('dashboard'))

    review = Review(
        customer_id=current_user.id,
        professional_id=professional_id,
        rating=rating,
        comment=comment,
    )

    db.session.add(review)

    # Commit so the new review is included in the aggregate
    db.session.commit()

    # Update average_rating for the professional based on all reviews
    ratings_sum = db.session.query(db.func.sum(Review.rating)).filter(Review.professional_id == professional_id).scalar()
    ratings_count = db.session.query(db.func.count(Review.id)).filter(Review.professional_id == professional_id).scalar()

    if ratings_count and ratings_sum is not None:
        professional.average_rating = float(ratings_sum) / float(ratings_count)
    else:
        professional.average_rating = 0.0

    db.session.commit()

    flash('Review submitted successfully!', 'success')
    return redirect(request.referrer or url_for('dashboard'))


# -------------------------
# Google OAuth (Authlib)
# -------------------------


oauth = OAuth(app)

GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')

if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'},
    )


@app.route('/auth/google/login')
def google_login():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        flash('Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.', 'error')
        return redirect(url_for('login'))

    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'http://127.0.0.1:5000/auth/google/callback')

    # Optional: store desired redirect
    next_url = request.args.get('next')
    session['post_login_redirect'] = next_url

    return oauth.google.authorize_redirect(redirect_uri, redirect_uri=redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET):
        flash('Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.', 'error')
        return redirect(url_for('login'))

    token = oauth.google.authorize_access_token()
    user_info = oauth.google.parse_id_token(token)

    email = (user_info.get('email') or '').strip().lower()
    name = user_info.get('name') or 'Google User'
    google_sub = user_info.get('sub') or user_info.get('oid')

    if not email:
        flash('Google login failed: email not provided.', 'error')
        return redirect(url_for('login'))

    user = User.query.filter_by(email=email).first()

    if user is None:
        # Create a minimal customer by default.
        user = User(
            email=email,
            password_hash=None,  # Google-only
            role='customer',
            name=name,
            phone='',
            city='Bannu',
            latitude=None,
            longitude=None,
            google_sub=google_sub,
        )
        db.session.add(user)
        db.session.commit()

    else:
        if user.google_sub is None and google_sub:
            user.google_sub = google_sub
            db.session.commit()

    login_user(user)

    next_url = session.pop('post_login_redirect', None)
    if next_url and _is_safe_url(next_url):
        return redirect(next_url)

    flash('Logged in with Google!', 'success')
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


