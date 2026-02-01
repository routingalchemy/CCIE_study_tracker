import os
import calendar
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
from werkzeug.utils import secure_filename
from config import Config


app = Flask(__name__)
app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = f'{Config.DATABASE_URL}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = f'{Config.DATABASE_TRACK_MODIFICATIONS}'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
db = SQLAlchemy(app)

class StudyItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text)
    hours_spent = db.Column(db.Float, default=0.0)
    progress = db.Column(db.Integer, default=0)
    theory_confidence = db.Column(db.Integer, default=0)
    practical_confidence = db.Column(db.Integer, default=0)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    operation_type = db.Column(db.String(20), default='add')  # 'add', 'modify', 'delete'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<StudyItem {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'notes': self.notes,
            'hours_spent': self.hours_spent,
            'progress': self.progress,
            'theory_confidence': self.theory_confidence,
            'practical_confidence': self.practical_confidence,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'operation_type': self.operation_type
        }

class KeyDate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<KeyDate {self.name} - {self.date}>'

    def days_remaining(self):
        today = datetime.utcnow().date()
        delta = (self.date - today).days
        return delta

    def is_past(self):
        return self.days_remaining() < 0

    def is_today(self):
        return self.days_remaining() == 0

with app.app_context():
    inspector = db.inspect(db.engine)
    if not inspector.has_table('study_item'):
        db.create_all()

def login_required(f):
    def wrapper(*args, **kwargs):
        if Config.ENABLE_PASSWORD_PROTECTION and 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper

@app.route('/')
@login_required
def index():
    sort_by = request.args.get('sort', 'last_modified')
    sort_order = request.args.get('order', 'desc')
    search_query = request.args.get('search', '').strip()

    valid_sorts = ['title', 'hours_spent', 'progress', 'theory_confidence', 'practical_confidence', 'last_modified']
    if sort_by not in valid_sorts:
        sort_by = 'last_modified'
    query = StudyItem.query
    if search_query:
        query = query.filter(StudyItem.title.ilike(f'%{search_query}%'))
    if sort_order == 'asc':
        if sort_by == 'title':
            query = query.order_by(StudyItem.title.asc())
        elif sort_by == 'hours_spent':
            query = query.order_by(StudyItem.hours_spent.asc())
        elif sort_by == 'progress':
            query = query.order_by(StudyItem.progress.asc())
        elif sort_by == 'theory_confidence':
            query = query.order_by(StudyItem.theory_confidence.asc())
        elif sort_by == 'practical_confidence':
            query = query.order_by(StudyItem.practical_confidence.asc())
        elif sort_by == 'last_modified':
            query = query.order_by(StudyItem.last_modified.asc())
    else:
        if sort_by == 'title':
            query = query.order_by(StudyItem.title.desc())
        elif sort_by == 'hours_spent':
            query = query.order_by(StudyItem.hours_spent.desc())
        elif sort_by == 'progress':
            query = query.order_by(StudyItem.progress.desc())
        elif sort_by == 'theory_confidence':
            query = query.order_by(StudyItem.theory_confidence.desc())
        elif sort_by == 'practical_confidence':
            query = query.order_by(StudyItem.practical_confidence.desc())
        elif sort_by == 'last_modified':
            query = query.order_by(StudyItem.last_modified.desc())

    items = query.all()
    total_items = len(items)
    total_hours = sum(item.hours_spent for item in items)
    avg_progress = sum(item.progress for item in items) / total_items if total_items > 0 else 0
    today = datetime.utcnow().date()
    upcoming_dates = KeyDate.query.filter(
        KeyDate.date >= today
    ).order_by(KeyDate.date.asc()).limit(5).all()

    return render_template('index.html',
                         items=items,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         total_items=total_items,
                         total_hours=round(total_hours, 2),
                         avg_progress=round(avg_progress, 1),
                         password_enabled=Config.ENABLE_PASSWORD_PROTECTION,
                         search_query=search_query,
                         upcoming_key_dates=upcoming_dates)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if not Config.ENABLE_PASSWORD_PROTECTION:
        session['logged_in'] = True
        return redirect(url_for('index'))

    if request.method == 'POST':
        password = request.form.get('password')
        if password == Config.PASSWORD:
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            flash('Invalid password', 'error')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        title = request.form.get('title')
        notes = request.form.get('notes')
        hours_spent = float(request.form.get('hours_spent', 0))
        progress = int(request.form.get('progress', 0))
        theory_confidence = int(request.form.get('theory_confidence', 0))
        practical_confidence = int(request.form.get('practical_confidence', 0))

        if not title:
            flash('Title is required', 'error')
            return redirect(url_for('add_item'))

        new_item = StudyItem(
            title=title,
            notes=notes,
            hours_spent=hours_spent,
            progress=min(max(progress, 0), 100),
            theory_confidence=min(max(theory_confidence, 0), 5),
            practical_confidence=min(max(practical_confidence, 0), 5),
            operation_type='add'
        )

        db.session.add(new_item)
        db.session.commit()

        flash('Item added successfully', 'success')
        return redirect(url_for('index'))

    return render_template('add_edit.html', item=None, action='Add')

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = StudyItem.query.get_or_404(item_id)

    if request.method == 'POST':
        item.title = request.form.get('title')
        item.notes = request.form.get('notes')
        item.hours_spent = float(request.form.get('hours_spent', 0))
        item.progress = int(request.form.get('progress', 0))
        item.theory_confidence = int(request.form.get('theory_confidence', 0))
        item.practical_confidence = int(request.form.get('practical_confidence', 0))
        item.last_modified = datetime.utcnow()

        if not item.title:
            flash('Title is required', 'error')
            return redirect(url_for('edit_item', item_id=item_id))

        item.theory_confidence = min(max(item.theory_confidence, 0), 5)
        item.practical_confidence = min(max(item.practical_confidence, 0), 5)
        item.operation_type = 'modify'

        db.session.commit()

        flash('Item updated successfully', 'success')
        return redirect(url_for('index'))

    return render_template('add_edit.html', item=item, action='Edit')

