from flask import Flask, jsonify, request, render_template, send_from_directory, send_file
import db
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
import re
import uuid
from email.utils import parseaddr
import csv
import io
import os
import smtplib
from email.message import EmailMessage
import sys

SOURCE_DIR = Path(__file__).resolve().parent


def find_asset_dir(name: str) -> Path:
    local_path = SOURCE_DIR / name
    if local_path.exists():
        return local_path
    installed_path = Path(sys.prefix) / 'share' / 'study-dash' / name
    return installed_path


LIBRARY_DIR = Path.cwd() / 'thelibrary'
PROFILE_DIR = Path.cwd() / 'profile'
TEMPLATE_DIR = find_asset_dir('templates')
STATIC_DIR = find_asset_dir('static')
ALLOWED_LIBRARY_EXTENSIONS = {'.pdf', '.txt', '.md', '.png', '.jpg', '.jpeg', '.webp'}
ALLOWED_SCHEDULE_EXTENSIONS = {'.csv', '.tsv', '.xlsx'}

app = Flask(__name__, static_folder=str(STATIC_DIR), template_folder=str(TEMPLATE_DIR))
_last_reminder_check = None


@app.before_request
def check_due_reminders():
    global _last_reminder_check
    today = datetime.now().date().isoformat()
    if _last_reminder_check == today:
        return
    if os.environ.get('STUDY_DASH_GMAIL_ADDRESS') and os.environ.get('STUDY_DASH_GMAIL_APP_PASSWORD') and db.get_profile().get('email'):
        _last_reminder_check = today
        try:
            send_due_reminders()
        except Exception:
            pass


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/history')
def history_page():
    return render_template('history.html')


@app.route('/goals')
def goals_page():
    return render_template('goals.html')


@app.route('/library')
def library_page():
    return render_template('library.html')


@app.route('/profile')
def profile_page():
    return render_template('profile.html')


def profile_payload():
    profile = db.get_profile()
    profile['avatar_url'] = f"/api/profile/avatar?v={profile['avatar_name']}" if profile.get('avatar_name') else None
    return profile


@app.route('/api/profile', methods=['GET', 'POST'])
def api_profile():
    if request.method == 'GET':
        return jsonify(profile_payload())
    name = (request.form.get('name') or '').strip()
    email = (request.form.get('email') or '').strip()
    if not name:
        return jsonify({'error': 'Please enter your name.'}), 400
    if parseaddr(email)[1] != email or '@' not in email:
        return jsonify({'error': 'Please enter a valid email address.'}), 400
    avatar = request.files.get('avatar')
    avatar_name = None
    if avatar and avatar.filename:
        extension = Path(secure_filename(avatar.filename)).suffix.lower()
        if extension not in {'.png', '.jpg', '.jpeg', '.webp'}:
            return jsonify({'error': 'Profile pictures must be PNG, JPG, JPEG, or WEBP.'}), 400
        PROFILE_DIR.mkdir(exist_ok=True)
        avatar_name = f'avatar{extension}'
        avatar.save(PROFILE_DIR / avatar_name)
    db.update_profile(name, email, avatar_name)
    return jsonify(profile_payload())


@app.route('/api/profile/avatar')
def profile_avatar():
    profile = db.get_profile()
    if not profile.get('avatar_name'):
        return jsonify({'error': 'No profile picture'}), 404
    return send_file(PROFILE_DIR / profile['avatar_name'])


def extract_paper_text(path: Path) -> str:
    if path.suffix.lower() == '.pdf':
        from pypdf import PdfReader
        return '\n'.join(page.extract_text() or '' for page in PdfReader(str(path)).pages).strip()
    if path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp'}:
        try:
            from PIL import Image, ImageOps
            import pytesseract
            image = ImageOps.exif_transpose(Image.open(path))
            return pytesseract.image_to_string(image).strip()
        except Exception as error:
            raise RuntimeError('Image OCR needs Tesseract installed on this computer.') from error
    return path.read_text(encoding='utf-8', errors='replace').strip()


def estimate_difficulty(text: str, question_count: int) -> str:
    if not text or question_count < 3:
        return 'Not enough data'
    long_questions = len(re.findall(r'(?is)(?:question|q\.?\s*\d+)[^\n]{140,}', text))
    reasoning_terms = len(re.findall(r'\b(?:which|reason|infer|minimum|maximum|approximate|assertion|statement|correct|incorrect)\b', text, re.I))
    score = (long_questions * 2) + reasoning_terms / max(question_count, 1)
    if score >= question_count * 0.8:
        return 'Hard'
    if score >= question_count * 0.35:
        return 'Moderate'
    return 'Easy'


