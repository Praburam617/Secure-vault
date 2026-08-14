import os
from datetime import datetime, timezone, timedelta
from flask import render_template, redirect, url_for, flash, request, send_file, jsonify, current_app, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.main import main_bp
from app.models import db, FileModel, ActivityLog, ShareLink, UserSession, UserSettings
from app.services.file_service import FileService
from app.services.encryption import EncryptionService
from app.services.decryption import DecryptionService
from app.services.hash_service import HashService
from app.services.security_service import SecurityService
from app.services.report_service import ReportService
from app.utils.helpers import get_client_ip, parse_user_agent, generate_random_token, build_share_url

@main_bp.route('/')
def landing():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('landing.html')


@main_bp.route('/how-it-works')
def how_it_works():
    """Dedicated How It Works page route."""
    return render_template('how_it_works.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    stats = ReportService.generate_summary(current_user)
    recent_files = current_user.files.filter_by(is_in_trash=False).order_by(FileModel.created_at.desc()).limit(5).all()
    recent_activity = current_user.activity_logs.order_by(ActivityLog.created_at.desc()).limit(8).all()
    
    return render_template('dashboard.html', 
                           stats=stats, 
                           recent_files=recent_files, 
                           recent_activity=recent_activity)


@main_bp.route('/vault')
@login_required
def vault():
    filter_type = request.args.get('filter', 'all')
    search_query = request.args.get('q', '').strip()

    query = FileModel.query.filter_by(user_id=current_user.id)

    if filter_type == 'encrypted':
        query = query.filter_by(is_encrypted=True, is_in_trash=False)
    elif filter_type == 'shared':
        query = query.filter_by(is_shared=True, is_in_trash=False)
    elif filter_type == 'trash':
        query = query.filter_by(is_in_trash=True)
    else: # all
        query = query.filter_by(is_in_trash=False)

    if search_query:
        query = query.filter(FileModel.original_filename.ilike(f"%{search_query}%"))

    files = query.order_by(FileModel.created_at.desc()).all()
    trash_count = FileModel.query.filter_by(user_id=current_user.id, is_in_trash=True).count()

    return render_template('vault.html', files=files, current_filter=filter_type, search_query=search_query, trash_count=trash_count)


@main_bp.route('/encrypt', methods=['GET', 'POST'])
@login_required
def encrypt_page():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No file provided for protection.", 'danger')
            return redirect(url_for('main.encrypt_page'))

        file = request.files['file']
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        retention_days = int(request.form.get('retention_days', 0))

        if not file or file.filename == '':
            flash("No selected file.", 'danger')
            return redirect(url_for('main.encrypt_page'))

        if not password or len(password) < 6:
            flash("Protection password must be at least 6 characters long.", 'danger')
            return redirect(url_for('main.encrypt_page'))

        if password != confirm_password:
            flash("Protection passwords do not match.", 'danger')
            return redirect(url_for('main.encrypt_page'))

        original_filename = secure_filename(file.filename)
        if not original_filename:
            original_filename = "protected_file"

        ext = FileService.get_extension(original_filename)
        if not FileService.validate_file_extension(original_filename):
            flash(f"Unsupported file extension '.{ext}'. Supported types: PDF, DOCX, TXT, ZIP, PNG, JPG, MP4, CSV, PPTX.", 'danger')
            SecurityService.log_event(current_user.id, 'UPLOAD_REJECTED', 'FAILED', get_client_ip(), parse_user_agent(), f"Invalid extension: {ext}")
            return redirect(url_for('main.encrypt_page'))

        # Save raw temporary upload
        temp_raw_filename = f"raw_{generate_random_token(16)}.{ext}"
        temp_raw_path = os.path.join(current_app.config['RAW_FOLDER'], temp_raw_filename)
        file.save(temp_raw_path)

        # File size check
        file_size = os.path.getsize(temp_raw_path)
        if file_size > current_app.config['MAX_CONTENT_LENGTH']:
            FileService.secure_wipe_file(temp_raw_path)
            flash("File size exceeds maximum allowable limit (50 MB).", 'danger')
            return redirect(url_for('main.encrypt_page'))

        # Validate magic numbers
        if not FileService.validate_magic_bytes(temp_raw_path, ext):
            FileService.secure_wipe_file(temp_raw_path)
            flash(f"File magic byte signature does not match extension '.{ext}'. Upload rejected.", 'danger')
            SecurityService.log_event(current_user.id, 'UPLOAD_MIME_SPOOF', 'FAILED', get_client_ip(), parse_user_agent(), f"Spoofed file header for extension: {ext}")
            return redirect(url_for('main.encrypt_page'))

        # Generate storage filename for encrypted payload
        stored_filename = FileService.generate_storage_filename("enc")
        encrypted_output_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], stored_filename)

        try:
            # Perform AES-256-GCM Encryption
            salt_hex, nonce_hex, raw_sha256, ciphertext_sha256 = EncryptionService.encrypt_file(
                temp_raw_path, encrypted_output_path, password
            )

            # Clean up temp raw file immediately
            FileService.secure_wipe_file(temp_raw_path)

            # Store metadata in DB
            new_file = FileModel(
                user_id=current_user.id,
                original_filename=original_filename,
                stored_filename=stored_filename,
                file_size=file_size,
                mime_type=file.content_type or 'application/octet-stream',
                file_extension=ext,
                enc_salt=salt_hex,
                enc_nonce=nonce_hex,
                sha256_hash=raw_sha256,
                ciphertext_hash=ciphertext_sha256,
                is_encrypted=True,
                is_shared=True,
                retention_days=retention_days
            )
            db.session.add(new_file)
            db.session.commit()

            # Create automatic high-entropy share link for post-encryption completion UI
            share_token = generate_random_token(24)
            share_link = ShareLink(
                file_id=new_file.id,
                user_id=current_user.id,
                share_token=share_token,
                max_downloads=None,
                expires_at=None
            )
            db.session.add(share_link)
            db.session.commit()

            SecurityService.log_event(current_user.id, 'ENCRYPT_FILE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Encrypted file: {original_filename} ({new_file.formatted_size()})")
            
            share_url = build_share_url(share_token)

            # Render encrypt page with post-encryption success card containing share URL
            return render_template('encrypt.html', 
                                   encryption_success=True, 
                                   protected_file=new_file, 
                                   share_url=share_url,
                                   share_token=share_token)

        except Exception as e:
            FileService.secure_wipe_file(temp_raw_path)
            db.session.rollback()
            SecurityService.log_event(current_user.id, 'ENCRYPT_FAILED', 'FAILED', get_client_ip(), parse_user_agent(), str(e))
            flash(f"Encryption failed: {str(e)}", 'danger')
            return redirect(url_for('main.encrypt_page'))

    return render_template('encrypt.html')


@main_bp.route('/decrypt', methods=['GET', 'POST'])
@login_required
def decrypt_page():
    """Dedicated Standalone Decrypt Page."""
    if request.method == 'POST':
        password = request.form.get('password', '')

        # Option A: File uploaded directly on decrypt page
        if 'file' in request.files and request.files['file'].filename != '':
            uploaded_file = request.files['file']
            filename = secure_filename(uploaded_file.filename) or "encrypted_file.enc"
            
            temp_enc_name = f"dec_in_{generate_random_token(16)}.enc"
            temp_enc_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], temp_enc_name)
            uploaded_file.save(temp_enc_path)

            temp_dec_name = f"dec_out_{generate_random_token(16)}"
            temp_dec_path = os.path.join(current_app.config['DECRYPTED_FOLDER'], temp_dec_name)

            try:
                DecryptionService.decrypt_file(
                    temp_enc_path,
                    temp_dec_path,
                    password
                )
                FileService.secure_wipe_file(temp_enc_path)

                SecurityService.log_event(current_user.id, 'DECRYPT_STANDALONE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Decrypted uploaded file: {filename}")

                out_filename = filename.replace('.enc', '') if filename.endswith('.enc') else f"decrypted_{filename}"
                response = send_file(
                    temp_dec_path,
                    as_attachment=True,
                    download_name=out_filename
                )
                @response.call_on_close
                def cleanup():
                    FileService.secure_wipe_file(temp_dec_path)

                return response
            except Exception as e:
                FileService.secure_wipe_file(temp_enc_path)
                FileService.secure_wipe_file(temp_dec_path)
                SecurityService.log_event(current_user.id, 'DECRYPT_FAILED', 'FAILED', get_client_ip(), parse_user_agent(), str(e))
                flash(str(e), 'danger')
                return render_template('decrypt.html')

        # Option B: Decrypting a file selected by ID from user's vault
        file_id = request.form.get('file_id', type=int)
        if file_id:
            file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
            encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], file_record.stored_filename)
            temp_decrypted_filename = f"dec_{generate_random_token(16)}.{file_record.file_extension}"
            decrypted_output_path = os.path.join(current_app.config['DECRYPTED_FOLDER'], temp_decrypted_filename)

            try:
                DecryptionService.decrypt_file(
                    encrypted_path,
                    decrypted_output_path,
                    password,
                    expected_raw_sha256=file_record.sha256_hash
                )

                SecurityService.log_event(current_user.id, 'DECRYPT_FILE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Decrypted file: {file_record.original_filename}")

                response = send_file(
                    decrypted_output_path,
                    as_attachment=True,
                    download_name=file_record.original_filename
                )
                @response.call_on_close
                def cleanup():
                    FileService.secure_wipe_file(decrypted_output_path)

                return response
            except Exception as e:
                SecurityService.log_event(current_user.id, 'DECRYPT_FAILED', 'FAILED', get_client_ip(), parse_user_agent(), str(e))
                flash(str(e), 'danger')
                return render_template('decrypt.html')

        flash("Please upload an encrypted file or select a file from your vault.", 'danger')
        return render_template('decrypt.html')

    user_files = current_user.files.filter_by(is_in_trash=False, is_encrypted=True).all()
    return render_template('decrypt.html', user_files=user_files)


@main_bp.route('/vault/decrypt/<int:file_id>', methods=['POST'])
@login_required
def decrypt_file(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    password = request.form.get('password', '')

    if not password:
        flash("Protection password is required to decrypt this file.", 'danger')
        return redirect(url_for('main.vault'))

    encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], file_record.stored_filename)
    temp_decrypted_filename = f"dec_{generate_random_token(16)}.{file_record.file_extension}"
    decrypted_output_path = os.path.join(current_app.config['DECRYPTED_FOLDER'], temp_decrypted_filename)

    try:
        DecryptionService.decrypt_file(
            encrypted_path,
            decrypted_output_path,
            password,
            expected_raw_sha256=file_record.sha256_hash
        )

        SecurityService.log_event(current_user.id, 'DECRYPT_FILE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Decrypted file: {file_record.original_filename}")

        response = send_file(
            decrypted_output_path,
            as_attachment=True,
            download_name=file_record.original_filename
        )
        
        @response.call_on_close
        def cleanup():
            FileService.secure_wipe_file(decrypted_output_path)

        return response

    except ValueError as e:
        SecurityService.log_event(current_user.id, 'DECRYPT_FAILED', 'FAILED', get_client_ip(), parse_user_agent(), f"Failed decryption for file ID {file_id}: {str(e)}")
        flash(str(e), 'danger')
        return redirect(url_for('main.vault'))
    except Exception as e:
        SecurityService.log_event(current_user.id, 'DECRYPT_ERROR', 'FAILED', get_client_ip(), parse_user_agent(), str(e))
        flash("An unexpected error occurred during decryption.", 'danger')
        return redirect(url_for('main.vault'))


@main_bp.route('/vault/download/<int:file_id>')
@login_required
def download_encrypted(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], file_record.stored_filename)

    if not os.path.exists(encrypted_path):
        flash("File payload not found on disk.", 'danger')
        return redirect(url_for('main.vault'))

    SecurityService.log_event(current_user.id, 'DOWNLOAD_ENCRYPTED', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Downloaded encrypted payload for: {file_record.original_filename}")
    return send_file(
        encrypted_path,
        as_attachment=True,
        download_name=f"{file_record.original_filename}.enc"
    )


@main_bp.route('/vault/rename/<int:file_id>', methods=['POST'])
@login_required
def rename_file(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    new_name = request.form.get('new_filename', '').strip()

    if not new_name:
        flash("Filename cannot be empty.", 'danger')
        return redirect(url_for('main.vault'))

    new_name = secure_filename(new_name)
    if '.' not in new_name and file_record.file_extension:
        new_name = f"{new_name}.{file_record.file_extension}"

    old_name = file_record.original_filename
    file_record.original_filename = new_name
    db.session.commit()

    SecurityService.log_event(current_user.id, 'RENAME_FILE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Renamed '{old_name}' to '{new_name}'")
    flash("File renamed successfully.", 'success')
    return redirect(url_for('main.vault'))


@main_bp.route('/vault/share/<int:file_id>', methods=['POST'])
@login_required
def create_share(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    share_password = request.form.get('share_password', '').strip()
    max_downloads = request.form.get('max_downloads', type=int)
    expiry_hours = request.form.get('expiry_hours', type=int)

    expires_at = None
    if expiry_hours and expiry_hours > 0:
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)

    share_token = generate_random_token(24)
    share_link = ShareLink(
        file_id=file_record.id,
        user_id=current_user.id,
        share_token=share_token,
        max_downloads=max_downloads if max_downloads and max_downloads > 0 else None,
        expires_at=expires_at
    )
    if share_password:
        share_link.set_password(share_password)

    file_record.is_shared = True
    db.session.add(share_link)
    db.session.commit()

    SecurityService.log_event(current_user.id, 'CREATE_SHARE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Created share link for file: {file_record.original_filename}")
    
    share_url = build_share_url(share_token)

    # AJAX request — return JSON so vault modal can display link inline
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        response_data = {
            'share_url': share_url,
            'has_password': bool(share_password),
            'max_downloads': max_downloads if max_downloads and max_downloads > 0 else None,
            'expires_at': expires_at.strftime('%Y-%m-%d %H:%M UTC') if expires_at else None,
        }
        return jsonify(response_data)

    # Standard form submit — redirect with flash
    flash(f"Secure share link created! URL: {share_url}", 'success')
    return redirect(url_for('main.vault'))



@main_bp.route('/share/<string:token>', methods=['GET', 'POST'])
def access_share(token):
    share_link = ShareLink.query.filter_by(share_token=token).first_or_404()

    if not share_link.is_valid():
        return render_template('share.html', expired=True)

    file_record = share_link.file

    if request.method == 'POST':
        share_password = request.form.get('share_password', '')
        file_password = request.form.get('file_password', '')

        if share_link.password_hash and not share_link.check_password(share_password):
            flash("Incorrect share link password.", 'danger')
            return render_template('share.html', share_link=share_link, file_record=file_record, requires_password=True)

        if not file_password:
            flash("File protection password is required to decrypt.", 'danger')
            return render_template('share.html', share_link=share_link, file_record=file_record, password_ok=True)

        encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], file_record.stored_filename)
        temp_decrypted_filename = f"share_dec_{generate_random_token(16)}.{file_record.file_extension}"
        decrypted_output_path = os.path.join(current_app.config['DECRYPTED_FOLDER'], temp_decrypted_filename)

        try:
            DecryptionService.decrypt_file(
                encrypted_path,
                decrypted_output_path,
                file_password,
                expected_raw_sha256=file_record.sha256_hash
            )

            share_link.download_count += 1
            if share_link.max_downloads and share_link.download_count >= share_link.max_downloads:
                share_link.is_active = False
            db.session.commit()

            SecurityService.log_event(share_link.user_id, 'SHARE_DOWNLOAD', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Shared file accessed: {file_record.original_filename}")

            response = send_file(
                decrypted_output_path,
                as_attachment=True,
                download_name=file_record.original_filename
            )
            
            @response.call_on_close
            def cleanup():
                FileService.secure_wipe_file(decrypted_output_path)

            return response

        except ValueError as e:
            err_msg = str(e)
            # Provide user-friendly messages
            if 'password' in err_msg.lower() or 'authentication' in err_msg.lower() or 'tag' in err_msg.lower():
                friendly = "❌ Wrong password — decryption failed. Please check the password and try again."
            elif 'integrity' in err_msg.lower() or 'hash' in err_msg.lower():
                friendly = "⚠️ File integrity check failed — the file may have been corrupted."
            else:
                friendly = f"Decryption failed: {err_msg}"
            flash(friendly, 'danger')
            return render_template('share.html', share_link=share_link, file_record=file_record,
                                   requires_password=bool(share_link.password_hash), password_ok=True)

    requires_password = bool(share_link.password_hash)
    return render_template('share.html', share_link=share_link, file_record=file_record, requires_password=requires_password)



@main_bp.route('/vault/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    file_record.is_in_trash = True
    file_record.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

    SecurityService.log_event(current_user.id, 'MOVE_TRASH', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Moved to trash: {file_record.original_filename}")
    flash(f"File '{file_record.original_filename}' moved to Trash.", 'info')
    return redirect(url_for('main.vault'))


@main_bp.route('/vault/restore/<int:file_id>', methods=['POST'])
@login_required
def restore_file(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    file_record.is_in_trash = False
    file_record.deleted_at = None
    db.session.commit()

    SecurityService.log_event(current_user.id, 'RESTORE_TRASH', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Restored file: {file_record.original_filename}")
    flash(f"File '{file_record.original_filename}' restored from Trash.", 'success')
    return redirect(url_for('main.vault', filter='trash'))


@main_bp.route('/vault/purge/<int:file_id>', methods=['POST'])
@login_required
def purge_file(file_id):
    file_record = FileModel.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    encrypted_path = os.path.join(current_app.config['ENCRYPTED_FOLDER'], file_record.stored_filename)

    FileService.secure_wipe_file(encrypted_path)
    original_name = file_record.original_filename

    db.session.delete(file_record)
    db.session.commit()

    SecurityService.log_event(current_user.id, 'PERMANENT_DELETE', 'SUCCESS', get_client_ip(), parse_user_agent(), f"Permanently wiped file: {original_name}")
    flash(f"File '{original_name}' permanently deleted and securely wiped from disk.", 'success')
    return redirect(url_for('main.vault', filter='trash'))


@main_bp.route('/activity')
@login_required
def activity():
    page = request.args.get('page', 1, type=int)
    logs = current_user.activity_logs.order_by(ActivityLog.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template('activity.html', logs=logs)


@main_bp.route('/security')
@login_required
def security():
    score = current_user.calculate_security_score()
    score_label, score_class = current_user.get_score_label()
    active_sessions_count = current_user.sessions.filter_by(is_active=True).count()

    return render_template('security.html', 
                           score=score, 
                           score_label=score_label, 
                           score_class=score_class,
                           active_sessions_count=active_sessions_count)


@main_bp.route('/profile')
@login_required
def profile():
    stats = ReportService.generate_summary(current_user)
    return render_template('profile.html', stats=stats)


@main_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings_page():
    user_settings = current_user.settings
    if not user_settings:
        user_settings = UserSettings(user_id=current_user.id)
        db.session.add(user_settings)
        db.session.commit()

    if request.method == 'POST':
        login_alerts = True if request.form.get('login_alerts') else False
        default_retention = int(request.form.get('default_retention_days', 0))
        theme = request.form.get('theme', 'dark')
        reduced_motion = True if request.form.get('reduced_motion') else False

        user_settings.login_alerts = login_alerts
        user_settings.default_retention_days = default_retention
        user_settings.theme = theme
        user_settings.reduced_motion = reduced_motion

        db.session.commit()
        SecurityService.log_event(current_user.id, 'UPDATE_SETTINGS', 'SUCCESS', get_client_ip(), parse_user_agent(), "Updated security & privacy settings.")
        flash("Settings updated successfully.", 'success')
        return redirect(url_for('main.settings_page'))

    return render_template('settings.html', settings=user_settings)


@main_bp.route('/sessions', methods=['GET', 'POST'])
@login_required
def sessions_page():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'revoke_others':
            current_token = session.get('session_token')
            UserSession.query.filter(
                UserSession.user_id == current_user.id,
                UserSession.session_token != current_token,
                UserSession.is_active == True
            ).update({'is_active': False})
            db.session.commit()

            SecurityService.log_event(current_user.id, 'REVOKE_SESSIONS', 'SUCCESS', get_client_ip(), parse_user_agent(), "Revoked all other active sessions.")
            flash("Signed out of all other sessions successfully.", 'success')
            return redirect(url_for('main.sessions_page'))

    active_sessions = current_user.sessions.filter_by(is_active=True).order_by(UserSession.last_seen.desc()).all()
    current_token = session.get('session_token')
    return render_template('sessions.html', sessions=active_sessions, current_token=current_token)


@main_bp.route('/reports')
@login_required
def reports():
    export_format = request.args.get('format')
    summary_data = ReportService.generate_summary(current_user)

    if export_format == 'json':
        export_dict = {
            'generated_at': summary_data['generated_at'],
            'user': summary_data['username'],
            'email': summary_data['email'],
            'security_score': summary_data['security_score'],
            'metrics': {
                'total_files': summary_data['total_files'],
                'encrypted_files': summary_data['encrypted_files'],
                'shared_files': summary_data['shared_files'],
                'storage_used': summary_data['storage_used_formatted'],
                'encryption_events': summary_data['encryption_events'],
                'decryption_events': summary_data['decryption_events'],
                'security_alerts': summary_data['security_alerts']
            }
        }
        return jsonify(export_dict)

    return render_template('reports.html', summary=summary_data)
