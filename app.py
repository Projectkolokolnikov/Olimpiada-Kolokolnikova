from flask import (Flask, render_template, request, redirect,
                   url_for, flash, session, send_file, jsonify)
from flask_mail import Mail, Message
import openpyxl
import os
import json
from datetime import datetime
from functools import wraps
import hashlib
import secrets

app = Flask(__name__)
app.secret_key = 'olimpiada_secret_key_2024_very_long'

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'
app.config['MAIL_DEFAULT_SENDER'] = ('Олимпиада Колокольникова', 'your_email@gmail.com')

mail = Mail(app)

DATA_DIR = 'data'
TASKS_DIR = 'static/tasks'
SCANS_DIR = 'static/scans'
DOCS_DIR  = 'static/docs'
USERS_FILE       = os.path.join(DATA_DIR, 'users.json')
ADMINS_FILE      = os.path.join(DATA_DIR, 'admins.json')
REVIEWS_FILE     = os.path.join(DATA_DIR, 'reviews.json')
NEWS_FILE        = os.path.join(DATA_DIR, 'news.json')
TASKS_FILE       = os.path.join(DATA_DIR, 'tasks.json')
RESULTS_FILE     = os.path.join(DATA_DIR, 'results.json')

for d in [DATA_DIR, TASKS_DIR, SCANS_DIR, DOCS_DIR]:
    os.makedirs(d, exist_ok=True)

# ==================== УТИЛИТЫ ====================

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def load_json(path, default=None):
    if default is None:
        default = []
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return default
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_by_email(email):
    users = load_json(USERS_FILE)
    return next((u for u in users if u['email'] == email.lower()), None)

def get_user_by_id(user_id):
    users = load_json(USERS_FILE)
    return next((u for u in users if u['id'] == user_id), None)

def save_user(user):
    users = load_json(USERS_FILE)
    for i, u in enumerate(users):
        if u['id'] == user['id']:
            users[i] = user
            save_json(USERS_FILE, users)
            return
    users.append(user)
    save_json(USERS_FILE, users)

def get_admin_by_login(login):
    admins = load_json(ADMINS_FILE)
    if not admins:
        return {
            'id': 1,
            'login': 'admin',
            'password': hash_password('olimpiada2024'),
            'name': 'Главный администратор',
            'super': True
        }
    return next((a for a in admins if a['login'] == login), None)

def init_default_admin():
    if not os.path.exists(ADMINS_FILE):
        default = [{
            'id': 1,
            'login': 'admin',
            'password': hash_password('olimpiada2024'),
            'name': 'Главный администратор',
            'super': True
        }]
        save_json(ADMINS_FILE, default)

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('user_id'):
            flash('Войдите в личный кабинет.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated

def send_email_safe(subject, recipients, html_body):
    try:
        msg = Message(subject=subject, recipients=recipients, html=html_body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f'[MAIL ERROR] {e}')
        return False

init_default_admin()

# ==================== ПУБЛИЧНЫЕ СТРАНИЦЫ ====================

@app.route('/')
def index():
    news_list = load_json(NEWS_FILE)
    recent_news = sorted(
        [n for n in news_list if n.get('published')],
        key=lambda x: x.get('id', 0), reverse=True
    )[:4]
    reviews = [r for r in load_json(REVIEWS_FILE) if r.get('approved')]
    return render_template('index.html', recent_news=recent_news, reviews=reviews)

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/news')
def news():
    news_list = sorted(
        [n for n in load_json(NEWS_FILE) if n.get('published')],
        key=lambda x: x.get('id', 0), reverse=True
    )
    return render_template('news.html', news_list=news_list)

@app.route('/news/<int:news_id>')
def news_detail(news_id):
    item = next((n for n in load_json(NEWS_FILE)
                 if n['id'] == news_id and n.get('published')), None)
    if not item:
        return redirect(url_for('news'))
    return render_template('news_detail.html', item=item)

@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    reviews_list = load_json(REVIEWS_FILE)
    approved = [r for r in reviews_list if r.get('approved')]
    if request.method == 'POST':
        name   = request.form.get('name', '').strip()
        status = request.form.get('status', '')
        text   = request.form.get('review_text', '').strip()
        if name and status and text:
            new_r = {
                'id': int(datetime.now().timestamp() * 1000),
                'name': name, 'status': status, 'text': text,
                'short': text[:100] + '...' if len(text) > 100 else text,
                'approved': False,
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M')
            }
            reviews_list.append(new_r)
            save_json(REVIEWS_FILE, reviews_list)
            flash('Отзыв отправлен на модерацию. Спасибо!', 'success')
            return redirect(url_for('reviews'))
        flash('Заполните все поля.', 'error')
    return render_template('reviews.html', reviews=approved)

@app.route('/tasks')
def tasks():
    tasks_list = [t for t in load_json(TASKS_FILE) if t.get('published')]
    by_tour = {}
    for t in tasks_list:
        tour = t.get('tour', 'Прочее')
        by_tour.setdefault(tour, []).append(t)
    return render_template('tasks.html', by_tour=by_tour)

@app.route('/tasks/download/<int:task_id>')
def task_download(task_id):
    task = next((t for t in load_json(TASKS_FILE)
                 if t['id'] == task_id and t.get('published')), None)
    if task and os.path.exists(task.get('filepath', '')):
        return send_file(task['filepath'], as_attachment=True,
                         download_name=task.get('filename', 'task.pdf'))
    flash('Файл не найден.', 'error')
    return redirect(url_for('tasks'))

# Положение об олимпиаде
@app.route('/docs/polozhenie')
def polozhenie():
    filepath = os.path.join('static', 'docs', 'polozhenie.pdf')
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=False,
                         download_name='Положение_об_олимпиаде.pdf')
    flash('Файл положения об олимпиаде ещё не загружен.', 'error')
    return redirect(url_for('index'))

