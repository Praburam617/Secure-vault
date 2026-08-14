from datetime import datetime, timezone
from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.auth import auth_bp
from app.models import db, User, UserSettings, UserSession
from app.services.security_service import SecurityService
from app.utils.validators import Validators
from app.utils.helpers import get_client_ip, parse_user_agent, generate_random_token
from app.utils.decorators import anonymous_required

@auth_bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # 1. Username validation
        valid_user, user_msg = Validators.is_valid_username(username)
        if not valid_user:
            flash(user_msg, 'danger')
            return render_template('register.html')

        # 2. Email validation
        valid_email, email_msg = Validators.is_valid_email(email)
        if not valid_email:
            flash(email_msg, 'danger')
            return render_template('register.html')

        # 3. Password strength validation
        valid_pwd, score, pwd_msg = Validators.check_password_strength(password)
        if not valid_pwd:
            flash(pwd_msg, 'danger')
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", 'danger')
            return render_template('register.html')

        # 4. Check uniqueness (Generic error message if user or email exists to prevent enumeration)
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash("An account with that username or email address already exists.", 'danger')
            SecurityService.log_event(None, 'REGISTER_FAILED', 'FAILED', get_client_ip(), parse_user_agent(), f"Duplicate registration attempt: {username}/{email}")
            return render_template('register.html')

        # 5. Create user
        try:
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()

            # Create default settings
            settings = UserSettings(user_id=new_user.id)
            db.session.add(settings)
            db.session.commit()

            SecurityService.log_event(new_user.id, 'REGISTER_SUCCESS', 'SUCCESS', get_client_ip(), parse_user_agent(), "User account registered successfully.")
            flash("Registration successful! You can now log in.", 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash("An unexpected error occurred during registration.", 'danger')
            return render_template('register.html')

    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = True if request.form.get('remember') else False

        # Find user by username or email
        user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()

        # Check account lockout
        if user:
            is_locked, remaining_mins = SecurityService.is_user_locked_out(user)
            if is_locked:
                flash(f"Account is temporarily locked due to multiple failed login attempts. Please try again in {remaining_mins} minutes.", 'danger')
                SecurityService.log_event(user.id, 'LOGIN_LOCKED', 'FAILED', get_client_ip(), parse_user_agent(), f"Locked out attempt.")
                return render_template('login.html')

        # Validate credentials (generic error message to prevent enumeration)
        if not user or not user.check_password(password):
            if user:
                SecurityService.record_failed_login(user)
            SecurityService.log_event(user.id if user else None, 'LOGIN_FAILED', 'FAILED', get_client_ip(), parse_user_agent(), f"Invalid credentials for identifier: {identifier}")
            flash("Invalid credentials. Please check your username/email and password.", 'danger')
            return render_template('login.html')

        # Credentials verified - reset lockout counters
        SecurityService.reset_failed_login(user)

        # Protect against session fixation
        session.clear()

        # Log in user via Flask-Login
        login_user(user, remember=remember)

        # Record Active Session
        session_token = generate_random_token(32)
        session['session_token'] = session_token
        new_session = UserSession(
            user_id=user.id,
            session_token=session_token,
            ip_address=get_client_ip(),
            user_agent=parse_user_agent(),
            device_info=parse_user_agent()[:64]
        )
        db.session.add(new_session)
        db.session.commit()

        SecurityService.log_event(user.id, 'LOGIN_SUCCESS', 'SUCCESS', get_client_ip(), parse_user_agent(), "User logged in successfully.")
        flash(f"Welcome back, {user.username}!", 'success')

        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.dashboard')
        return redirect(next_page)

    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    session_token = session.get('session_token')
    if session_token:
        active_sess = UserSession.query.filter_by(session_token=session_token).first()
        if active_sess:
            active_sess.is_active = False
            db.session.commit()

    user_id = current_user.id
    username = current_user.username
    logout_user()
    session.clear()
    SecurityService.log_event(user_id, 'LOGOUT', 'SUCCESS', get_client_ip(), parse_user_agent(), f"User {username} logged out.")
    flash("You have been logged out securely.", 'info')
    return redirect(url_for('main.landing'))


@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_password', '')

    if not current_user.check_password(current_password):
        flash("Current password is incorrect.", 'danger')
        SecurityService.log_event(current_user.id, 'CHANGE_PASSWORD', 'FAILED', get_client_ip(), parse_user_agent(), "Incorrect current password.")
        return redirect(url_for('main.settings_page'))

    valid_pwd, score, pwd_msg = Validators.check_password_strength(new_password)
    if not valid_pwd:
        flash(pwd_msg, 'danger')
        return redirect(url_for('main.settings_page'))

    if new_password != confirm_password:
        flash("New passwords do not match.", 'danger')
        return redirect(url_for('main.settings_page'))

    current_user.set_password(new_password)
    db.session.commit()
    SecurityService.log_event(current_user.id, 'CHANGE_PASSWORD', 'SUCCESS', get_client_ip(), parse_user_agent(), "Password updated successfully.")
    flash("Your password has been updated successfully.", 'success')
    return redirect(url_for('main.settings_page'))