@app.route('/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = StudyItem.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()

    flash('Item deleted successfully', 'success')
    return redirect(url_for('index'))

@app.route('/bulk_delete', methods=['POST'])
@login_required
def bulk_delete():
    action = request.form.get('action')
    search_query = request.form.get('search', '')
    sort_by = request.form.get('sort', 'last_modified')
    sort_order = request.form.get('order', 'desc')

    if action == 'all':
        query = StudyItem.query
        if search_query:
            query = query.filter(StudyItem.title.ilike(f'%{search_query}%'))
        deleted_count = query.delete()
        db.session.commit()
        flash(f'All {deleted_count} items deleted successfully', 'success')

    elif action == 'selected':
        item_ids = request.form.getlist('item_ids')
        if item_ids:
            deleted_count = StudyItem.query.filter(StudyItem.id.in_(item_ids)).delete()
            db.session.commit()
            flash(f'{deleted_count} selected items deleted successfully', 'success')
        else:
            flash('No items selected', 'error')
    return redirect(url_for('delete_items', search=search_query, sort=sort_by, order=sort_order))

@app.route('/delete')
@login_required
def delete_items():
    sort_by = request.args.get('sort', 'last_modified')
    sort_order = request.args.get('order', 'desc')
    search_query = request.args.get('search', '').strip()
    valid_sorts = ['title', 'hours_spent', 'progress', 'theory_confidence', 'practical_confidence', 'last_modified']
    if sort_by not in valid_sorts:
        sort_by = 'last_modified'
    query = StudyItem.query
    if search_query:
        query = query.filter(StudyItem.title.ilike(f'%{search_query}%'))
    if sort_order == 'asc':
        if sort_by == 'title':
            query = query.order_by(StudyItem.title.asc())
        elif sort_by == 'hours_spent':
            query = query.order_by(StudyItem.hours_spent.asc())
        elif sort_by == 'progress':
            query = query.order_by(StudyItem.progress.asc())
        elif sort_by == 'theory_confidence':
            query = query.order_by(StudyItem.theory_confidence.asc())
        elif sort_by == 'practical_confidence':
            query = query.order_by(StudyItem.practical_confidence.asc())
        elif sort_by == 'last_modified':
            query = query.order_by(StudyItem.last_modified.asc())
    else:
        if sort_by == 'title':
            query = query.order_by(StudyItem.title.desc())
        elif sort_by == 'hours_spent':
            query = query.order_by(StudyItem.hours_spent.desc())
        elif sort_by == 'progress':
            query = query.order_by(StudyItem.progress.desc())
        elif sort_by == 'theory_confidence':
            query = query.order_by(StudyItem.theory_confidence.desc())
        elif sort_by == 'practical_confidence':
            query = query.order_by(StudyItem.practical_confidence.desc())
        elif sort_by == 'last_modified':
            query = query.order_by(StudyItem.last_modified.desc())

    items = query.all()

    return render_template('delete.html',
                         items=items,
                         sort_by=sort_by,
                         sort_order=sort_order,
                         search_query=search_query)

@app.route('/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    current_theme = session.get('theme', Config.DEFAULT_THEME)
    new_theme = 'dark' if current_theme == 'light' else 'light'
    session['theme'] = new_theme
    session.modified = True  
    return jsonify({'theme': new_theme})

@app.route('/bulk_import', methods=['GET', 'POST'])
@login_required
def bulk_import():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)

        if not file.filename.endswith(('.xlsx', '.xls')):
            flash('Please upload an Excel file (.xlsx or .xls)', 'error')
            return redirect(request.url)

        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            file.save(filepath)
            df = pd.read_excel(filepath)
            title_cols = request.form.getlist('title_columns')
            notes_cols = request.form.getlist('notes_columns')
            hours_col = request.form.get('hours_column')
            progress_col = request.form.get('progress_column')
            theory_col = request.form.get('theory_column')
            practical_col = request.form.get('practical_column')
            sheet_name = request.form.get('sheet_name')
            data_start_row = int(request.form.get('data_start_row', 2)) - 1
            if sheet_name:
                df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
            else:
                df = pd.read_excel(filepath, header=None)
            if data_start_row > 0:
                df = df.iloc[data_start_row:].reset_index(drop=True)
            def col_letter_to_index(col_letter):
                if not col_letter:
                    return None
                index = 0
                for char in col_letter.upper():
                    index = index * 26 + (ord(char) - ord('A') + 1)
                return index - 1

            title_indices = [col_letter_to_index(col) for col in title_cols if col]
            notes_indices = [col_letter_to_index(col) for col in notes_cols if col]
            hours_index = col_letter_to_index(hours_col)
            progress_index = col_letter_to_index(progress_col)
            theory_index = col_letter_to_index(theory_col)
            practical_index = col_letter_to_index(practical_col)

            imported_count = 0

            for _, row in df.iterrows():
                title_parts = []
                for idx in title_indices:
                    if idx is not None and idx < len(row) and pd.notna(row.iloc[idx]):
                        title_parts.append(str(row.iloc[idx]))
                title = ' '.join(title_parts) if title_parts else ''
                if not title.strip():
                    continue
                notes_parts = []
                for idx in notes_indices:
                    if idx is not None and idx < len(row) and pd.notna(row.iloc[idx]):
                        notes_parts.append(str(row.iloc[idx]))
                notes = '\n'.join(notes_parts) if notes_parts else None
                hours_spent = 0.0
                if hours_index is not None and hours_index < len(row) and pd.notna(row.iloc[hours_index]):
                    try:
                        hours_spent = float(row.iloc[hours_index])
                    except (ValueError, TypeError):
                        hours_spent = 0.0

                progress = 0
                if progress_index is not None and progress_index < len(row) and pd.notna(row.iloc[progress_index]):
                    try:
                        progress = int(float(row.iloc[progress_index]))
                        progress = min(max(progress, 0), 100)
                    except (ValueError, TypeError):
                        progress = 0

                theory_confidence = 0
                if theory_index is not None and theory_index < len(row) and pd.notna(row.iloc[theory_index]):
                    try:
                        theory_confidence = int(float(row.iloc[theory_index]))
                        theory_confidence = min(max(theory_confidence, 0), 5)
                    except (ValueError, TypeError):
                        theory_confidence = 0

                practical_confidence = 0
                if practical_index is not None and practical_index < len(row) and pd.notna(row.iloc[practical_index]):
                    try:
                        practical_confidence = int(float(row.iloc[practical_index]))
                        practical_confidence = min(max(practical_confidence, 0), 5)
                    except (ValueError, TypeError):
                        practical_confidence = 0
                new_item = StudyItem(
                    title=title,
                    notes=notes,
                    hours_spent=hours_spent,
                    progress=progress,
                    theory_confidence=theory_confidence,
                    practical_confidence=practical_confidence
                )

                db.session.add(new_item)
                imported_count += 1

            db.session.commit()

            os.remove(filepath)

            flash(f'Successfully imported {imported_count} items', 'success')
            return redirect(url_for('index'))

        except Exception as e:
            flash(f'Error importing file: {str(e)}', 'error')
            return redirect(request.url)

    return render_template('bulk_import.html')

@app.route('/calendar')
@login_required
def calendar_view():
    year = request.args.get('year', datetime.utcnow().year, type=int)
    month = request.args.get('month', datetime.utcnow().month, type=int)
    key_dates = KeyDate.query.all()
    start_date = datetime(year, month, 1).date()
    if month == 12:
        end_date = datetime(year + 1, 1, 1).date() - timedelta(days=1)
    else:
        end_date = datetime(year, month + 1, 1).date() - timedelta(days=1)
    start_dt = datetime.combine(start_date, datetime.min.time())
    end_dt = datetime.combine(end_date, datetime.max.time())
    updates = db.session.query(StudyItem.id, StudyItem.title, StudyItem.last_modified, StudyItem.operation_type).filter(
        StudyItem.last_modified.between(start_dt, end_dt)
    ).all()

    update_dates = {}
    for update in updates:
        if update[2]:
            date_key = update[2].date()
            if date_key not in update_dates:
                update_dates[date_key] = True

    key_dates_map = {}
    for key_date in key_dates:
        key_dates_map[key_date.date] = key_date
    cal = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    if month == 1:
        prev_month, prev_year = 12, year - 1
    else:
        prev_month, prev_year = month - 1, year

    if month == 12:
        next_month, next_year = 1, year + 1
    else:
        next_month, next_year = month + 1, year

    calendar_data = []
    for week in cal:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append({'day': None, 'updates': [], 'key_date': None})
            else:
                day_date = datetime(year, month, day).date()
                has_updates = day_date in update_dates
                key_date = key_dates_map.get(day_date)
                week_data.append({
                    'day': day,
                    'date': day_date,
                    'has_updates': has_updates,
                    'key_date': key_date
                })
        calendar_data.append(week_data)

    return render_template('calendar.html',
                         year=year,
                         month=month,
                         month_name=datetime(year, month, 1).strftime('%B'),
                         calendar=calendar_data,
                         key_dates=key_dates,
                         prev_month=prev_month,
                         prev_year=prev_year,
                         next_month=next_month,
                         next_year=next_year)

@app.route('/calendar/day/<date_str>')
@login_required
def calendar_day_view(date_str):
    try:
        day_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        flash('Invalid date format', 'error')
        return redirect(url_for('calendar_view'))
    start_datetime = datetime.combine(day_date, datetime.min.time())
    end_datetime = datetime.combine(day_date, datetime.max.time())
    updates = db.session.query(StudyItem).filter(
        StudyItem.last_modified.between(start_datetime, end_datetime)
    ).order_by(StudyItem.last_modified.desc()).all()
    key_date = KeyDate.query.filter_by(date=day_date).first()

    return render_template('calendar_day.html',
                         date=day_date,
                         updates=updates,
                         key_date=key_date)

@app.route('/key_date/add', methods=['GET', 'POST'])
@login_required
def add_key_date():
    if request.method == 'POST':
        name = request.form.get('name')
        date_str = request.form.get('date')
        notes = request.form.get('notes')

        if not name or not date_str:
            flash('Name and date are required', 'error')
            return redirect(url_for('add_key_date'))

        try:
            if 'T' not in date_str and '.' in date_str:
                key_date_obj = datetime.strptime(date_str, '%Y.%m.%d').date()
            else:
                key_date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            key_date = KeyDate(
                name=name,
                date=key_date_obj,
                notes=notes
            )
            db.session.add(key_date)
            db.session.commit()
            flash('Key date added successfully', 'success')
            return redirect(url_for('calendar_view'))
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('add_key_date'))

    return render_template('add_key_date.html')