def count_questions(text: str) -> int:
    markers = re.findall(r'(?<!\d)(?:Q(?:uestion)?\s*)?(\d{1,3})\s*[.)](?=\s|$)', text, re.I)
    numbers = {int(number) for number in markers if 1 <= int(number) <= 200}
    if numbers:
        sequence = 0
        while sequence + 1 in numbers:
            sequence += 1
        if sequence >= 3:
            return sequence
        return len(numbers)
    return len(re.findall(r'(?i)\bquestion\b', text))


def parse_user_date(value: str):
    for date_format in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(value, date_format).strftime('%Y-%m-%d')
        except (TypeError, ValueError):
            continue
    return None


def parse_schedule_date(value):
    if value is None:
        return None
    if hasattr(value, 'strftime'):
        return value.strftime('%Y-%m-%d')
    text = str(value).strip()
    for date_format in ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y'):
        try:
            return datetime.strptime(text, date_format).strftime('%Y-%m-%d')
        except ValueError:
            continue
    return None


def normalize_schedule_row(row):
    normalized = {str(key).strip().lower().replace(' ', '_'): value for key, value in row.items() if key is not None}
    date_value = normalized.get('date') or normalized.get('exam_date') or normalized.get('test_date')
    title = normalized.get('test') or normalized.get('exam') or normalized.get('title') or normalized.get('test_name')
    portions = normalized.get('portions') or normalized.get('topics') or normalized.get('syllabus') or ''
    exam_time = normalized.get('time') or normalized.get('exam_time') or None
    date = parse_schedule_date(date_value)
    if not date or not str(title or '').strip():
        return None
    return {'title': str(title).strip(), 'exam_date': date, 'exam_time': str(exam_time).strip() if exam_time else None, 'portions': str(portions).strip()}


def send_due_reminders():
    profile = db.get_profile()
    sender = os.environ.get('STUDY_DASH_GMAIL_ADDRESS', '').strip()
    app_password = os.environ.get('STUDY_DASH_GMAIL_APP_PASSWORD', '').strip()
    recipient = profile.get('email', '').strip()
    if not sender or not app_password or not recipient:
        return {'sent': 0, 'skipped': 0, 'error': 'Gmail address, Gmail app password, and profile email are required.'}
    today = datetime.now().date()
    due = [event for event in db.get_exam_events() if not event['reminder_sent_at'] and (datetime.strptime(event['exam_date'], '%Y-%m-%d').date() - today).days == 1]
    if not due:
        return {'sent': 0, 'skipped': 0, 'message': 'No reminders are due today.'}
    sent = 0
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender, app_password)
            for event in due:
                message = EmailMessage()
                message['Subject'] = f"Reminder: {event['title']} is tomorrow"
                message['From'] = sender
                message['To'] = recipient
                when = event['exam_date']
                if event['exam_time']:
                    when += f" at {event['exam_time']}"
                portions = event['portions'] or 'No portions were provided.'
                message.set_content(f"Hello {profile.get('name') or 'there'},\n\nThis is a reminder that {event['title']} is tomorrow ({when}).\n\nPortions:\n{portions}\n\nGood luck with your preparation!")
                smtp.send_message(message)
                db.mark_exam_reminded(event['id'], datetime.now().isoformat(timespec='seconds'))
                sent += 1
    except Exception as error:
        return {'sent': sent, 'skipped': len(due) - sent, 'error': f'Gmail sending failed: {error}'}
    return {'sent': sent, 'skipped': 0}


@app.route('/api/library', methods=['GET', 'POST'])
def api_library():
    if request.method == 'GET':
        return jsonify(db.get_library_papers())
    upload = request.files.get('paper')
    if not upload or not upload.filename:
        return jsonify({'error': 'Choose a PDF, image, TXT, or Markdown paper first.'}), 400
    original_name = secure_filename(upload.filename)
    extension = Path(original_name).suffix.lower()
    if extension not in ALLOWED_LIBRARY_EXTENSIONS:
        return jsonify({'error': 'Only PDF, PNG, JPG, JPEG, WEBP, TXT, and Markdown files are supported.'}), 400
    LIBRARY_DIR.mkdir(exist_ok=True)
    stored_name = f'{uuid.uuid4().hex}{extension}'
    path = LIBRARY_DIR / stored_name
    upload.save(path)
    try:
        text = extract_paper_text(path)
    except Exception as error:
        path.unlink(missing_ok=True)
        return jsonify({'error': f'Could not read this file: {error}'}), 400
    if not text:
        path.unlink(missing_ok=True)
        return jsonify({'error': 'No readable text was found in this file.'}), 400
    questions = count_questions(text)
    paper_id = db.add_library_paper(original_name, stored_name, extension[1:], text, questions,
                                    estimate_difficulty(text, questions), datetime.now().isoformat(timespec='seconds'))
    return jsonify({'id': paper_id}), 201