# ==================== АУТЕНТИФИКАЦИЯ ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if session.get('user_id'):
        return redirect(url_for('cabinet'))
    if request.method == 'POST':
        email     = request.form.get('email', '').strip().lower()
        password  = request.form.get('password', '')
        password2 = request.form.get('password2', '')

        if not email or not password:
            flash('Заполните все поля.', 'error')
            return render_template('auth/register.html')
        if password != password2:
            flash('Пароли не совпадают.', 'error')
            return render_template('auth/register.html')
        if len(password) < 6:
            flash('Пароль должен содержать не менее 6 символов.', 'error')
            return render_template('auth/register.html')
        if get_user_by_email(email):
            flash('Пользователь с таким email уже зарегистрирован.', 'error')
            return render_template('auth/register.html')

        user = {
            'id': int(datetime.now().timestamp() * 1000),
            'email': email,
            'password': hash_password(password),
            'profile_filled': False,
            'application_status': 'draft',
            'profile': {},
            'results': [],
            'created_at': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        save_user(user)

        send_email_safe(
            subject='Добро пожаловать на олимпиаду Колокольникова!',
            recipients=[email],
            html_body=render_template('emails/welcome.html', email=email)
        )

        session['user_id'] = user['id']
        flash('Регистрация прошла успешно! Заполните профиль для подачи заявки.', 'success')
        return redirect(url_for('cabinet'))
    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user_id'):
        return redirect(url_for('cabinet'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = get_user_by_email(email)
        if user and user['password'] == hash_password(password):
            session['user_id'] = user['id']
            return redirect(url_for('cabinet'))
        flash('Неверный email или пароль.', 'error')
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('login'))

@app.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user  = get_user_by_email(email)
        if user:
            token = secrets.token_urlsafe(32)
            users = load_json(USERS_FILE)
            for u in users:
                if u['id'] == user['id']:
                    u['reset_token']   = token
                    u['reset_expires'] = datetime.now().strftime('%d.%m.%Y %H:%M')
                    break
            save_json(USERS_FILE, users)
            reset_link = url_for('reset_password', token=token, _external=True)
            send_email_safe(
                subject='Восстановление пароля — Олимпиада Колокольникова',
                recipients=[email],
                html_body=render_template('emails/reset_password.html',
                                          reset_link=reset_link)
            )
        flash('Если email зарегистрирован — письмо отправлено.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/forgot.html')

@app.route('/reset/<token>', methods=['GET', 'POST'])
def reset_password(token):
    users = load_json(USERS_FILE)
    user  = next((u for u in users if u.get('reset_token') == token), None)
    if not user:
        flash('Ссылка недействительна или устарела.', 'error')
        return redirect(url_for('login'))
    if request.method == 'POST':
        password  = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        if password != password2 or len(password) < 6:
            flash('Пароли не совпадают или слишком короткий.', 'error')
            return render_template('auth/reset.html', token=token)
        for u in users:
            if u['id'] == user['id']:
                u['password'] = hash_password(password)
                u.pop('reset_token', None)
                u.pop('reset_expires', None)
                break
        save_json(USERS_FILE, users)
        flash('Пароль успешно изменён. Войдите.', 'success')
        return redirect(url_for('login'))
    return render_template('auth/reset.html', token=token)

# ==================== ЛИЧНЫЙ КАБИНЕТ ====================

@app.route('/cabinet')
@login_required
def cabinet():
    user = get_user_by_id(session['user_id'])
    if not user:
        session.pop('user_id', None)
        return redirect(url_for('login'))
    results      = load_json(RESULTS_FILE)
    user_results = [r for r in results if r.get('user_id') == user['id']]
    return render_template('cabinet/index.html', user=user, results=user_results)

@app.route('/cabinet/profile', methods=['GET', 'POST'])
@login_required
def cabinet_profile():
    user = get_user_by_id(session['user_id'])
    if request.method == 'POST':
        profile = {
            'fio':                 request.form.get('fio', '').strip(),
            'gender':              request.form.get('gender', ''),
            'birthdate':           request.form.get('birthdate', ''),
            'snils':               request.form.get('snils', '').strip(),
            'citizenship':         request.form.get('citizenship', 'Россия').strip(),
            'phone':               request.form.get('phone', '').strip(),
            'school':              request.form.get('school', '').strip(),
            'study_class':         request.form.get('study_class', ''),
            'participation_class': request.form.get('participation_class', ''),
        }
        required = ['fio', 'gender', 'birthdate', 'snils',
                    'citizenship', 'phone', 'school',
                    'study_class', 'participation_class']
        if not all(profile[f] for f in required):
            flash('Заполните все обязательные поля.', 'error')
            return render_template('cabinet/profile.html', user=user)

        users = load_json(USERS_FILE)
        for u in users:
            if u['id'] == user['id']:
                u['profile']        = profile
                u['profile_filled'] = True
                break
        save_json(USERS_FILE, users)
        flash('Профиль сохранён.', 'success')
        return redirect(url_for('cabinet'))
    return render_template('cabinet/profile.html', user=user)

@app.route('/cabinet/apply', methods=['POST'])
@login_required
def cabinet_apply():
    user = get_user_by_id(session['user_id'])
    if not user.get('profile_filled'):
        flash('Сначала заполните профиль.', 'error')
        return redirect(url_for('cabinet_profile'))
    if user.get('application_status') not in ['draft', 'rejected']:
        flash('Заявка уже подана.', 'error')
        return redirect(url_for('cabinet'))

    users = load_json(USERS_FILE)
    for u in users:
        if u['id'] == user['id']:
            u['application_status'] = 'new'
            u['applied_at']         = datetime.now().strftime('%d.%m.%Y %H:%M')
            break
    save_json(USERS_FILE, users)

    send_email_safe(
        subject='Заявка на олимпиаду принята!',
        recipients=[user['email']],
        html_body=render_template('emails/application_received.html', user=user)
    )
    flash('Заявка успешно подана! Ожидайте подтверждения.', 'success')
    return redirect(url_for('cabinet'))

@app.route('/cabinet/results')
@login_required
def cabinet_results():
    user         = get_user_by_id(session['user_id'])
    results      = load_json(RESULTS_FILE)
    user_results = [r for r in results if r.get('user_id') == user['id']]
    return render_template('cabinet/results.html', user=user, results=user_results)

@app.route('/cabinet/results/scan/<int:result_id>')
@login_required
def cabinet_scan(result_id):
    results = load_json(RESULTS_FILE)
    result  = next((r for r in results
                    if r['id'] == result_id
                    and r.get('user_id') == session['user_id']), None)
    if result and os.path.exists(result.get('scan_path', '')):
        return send_file(result['scan_path'], as_attachment=False,
                         download_name=result['scan_name'])
    flash('Файл не найден.', 'error')
    return redirect(url_for('cabinet_results'))

# ==================== АДМИН ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        login_val = request.form.get('login', '')
        password  = request.form.get('password', '')
        admin     = get_admin_by_login(login_val)
        if admin and admin['password'] == hash_password(password):
            session['admin_logged_in'] = True
            session['admin_id']        = admin['id']
            session['admin_name']      = admin['name']
            session['admin_super']     = admin.get('super', False)
            return redirect(url_for('admin_dashboard'))
        flash('Неверный логин или пароль.', 'error')
    return render_template('admin/login.html')

@app.route('/admin/logout')
def admin_logout():
    for k in ['admin_logged_in', 'admin_id', 'admin_name', 'admin_super']:
        session.pop(k, None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@admin_required
def admin_dashboard():
    users        = load_json(USERS_FILE)
    reviews_list = load_json(REVIEWS_FILE)
    news_list    = load_json(NEWS_FILE)
    tasks_list   = load_json(TASKS_FILE)
    pol_exists   = os.path.exists(os.path.join('static', 'docs', 'polozhenie.pdf'))
    stats = {
        'regs_total':       len(users),
        'regs_new':         len([u for u in users if u.get('application_status') == 'new']),
        'regs_approved':    len([u for u in users if u.get('application_status') == 'approved']),
        'reviews_pending':  len([r for r in reviews_list if not r.get('approved')]),
        'news_count':       len(news_list),
        'tasks_count':      len(tasks_list),
        'pol_exists':       pol_exists,
    }
    return render_template('admin/dashboard.html', stats=stats)

# --- УЧАСТНИКИ ---
@app.route('/admin/participants')
@admin_required
def admin_participants():
    users         = load_json(USERS_FILE)
    users         = sorted(users, key=lambda x: x.get('id', 0), reverse=True)
    filter_status = request.args.get('status', 'all')
    if filter_status != 'all':
        users = [u for u in users if u.get('application_status') == filter_status]
    return render_template('admin/participants.html',
                           users=users, filter_status=filter_status)

@app.route('/admin/participants/<int:user_id>')
@admin_required
def admin_participant_detail(user_id):
    user    = get_user_by_id(user_id)
    if not user:
        return redirect(url_for('admin_participants'))
    results = [r for r in load_json(RESULTS_FILE) if r.get('user_id') == user_id]
    return render_template('admin/participant_detail.html',
                           user=user, results=results)

@app.route('/admin/participants/<int:user_id>/action', methods=['POST'])
@admin_required
def admin_participant_action(user_id):
    action = request.form.get('action')
    users  = load_json(USERS_FILE)
    user   = next((u for u in users if u['id'] == user_id), None)
    if not user:
        return redirect(url_for('admin_participants'))

    if action == 'approve':
        user['application_status'] = 'approved'
        send_email_safe(
            subject='Ваша заявка одобрена — Олимпиада Колокольникова',
            recipients=[user['email']],
            html_body=render_template('emails/application_approved.html', user=user)
        )
        flash('Заявка одобрена. Письмо отправлено.', 'success')
    elif action == 'reject':
        user['application_status'] = 'rejected'
        reason = request.form.get('reason', '')
        user['reject_reason'] = reason
        send_email_safe(
            subject='Информация по вашей заявке — Олимпиада Колокольникова',
            recipients=[user['email']],
            html_body=render_template('emails/application_rejected.html',
                                      user=user, reason=reason)
        )
        flash('Заявка отклонена. Письмо отправлено.', 'success')

    save_json(USERS_FILE, users)
    return redirect(url_for('admin_participant_detail', user_id=user_id))

@app.route('/admin/participants/export')
@admin_required
def admin_export_excel():
    users = load_json(USERS_FILE)
    wb    = openpyxl.Workbook()
    ws    = wb.active
    ws.title = 'Участники'
    headers = ['ID', 'Email', 'ФИО', 'Пол', 'Дата рождения', 'СНИЛС',
               'Гражданство', 'Телефон', 'Место обучения',
               'Класс обучения', 'Класс участия', 'Статус заявки', 'Дата регистрации']
    ws.append(headers)
    for u in users:
        p = u.get('profile', {})
        ws.append([
            u.get('id'), u.get('email'),
            p.get('fio'), p.get('gender'), p.get('birthdate'), p.get('snils'),
            p.get('citizenship'), p.get('phone'), p.get('school'),
            p.get('study_class'), p.get('participation_class'),
            u.get('application_status'), u.get('created_at')
        ])
    for col in ws.columns:
        max_len = max((len(str(cell.value or '')) for cell in col), default=10)
        ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)
    filepath = os.path.join(DATA_DIR, 'export.xlsx')
    wb.save(filepath)
    return send_file(filepath, as_attachment=True, download_name='participants.xlsx')

# --- РЕЗУЛЬТАТЫ ---
@app.route('/admin/results/add', methods=['GET', 'POST'])
@admin_required
def admin_add_result():
    users = load_json(USERS_FILE)
    if request.method == 'POST':
        user_id = int(request.form.get('user_id', 0))
        user    = get_user_by_id(user_id)
        if not user:
            flash('Участник не найден.', 'error')
            return redirect(url_for('admin_add_result'))

        scan_file  = request.files.get('scan')
        scan_path  = ''
        scan_name  = ''
        if scan_file and scan_file.filename:
            scan_name = f"{user_id}_{int(datetime.now().timestamp())}_{scan_file.filename}"
            scan_path = os.path.join(SCANS_DIR, scan_name)
            scan_file.save(scan_path)

        result = {
            'id':        int(datetime.now().timestamp() * 1000),
            'user_id':   user_id,
            'user_email':user.get('email'),
            'user_fio':  user.get('profile', {}).get('fio', user.get('email')),
            'tour':      request.form.get('tour', ''),
            'score':     request.form.get('score', ''),
            'max_score': request.form.get('max_score', ''),
            'diploma':   request.form.get('diploma', ''),
            'comment':   request.form.get('comment', ''),
            'scan_name': scan_name,
            'scan_path': scan_path,
            'added_at':  datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        results = load_json(RESULTS_FILE)
        results.append(result)
        save_json(RESULTS_FILE, results)

        send_email_safe(
            subject=f'Результаты {result["tour"]} — Олимпиада Колокольникова',
            recipients=[user['email']],
            html_body=render_template('emails/results_published.html',
                                      user=user, result=result)
        )
        flash('Результат добавлен и участник уведомлён.', 'success')
        return redirect(url_for('admin_participant_detail', user_id=user_id))

    approved_users = [u for u in users if u.get('application_status') == 'approved']
    return render_template('admin/result_form.html', users=approved_users)

@app.route('/admin/results/scan/<int:result_id>')
@admin_required
def admin_download_scan(result_id):
    results = load_json(RESULTS_FILE)
    result  = next((r for r in results if r['id'] == result_id), None)
    if result and os.path.exists(result.get('scan_path', '')):
        return send_file(result['scan_path'], as_attachment=False,
                         download_name=result['scan_name'])
    flash('Файл не найден.', 'error')
    return redirect(url_for('admin_participants'))

# --- ПОЛОЖЕНИЕ ОБ ОЛИМПИАДЕ (загрузка через админку) ---
@app.route('/admin/upload-polozhenie', methods=['GET', 'POST'])
@admin_required
def admin_upload_polozhenie():
    filepath = os.path.join('static', 'docs', 'polozhenie.pdf')
    exists   = os.path.exists(filepath)

    if request.method == 'POST':
        file = request.files.get('file')
        if file and file.filename:
            os.makedirs(os.path.join('static', 'docs'), exist_ok=True)
            file.save(filepath)
            flash('Положение об олимпиаде загружено!', 'success')
            return redirect(url_for('admin_upload_polozhenie'))
        flash('Выберите файл.', 'error')

    return render_template('admin/upload_polozhenie.html', exists=exists)

# --- ОТЗЫВЫ ---
@app.route('/admin/reviews')
@admin_required
def admin_reviews():
    reviews_list = sorted(load_json(REVIEWS_FILE),
                          key=lambda x: x.get('id', 0), reverse=True)
    return render_template('admin/reviews.html', reviews=reviews_list)

@app.route('/admin/reviews/add', methods=['GET', 'POST'])
@admin_required
def admin_add_review():
    if request.method == 'POST':
        reviews_list = load_json(REVIEWS_FILE)
        text = request.form.get('text', '').strip()
        new_r = {
            'id':        int(datetime.now().timestamp() * 1000),
            'name':      request.form.get('name', '').strip(),
            'status':    request.form.get('status', 'участник'),
            'text':      text,
            'short':     text[:100] + '...' if len(text) > 100 else text,
            'approved':  True,
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        reviews_list.append(new_r)
        save_json(REVIEWS_FILE, reviews_list)
        flash('Отзыв добавлен.', 'success')
        return redirect(url_for('admin_reviews'))
    return render_template('admin/review_form.html')

@app.route('/admin/reviews/<int:rev_id>/action', methods=['POST'])
@admin_required
def admin_review_action(rev_id):
    action       = request.form.get('action')
    reviews_list = load_json(REVIEWS_FILE)
    for r in reviews_list:
        if r['id'] == rev_id:
            if action == 'approve':
                r['approved'] = True
                flash('Отзыв одобрен.', 'success')
            elif action == 'reject':
                r['approved'] = False
                flash('Отзыв скрыт.', 'success')
            elif action == 'delete':
                reviews_list.remove(r)
                flash('Отзыв удалён.', 'success')
                save_json(REVIEWS_FILE, reviews_list)
                return redirect(url_for('admin_reviews'))
            break
    save_json(REVIEWS_FILE, reviews_list)
    return redirect(url_for('admin_reviews'))

# --- НОВОСТИ ---
@app.route('/admin/news')
@admin_required
def admin_news():
    news_list = sorted(load_json(NEWS_FILE),
                       key=lambda x: x.get('id', 0), reverse=True)
    return render_template('admin/news.html', news_list=news_list)

@app.route('/admin/news/add', methods=['GET', 'POST'])
@admin_required
def admin_add_news():
    if request.method == 'POST':
        news_list = load_json(NEWS_FILE)
        title     = request.form.get('title', '').strip()
        text      = request.form.get('text', '').strip()
        if title and text:
            item = {
                'id':        int(datetime.now().timestamp() * 1000),
                'title':     title, 'text': text,
                'preview':   text[:120] + '...' if len(text) > 120 else text,
                'date':      datetime.now().strftime('%d.%m.%Y'),
                'published': 'published' in request.form,
                'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M')
            }
            news_list.append(item)
            save_json(NEWS_FILE, news_list)
            flash('Новость добавлена.', 'success')
            return redirect(url_for('admin_news'))
        flash('Заполните все поля.', 'error')
    return render_template('admin/news_form.html', item=None)

@app.route('/admin/news/<int:news_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit_news(news_id):
    news_list = load_json(NEWS_FILE)
    item      = next((n for n in news_list if n['id'] == news_id), None)
    if not item:
        return redirect(url_for('admin_news'))
    if request.method == 'POST':
        item['title']     = request.form.get('title', '').strip()
        item['text']      = request.form.get('text', '').strip()
        item['preview']   = item['text'][:120] + '...' if len(item['text']) > 120 else item['text']
        item['published'] = 'published' in request.form
        save_json(NEWS_FILE, news_list)
        flash('Новость обновлена.', 'success')
        return redirect(url_for('admin_news'))
    return render_template('admin/news_form.html', item=item)

@app.route('/admin/news/<int:news_id>/delete', methods=['POST'])
@admin_required
def admin_delete_news(news_id):
    news_list = [n for n in load_json(NEWS_FILE) if n['id'] != news_id]
    save_json(NEWS_FILE, news_list)
    flash('Новость удалена.', 'success')
    return redirect(url_for('admin_news'))

# --- ЗАДАНИЯ ---
@app.route('/admin/tasks')
@admin_required
def admin_tasks():
    tasks_list = sorted(load_json(TASKS_FILE),
                        key=lambda x: x.get('id', 0), reverse=True)
    return render_template('admin/tasks.html', tasks_list=tasks_list)

@app.route('/admin/tasks/add', methods=['GET', 'POST'])
@admin_required
def admin_add_task():
    if request.method == 'POST':
        tasks_list = load_json(TASKS_FILE)
        title      = request.form.get('title', '').strip()
        tour       = request.form.get('tour', '').strip()
        year       = request.form.get('year', '').strip()
        task_type  = request.form.get('task_type', 'task')
        file       = request.files.get('file')

        if not title or not tour or not year:
            flash('Заполните все обязательные поля.', 'error')
            return render_template('admin/task_form.html')

        filepath, filename = '', ''
        if file and file.filename:
            filename = f"{int(datetime.now().timestamp())}_{file.filename}"
            filepath = os.path.join(TASKS_DIR, filename)
            file.save(filepath)

        task = {
            'id':        int(datetime.now().timestamp() * 1000),
            'title':     title, 'tour': tour, 'year': year,
            'task_type': task_type, 'filename': filename, 'filepath': filepath,
            'published': 'published' in request.form,
            'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M')
        }
        tasks_list.append(task)
        save_json(TASKS_FILE, tasks_list)
        flash('Задание загружено.', 'success')
        return redirect(url_for('admin_tasks'))
    return render_template('admin/task_form.html')

@app.route('/admin/tasks/<int:task_id>/delete', methods=['POST'])
@admin_required
def admin_delete_task(task_id):
    tasks_list = load_json(TASKS_FILE)
    task       = next((t for t in tasks_list if t['id'] == task_id), None)
    if task and os.path.exists(task.get('filepath', '')):
        os.remove(task['filepath'])
    save_json(TASKS_FILE, [t for t in tasks_list if t['id'] != task_id])
    flash('Задание удалено.', 'success')
    return redirect(url_for('admin_tasks'))

@app.route('/admin/tasks/<int:task_id>/toggle', methods=['POST'])
@admin_required
def admin_toggle_task(task_id):
    tasks_list = load_json(TASKS_FILE)
    for t in tasks_list:
        if t['id'] == task_id:
            t['published'] = not t.get('published', False)
            break
    save_json(TASKS_FILE, tasks_list)
    return redirect(url_for('admin_tasks'))

# --- АДМИНИСТРАТОРЫ ---
@app.route('/admin/admins')
@admin_required
def admin_admins():
    if not session.get('admin_super'):
        flash('Только суперадминистратор может управлять администраторами.', 'error')
        return redirect(url_for('admin_dashboard'))
    admins = load_json(ADMINS_FILE)
    return render_template('admin/admins.html', admins=admins)

@app.route('/admin/admins/add', methods=['GET', 'POST'])
@admin_required
def admin_add_admin():
    if not session.get('admin_super'):
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        login_val = request.form.get('login', '').strip()
        password  = request.form.get('password', '')
        name      = request.form.get('name', '').strip()
        admins    = load_json(ADMINS_FILE)

        if any(a['login'] == login_val for a in admins):
            flash('Логин уже занят.', 'error')
            return render_template('admin/admin_form.html')
        if not login_val or not password or not name:
            flash('Заполните все поля.', 'error')
            return render_template('admin/admin_form.html')

        new_admin = {
            'id':       int(datetime.now().timestamp() * 1000),
            'login':    login_val,
            'password': hash_password(password),
            'name':     name,
            'super':    False
        }
        admins.append(new_admin)
        save_json(ADMINS_FILE, admins)
        flash(f'Администратор {name} добавлен.', 'success')
        return redirect(url_for('admin_admins'))
    return render_template('admin/admin_form.html')

@app.route('/admin/admins/<int:admin_id>/delete', methods=['POST'])
@admin_required
def admin_delete_admin(admin_id):
    if not session.get('admin_super'):
        return redirect(url_for('admin_dashboard'))
    if admin_id == session.get('admin_id'):
        flash('Нельзя удалить себя.', 'error')
        return redirect(url_for('admin_admins'))
    admins = [a for a in load_json(ADMINS_FILE) if a['id'] != admin_id]
    save_json(ADMINS_FILE, admins)
    flash('Администратор удалён.', 'success')
    return redirect(url_for('admin_admins'))

if __name__ == '__main__':
    app.run(debug=True)