@app.route('/key_date/edit/<int:date_id>', methods=['GET', 'POST'])
@login_required
def edit_key_date(date_id):
    key_date = KeyDate.query.get_or_404(date_id)

    if request.method == 'POST':
        key_date.name = request.form.get('name')
        date_str = request.form.get('date')
        key_date.notes = request.form.get('notes')

        if not key_date.name or not date_str:
            flash('Name and date are required', 'error')
            return redirect(url_for('edit_key_date', date_id=date_id))

        try:
            if 'T' not in date_str and '.' in date_str:
                key_date.date = datetime.strptime(date_str, '%Y.%m.%d').date()
            else:
                key_date.date = datetime.strptime(date_str, '%Y-%m-%d').date()
            db.session.commit()
            flash('Key date updated successfully', 'success')
            return redirect(url_for('calendar_view'))
        except ValueError:
            flash('Invalid date format', 'error')
            return redirect(url_for('edit_key_date', date_id=date_id))

    return render_template('edit_key_date.html', key_date=key_date)

@app.route('/key_date/delete/<int:date_id>', methods=['POST'])
@login_required
def delete_key_date(date_id):
    key_date = KeyDate.query.get_or_404(date_id)
    db.session.delete(key_date)
    db.session.commit()
    flash('Key date deleted successfully', 'success')
    return redirect(url_for('calendar_view'))

if __name__ == '__main__':
    app.run(debug=Config.DEBUG)