@app.route('/api/library/<int:paper_id>', methods=['GET', 'DELETE'])
def api_library_paper(paper_id):
    paper = db.get_library_paper(paper_id)
    if not paper:
        return jsonify({'error': 'Paper not found'}), 404
    if request.method == 'DELETE':
        (LIBRARY_DIR / paper['stored_name']).unlink(missing_ok=True)
        db.delete_library_paper(paper_id)
        return jsonify({'deleted': paper_id})
    return jsonify({key: paper[key] for key in ('id', 'original_name', 'file_type', 'extracted_text', 'question_count', 'difficulty', 'uploaded_at')})


@app.route('/api/library/<int:paper_id>/file')
def library_file(paper_id):
    paper = db.get_library_paper(paper_id)
    if not paper:
        return jsonify({'error': 'Paper not found'}), 404
    return send_file(LIBRARY_DIR / paper['stored_name'], as_attachment=True, download_name=paper['original_name'])


@app.route('/api/library/ask', methods=['POST'])
def ask_library():
    data = request.get_json() or {}
    query = (data.get('question') or '').strip()
    if not query:
        return jsonify({'error': 'Type the question or doubt you want to find.'}), 400
    terms = [term.lower() for term in re.findall(r'[a-zA-Z0-9]{3,}', query)]
    matches = []
    for paper in db.get_library_papers():
        full = db.get_library_paper(paper['id'])
        text = full['extracted_text']
        paragraphs = [part.strip() for part in re.split(r'\n\s*\n|(?<=\.)\s{2,}', text) if part.strip()]
        ranked = sorted(((sum(term in part.lower() for term in terms), part) for part in paragraphs), reverse=True)
        for score, excerpt in ranked[:2]:
            if score:
                matches.append({'paper': paper['original_name'], 'excerpt': excerpt[:700], 'score': score})
    matches.sort(key=lambda item: item['score'], reverse=True)
    return jsonify({'answer': 'Here are the closest passages from your saved papers. Use them to verify the doubt; an answer key or AI solver is needed for a guaranteed solution.', 'matches': matches[:5]})


@app.route('/api/schedule', methods=['GET', 'POST'])
def api_schedule():
    if request.method == 'GET':
        return jsonify(db.get_exam_events())
    data = request.get_json() or {}
    title = (data.get('title') or '').strip()
    exam_date = parse_schedule_date(data.get('exam_date'))
    if not title or not exam_date:
        return jsonify({'error': 'Add a test name and a valid date in DD/MM/YYYY format.'}), 400
    event_id = db.add_exam_event(title, exam_date, (data.get('exam_time') or '').strip() or None, (data.get('portions') or '').strip())
    return jsonify({'id': event_id}), 201


@app.route('/api/schedule/import', methods=['POST'])
def import_schedule():
    upload = request.files.get('schedule')
    if not upload or not upload.filename:
        return jsonify({'error': 'Choose a CSV, TSV, or Excel sheet first.'}), 400
    extension = Path(secure_filename(upload.filename)).suffix.lower()
    if extension not in ALLOWED_SCHEDULE_EXTENSIONS:
        return jsonify({'error': 'Only CSV, TSV, and XLSX sheets are supported.'}), 400
    try:
        if extension == '.xlsx':
            from openpyxl import load_workbook
            workbook = load_workbook(upload, read_only=True, data_only=True)
            sheet = workbook.active
            rows = list(sheet.values)
            headers = rows[0] if rows else []
            records = [dict(zip(headers, row)) for row in rows[1:]]
        else:
            content = upload.read().decode('utf-8-sig')
            delimiter = '\t' if extension == '.tsv' else None
            records = list(csv.DictReader(io.StringIO(content), delimiter=delimiter or ','))
        events = [normalize_schedule_row(row) for row in records]
        events = [event for event in events if event]
        if not events:
            return jsonify({'error': 'No rows with a date and test name were found.'}), 400
        for event in events:
            db.add_exam_event(**event)
        return jsonify({'imported': len(events)}), 201
    except Exception as error:
        return jsonify({'error': f'Could not read this sheet: {error}'}), 400


@app.route('/api/schedule/<int:event_id>', methods=['DELETE'])
def delete_schedule_event(event_id):
    if not db.get_exam_event(event_id):
        return jsonify({'error': 'Schedule entry not found'}), 404
    db.delete_exam_event(event_id)
    return jsonify({'deleted': event_id})


@app.route('/api/schedule/send-reminders', methods=['POST'])
def api_send_reminders():
    result = send_due_reminders()
    return jsonify(result), 200 if not result.get('error') else 503


@app.route('/api/tests', methods=['GET', 'POST'])
def api_tests():
    if request.method == 'GET':
        tests = db.get_tests(order_desc=False)
        return jsonify(tests)
    data = request.get_json() or {}
    # validate
    date = parse_user_date(data.get('date'))
    name = data.get('test_name')
    if not date:
        return jsonify({'error': 'Invalid date'}), 400
    if not name:
        return jsonify({'error': 'Test name required'}), 400
    try:
        p = int(data.get('physics', 0))
        c = int(data.get('chemistry', 0))
        m = int(data.get('maths', 0))
    except Exception:
        return jsonify({'error': 'Scores must be integers'}), 400
    for v in (p, c, m):
        if v < 0 or v > 60:
            return jsonify({'error': 'Scores must be 0-60'}), 400
    tid = db.add_test(date, name, p, c, m)
    return jsonify({'id': tid}), 201


@app.route('/api/tests/<int:tid>', methods=['PUT', 'DELETE'])
def api_test_modify(tid):
    if request.method == 'DELETE':
        db.delete_test(tid)
        return jsonify({'deleted': tid})
    data = request.get_json() or {}
    date = parse_user_date(data.get('date'))
    name = data.get('test_name')
    if not date:
        return jsonify({'error': 'Invalid date'}), 400
    try:
        p = int(data.get('physics', 0))
        c = int(data.get('chemistry', 0))
        m = int(data.get('maths', 0))
    except Exception:
        return jsonify({'error': 'Scores must be integers'}), 400
    db.update_test(tid, date, name, p, c, m)
    return jsonify({'updated': tid})


@app.route('/api/goals', methods=['GET', 'POST'])
def api_goals():
    if request.method == 'GET':
        goals = db.get_goals()
        # enhance goals with a computed current score and status
        enhanced = []
        tests_all = db.get_tests(order_desc=False)
        for g in goals:
            eg = dict(g)
            eg['current_score'] = None
            eg['status'] = 'no data'
            # if the goal references a specific test, include that test's total
            if eg.get('test_id'):
                t = db.get_test_by_id(eg['test_id'])
                if t:
                    eg['current_score'] = t.get('total')
                    eg['status'] = 'met' if t.get('total', 0) >= eg.get('target', 0) else 'pending'
                else:
                    eg['status'] = 'missing test'
            # otherwise if start/end provided, compute best total in that window
            elif eg.get('start_date') and eg.get('end_date'):
                try:
                    from datetime import datetime
                    sd = datetime.strptime(eg['start_date'], '%Y-%m-%d')
                    ed = datetime.strptime(eg['end_date'], '%Y-%m-%d')
                    best = None
                    for t in tests_all:
                        try:
                            td = datetime.strptime(t['date'], '%Y-%m-%d')
                        except Exception:
                            continue
                        if sd <= td <= ed:
                            if best is None or t.get('total', 0) > best:
                                best = t.get('total', 0)
                    if best is not None:
                        eg['current_score'] = best
                        eg['status'] = 'met' if best >= eg.get('target', 0) else 'pending'
                    else:
                        eg['status'] = 'no tests in window'
                except Exception:
                    eg['status'] = 'invalid window'
            enhanced.append(eg)
        return jsonify(enhanced)
    data = request.get_json() or {}
    name = data.get('name')
    gtype = data.get('type')
    try:
        target = int(data.get('target'))
    except Exception:
        return jsonify({'error': 'Target must be integer'}), 400
    start = parse_user_date(data.get('start_date')) if data.get('start_date') else None
    end = parse_user_date(data.get('end_date')) if data.get('end_date') else None
    if (data.get('start_date') and not start) or (data.get('end_date') and not end):
        return jsonify({'error': 'Dates must use DD/MM/YYYY'}), 400
    test_id = data.get('test_id')
    gid = db.add_goal(name, gtype, target, start, end, test_id)
    return jsonify({'id': gid}), 201


@app.route('/api/goals/<int:gid>', methods=['PUT', 'DELETE'])
def api_goal_modify(gid):
    if request.method == 'DELETE':
        db.delete_goal(gid)
        return jsonify({'deleted': gid})
    data = request.get_json() or {}
    name = data.get('name')
    gtype = data.get('type')
    try:
        target = int(data.get('target'))
    except Exception:
        return jsonify({'error': 'Target must be integer'}), 400
    start = parse_user_date(data.get('start_date')) if data.get('start_date') else None
    end = parse_user_date(data.get('end_date')) if data.get('end_date') else None
    if (data.get('start_date') and not start) or (data.get('end_date') and not end):
        return jsonify({'error': 'Dates must use DD/MM/YYYY'}), 400
    test_id = data.get('test_id')
    db.update_goal(gid, name, gtype, target, start, end, test_id)
    return jsonify({'updated': gid})


def main():
    db.init_db()
    app.run(host='127.0.0.1', port=5000, debug=True)


if __name__ == '__main__':
    main()
