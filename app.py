from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_, desc
from sqlalchemy import func, desc
import json
import pandas as pd
import io
import os

# برای تاریخ شمسی
from jdatetime import date as jdate

def fa_to_en(s):
    if not s:
        return s
    fa = '۰۱۲۳۴۵۶۷۸۹'
    en = '0123456789'
    table = str.maketrans(fa, en)
    return s.translate(table)

# متراژ استاندارد دستگاه‌ها
STANDARD_FOOTAGE = {
    1: 1100, 2: 800, 3: 800, 4: 800, 5: 800,
    6: 800, 7: 1100, 8: 700, 9: 700, 10: 650,
    11: 1050, 12: 1050, 13: 1050, 14: 1050, 15: 650
}
# تعریف اپ
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///factory_monitoring.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# فیلتر تاریخ شمسی (حالا app تعریف شده، پس کار می‌کنه)
@app.template_filter('jalali_date')
def jalali_date_filter(value, format='%Y/%m/%d'):
    if value is None:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d').date()
        except:
            return value
    if isinstance(value, date):
        jd = jdate.fromgregorian(date=value)
        return jd.strftime(format)
    return str(value)

# بقیه فیلترها (اگر داری)
@app.template_filter('floatformat')
def floatformat_filter(value, precision=1):
    if value is None:
        return ''
    try:
        return round(float(value), precision)
    except (ValueError, TypeError):
        return value

# ادامه کد: db, login_manager, migrate و ...
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
migrate = Migrate(app, db)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100))
    role = db.Column(db.String(20))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Machine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_number = db.Column(db.Integer, nullable=False)
    section = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')
    standard_footage = db.Column(db.Float, default=800)  # ⭐ این خط را اضافه کنید


class CircularReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20), nullable=False)
    machine_number = db.Column(db.Integer, db.ForeignKey('machine.id'))
    operator_name = db.Column(db.String(100), nullable=False)
    bag_width = db.Column(db.Float)
    color = db.Column(db.String(50))
    cleanliness = db.Column(db.String(50))
    machine_speed = db.Column(db.Float)
    footage = db.Column(db.Float)
    roll_weight = db.Column(db.Float)
    downtime_hours = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ExtruderReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20), nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    color_material = db.Column(db.Float, nullable=True)
    carbon_material = db.Column(db.Float, nullable=True)
    brightener_material = db.Column(db.Float, nullable=True)
    material_weight = db.Column(db.Float, nullable=True)
    machine_speed = db.Column(db.Float, nullable=True)
    water_temp = db.Column(db.Float, nullable=True)
    mardon_temp = db.Column(db.Float, nullable=True)
    mold_temp = db.Column(db.Float, nullable=True)
    furnace_temp = db.Column(db.Float, nullable=True)
    denier_measurement_time = db.Column(db.String(10), nullable=True)
    salon_denier = db.Column(db.Float, nullable=True)
    wall_denier = db.Column(db.Float, nullable=True)
    color = db.Column(db.String(50), nullable=True)
    remaining_weight = db.Column(db.Float, nullable=True)
    waste = db.Column(db.Float, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class SewingReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20), nullable=False)
    operator_name = db.Column(db.String(100), nullable=False)
    roll_barcode = db.Column(db.String(100))
    roll_weight = db.Column(db.Float)
    footage = db.Column(db.Float)
    bag_width = db.Column(db.Float)
    bag_length = db.Column(db.Float)
    color = db.Column(db.String(50))
    bags_produced = db.Column(db.Integer)
    grade_b_bags = db.Column(db.Integer)
    unsewn_bags = db.Column(db.Integer)
    bundle_count = db.Column(db.Integer)
    waste = db.Column(db.Float)
    notes = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class MachineIssue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    machine_number = db.Column(db.Integer, db.ForeignKey('machine.id'))
    section = db.Column(db.String(50))
    issue_type = db.Column(db.String(100))
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    shift = db.Column(db.String(20))
    reported_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_now():
    return {'now': datetime.now()}



# Routes
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html', user=current_user)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('نام کاربری یا رمز عبور اشتباه است', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')

        if current_user.check_password(old_password):
            current_user.set_password(new_password)
            db.session.commit()
            flash('رمز عبور با موفقیت تغییر کرد', 'success')
            return redirect(url_for('index'))
        else:
            flash('رمز عبور فعلی اشتباه است', 'error')

    return render_template('change_password.html')


# Report Routes
@app.route('/report/circular', methods=['GET', 'POST'])
@login_required
def circular_report():
    if request.method == 'POST':
        try:
            # تابع کمکی برای تبدیل امن به float (رشته خالی → None یا default)
            def get_float(key, default=None):
                value = request.form.get(key)
                if value is None or value.strip() == '':
                    return default
                try:
                    return float(value)
                except ValueError:
                    return default

            # فیلدهای اجباری را مستقیم بگیرید (فرم اعتبارسنجی سمت کاربر دارد، اما اینجا هم چک می‌کنیم)
            date_str = request.form.get('date')
            if not date_str:
                flash('تاریخ الزامی است.', 'error')
                return redirect(url_for('circular_report'))

            report_date = datetime.strptime(date_str, '%Y-%m-%d').date()

            shift = request.form.get('shift')
            machine_id = request.form.get('machine_number')
            operator = request.form.get('operator_name')
            footage_str = request.form.get('footage')

            if not all([shift, machine_id, operator, footage_str]):
                flash('فیلدهای الزامی را پر کنید.', 'error')
                return redirect(url_for('circular_report'))

            report = CircularReport(
                date=report_date,
                shift=shift,
                machine_number=int(machine_id),
                operator_name=operator,
                bag_width=get_float('bag_width'),                  # اختیاری → None اگر خالی
                color=request.form.get('color') or None,
                cleanliness=request.form.get('cleanliness') or None,
                machine_speed=get_float('machine_speed'),          # اختیاری → None اگر خالی
                footage=float(footage_str),                        # اجباری
                roll_weight=get_float('roll_weight'),              # اختیاری → None اگر خالی
                downtime_hours=get_float('downtime_hours', default=0.0),  # پیش‌فرض 0
                notes=request.form.get('notes'),
                created_by=current_user.id
            )

            db.session.add(report)

            # فقط اگر توضیحات وجود داشت، مسئله ثبت شود
            notes = request.form.get('notes')
            if notes and notes.strip():
                issue = MachineIssue(
                    machine_number=report.machine_number,
                    section='circular',
                    issue_type='گزارش عملیاتی',
                    description=notes.strip(),
                    date=report.date,
                    shift=report.shift,
                    reported_by=current_user.id
                )
                db.session.add(issue)

            db.session.commit()
            flash('گزارش با موفقیت ثبت شد', 'success')

        except ValueError as ve:
            db.session.rollback()
            flash(f'خطا در داده‌های عددی: مقدار معتبر وارد کنید.', 'error')
        except Exception as e:
            db.session.rollback()
            flash(f'خطا در ثبت گزارش: {str(e)}', 'error')

        return redirect(url_for('circular_report'))

    # بخش GET — بدون تغییر (فقط کمی تمیزتر)
    machines = Machine.query.filter_by(section='circular').order_by(Machine.machine_number).all()
    recent_reports = CircularReport.query.order_by(desc(CircularReport.created_at)).limit(10).all()
    return render_template('circular_report.html', machines=machines, recent_reports=recent_reports)


@app.route('/report/extruder', methods=['GET', 'POST'])
@login_required
def extruder_report():
    if request.method == 'POST':
        try:
            date_str = request.form.get('date')
            if not date_str or date_str.strip() == '':
                flash('تاریخ الزامی است.', 'error')
                return redirect(url_for('extruder_report'))

            date_str = fa_to_en(date_str.strip())

            try:
                # اگر شمسی بود (۱۴۰۴-۰۹-۲۲)
                if date_str.startswith('14'):
                    y, m, d = map(int, date_str.split('-'))
                    report_date = jdate(y, m, d).togregorian()
                else:
                    # میلادی
                    report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except Exception as e:
                flash('خطای تاریخ: فرمت صحیح YYYY-MM-DD است', 'error')
                return redirect(url_for('extruder_report'))

            shift = request.form.get('shift')
            operator_name = request.form.get('operator_name')

            if not shift:
                flash('شیفت کاری الزامی است.', 'error')
                return redirect(url_for('extruder_report'))

            if not operator_name:
                flash('نام اپراتور الزامی است.', 'error')
                return redirect(url_for('extruder_report'))

            # تابع‌های کمکی برای اختیاری بودن
            def safe_float(key):
                value = request.form.get(key)
                if not value or value.strip() == '':
                    return None
                try:
                    return float(value)
                except:
                    return None

            def safe_str(key):
                value = request.form.get(key)
                return value.strip() if value else None

            report = ExtruderReport(
                date=report_date,
                shift=shift,
                operator_name=operator_name,
                color_material=safe_float('color_material'),
                carbon_material=safe_float('carbon_material'),
                brightener_material=safe_float('brightener_material'),
                material_weight=safe_float('material_weight'),
                machine_speed=safe_float('machine_speed'),
                water_temp=safe_float('water_temp'),
                mardon_temp=safe_float('mardon_temp'),
                mold_temp=safe_float('mold_temp'),
                furnace_temp=safe_float('furnace_temp'),
                denier_measurement_time=safe_str('denier_measurement_time'),
                salon_denier=safe_float('salon_denier'),
                wall_denier=safe_float('wall_denier'),
                color=safe_str('color'),
                remaining_weight=safe_float('remaining_weight'),
                waste=safe_float('waste'),
                notes=safe_str('notes'),
                created_by=current_user.id
            )

            db.session.add(report)
            db.session.commit()
            flash('گزارش با موفقیت ثبت شد (حتی با فیلدهای خالی)!', 'success')

        except Exception as e:
            db.session.rollback()
            flash(f'خطای عمومی: {str(e)}', 'error')

        return redirect(url_for('extruder_report'))

    # GET: نمایش اخیرها (اگر می‌خوای نمایش بدی، اما در کدت نبود – اضافه کردم)
    recent_reports = ExtruderReport.query.order_by(desc(ExtruderReport.created_at)).limit(10).all()
    return render_template('extruder_report.html', recent_reports=recent_reports)


@app.route('/report/sewing', methods=['GET', 'POST'])
@login_required
def sewing_report():
    recent_reports = SewingReport.query.order_by(SewingReport.date.desc(), SewingReport.created_at.desc()).limit(10).all()

    if request.method == 'POST':
        try:
            # دریافت تاریخ از فیلد مخفی (gregorian-date)
            date_str = request.form.get('date')  # این همان gregorian-date است

            if not date_str or not date_str.strip():
                flash('لطفاً تاریخ را از تقویم انتخاب کنید.', 'error')
                return redirect(url_for('sewing_report'))

            date_str = date_str.strip()

            # تلاش برای تبدیل به تاریخ میلادی
            try:
                report_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                # اگر نشد، احتمالاً کاربر دستی نوشته یا مشکل دیگری وجود دارد
                flash('تاریخ انتخاب شده نامعتبر است. لطفاً حتماً از تقویم شمسی استفاده کنید.', 'error')
                return redirect(url_for('sewing_report'))

            shift = request.form.get('shift')
            operator_name = request.form.get('operator_name')
            if not operator_name:
                operator_name = request.form.get('operatorSelect')  # fallback

            if not shift or not operator_name:
                flash('شیفت کاری و نام اپراتور الزامی هستند.', 'error')
                return redirect(url_for('sewing_report'))

            operator_name = operator_name.strip()

            # توابع کمکی
            def get_float(key, default=0.0):
                val = request.form.get(key)
                if not val or val.strip() == '':
                    return default
                try:
                    return float(val.replace(',', ''))  # پشتیبانی از ویرگول
                except:
                    return default

            def get_int(key, default=0):
                val = request.form.get(key)
                if not val or val.strip() == '':
                    return default
                try:
                    return int(val.replace(',', ''))
                except:
                    return default

            report = SewingReport(
                date=report_date,
                shift=shift,
                operator_name=operator_name,
                roll_barcode=request.form.get('roll_barcode') or None,
                roll_weight=get_float('roll_weight'),
                footage=get_float('footage'),
                bag_width=get_float('bag_width'),
                bag_length=get_float('bag_length'),
                color=request.form.get('color') or None,
                bags_produced=get_int('bags_produced'),
                grade_b_bags=get_int('grade_b_bags'),
                unsewn_bags=get_int('unsewn_bags'),
                bundle_count=get_int('bundle_count'),
                waste=get_float('waste'),
                notes=request.form.get('notes') or None,
                created_by=current_user.id
            )

            db.session.add(report)
            db.session.commit()
            flash('گزارش دوخت و برش با موفقیت ثبت شد.', 'success')

        except Exception as e:
            db.session.rollback()
            flash('خطایی در ثبت گزارش رخ داد. لطفاً دوباره تلاش کنید.', 'error')
            print("Sewing Report Error:", e)

        return redirect(url_for('sewing_report'))

    return render_template('sewing_report.html', recent_reports=recent_reports)

# Edit/Delete Reports
@app.route('/report/edit/<report_type>/<int:report_id>', methods=['GET', 'POST'])
@login_required
def edit_report(report_type, report_id):
    models = {'circular': CircularReport, 'extruder': ExtruderReport, 'sewing': SewingReport}
    model = models.get(report_type)
    report = model.query.get_or_404(report_id)

    if request.method == 'POST':
        for key in request.form.keys():
            if hasattr(report, key) and key not in ['id', 'created_at', 'created_by']:
                value = request.form.get(key)
                if key == 'date':
                    value = datetime.strptime(value, '%Y-%m-%d').date()
                elif key in ['footage', 'roll_weight', 'downtime_hours', 'bag_width', 'machine_speed']:
                    value = float(value) if value else 0
                elif key in ['bags_produced', 'grade_b_bags', 'unsewn_bags', 'bundle_count', 'machine_number']:
                    value = int(value) if value else 0
                setattr(report, key, value)

        db.session.commit()
        flash('گزارش با موفقیت ویرایش شد', 'success')
        return redirect(url_for('manage_reports'))

    machines = Machine.query.filter_by(section='circular').all() if report_type == 'circular' else []
    return render_template('edit_report.html', report=report, report_type=report_type, machines=machines)


@app.route('/report/delete/<report_type>/<int:report_id>')
@login_required
def delete_report(report_type, report_id):
    models = {'circular': CircularReport, 'extruder': ExtruderReport, 'sewing': SewingReport}
    model = models.get(report_type)
    report = model.query.get_or_404(report_id)
    db.session.delete(report)
    db.session.commit()
    flash('گزارش حذف شد', 'success')
    return redirect(url_for('manage_reports'))


@app.route('/manage-reports')
@login_required
def manage_reports():
    circular = CircularReport.query.order_by(desc(CircularReport.created_at)).all()
    extruder = ExtruderReport.query.order_by(desc(ExtruderReport.created_at)).all()
    sewing = SewingReport.query.order_by(desc(SewingReport.created_at)).all()
    return render_template('manage_reports.html', circular=circular, extruder=extruder, sewing=sewing)


# Analytics Routes with Filters
@app.route('/analytics/operators')
@login_required
def operator_analytics():
    # دریافت days و تبدیل ایمن به عدد
    days_str = request.args.get('days', '30')
    try:
        days = int(days_str)
        if days <= 0:
            days = 30  # جلوگیری از مقادیر نامعتبر
    except (ValueError, TypeError):
        days = 30  # پیش‌فرض در صورت خطا

    shift_filter = request.args.get('shift', '').strip()
    performance_filter = request.args.get('performance', '').strip()
    search_query = request.args.get('search', '').strip()

    # محاسبه بازه زمانی
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # ساخت کوئری
    query = db.session.query(
        CircularReport.operator_name,
        func.avg(CircularReport.footage).label('avg_footage'),
        func.avg(CircularReport.downtime_hours).label('avg_downtime'),
        func.count(CircularReport.id).label('shift_count')
    ).filter(CircularReport.date >= start_date, CircularReport.date <= end_date)

    if shift_filter:
        query = query.filter(CircularReport.shift == shift_filter)

    if search_query:
        query = query.filter(CircularReport.operator_name.contains(search_query))

    operators_data = query.group_by(CircularReport.operator_name).having(func.count(CircularReport.id) > 0).all()

    # فیلتر عملکرد
    if performance_filter:
        filtered = []
        for op in operators_data:
            efficiency = (op.avg_footage / 3000) * 100 if op.avg_footage else 0
            if (performance_filter == 'excellent' and efficiency >= 90) or \
               (performance_filter == 'good' and 75 <= efficiency < 90) or \
               (performance_filter == 'average' and 60 <= efficiency < 75) or \
               (performance_filter == 'weak' and efficiency < 60):
                filtered.append(op)
        operators_data = filtered

    return render_template('operator_analytics.html',
                           operators=operators_data,
                           days=days,
                           shift_filter=shift_filter,
                           performance_filter=performance_filter,
                           search_query=search_query)


@app.route('/analytics/machines/<section>')
@login_required
def machine_analytics(section):
    days = request.args.get('days', '30', type=int)
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    if section == 'circular':
        machine_data = db.session.query(
            CircularReport.machine_number,
            CircularReport.shift,
            func.avg(CircularReport.footage).label('avg_footage'),
            func.avg(CircularReport.downtime_hours).label('avg_downtime')
        ).filter(CircularReport.date >= start_date).group_by(
            CircularReport.machine_number, CircularReport.shift
        ).all()

    issues = MachineIssue.query.filter_by(section=section).filter(
        MachineIssue.date >= start_date
    ).all()

    return render_template('machine_analytics.html', section=section,
                           machine_data=machine_data, issues=issues, days=days)


# Settings
@app.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


# Warehouse
@app.route('/warehouse')
@login_required
def warehouse():
    return render_template('warehouse.html')


# API Routes with flexible date ranges
# --- اضافه کن یا جایگزین کن: API پیشرفته داشبورد ---
from sqlalchemy import func  # اطمینان از وجود import

@app.route('/api/machines')
@login_required
def api_machines():
    """برای پر کردن لیست دستگاه‌ها (فقط در صورت نیاز به نمایش شماره دستگاه‌ها)"""
    section = request.args.get('section', 'circular')
    machines = []
    if section == 'circular':
        machines = [m.machine_number for m in Machine.query.filter_by(section='circular').order_by(Machine.machine_number).all()]
    return jsonify({'machines': machines})


# در بالای فایل، بعد از import ها
from sqlalchemy import and_

# در تابع dashboard_data، این خطوط را جایگزین کن:
@app.route('/api/dashboard-data')
@login_required
def dashboard_data():
    # پارامترها
    section = request.args.get('section', 'circular')
    shift = request.args.get('shift')
    machine = request.args.get('machine')
    period = request.args.get('period', '7d')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # محاسبه بازه زمانی
    today = date.today()
    if period == 'today':
        start_date = end_date = today
    elif period == '7d':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == '1m':
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == '1y':
        start_date = today - timedelta(days=365)
        end_date = today
    elif period == 'custom' and start_date_str and end_date_str:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    else:
        start_date = today - timedelta(days=30)
        end_date = today

    # بازه قبلی برای مقایسه
    delta = end_date - start_date
    prev_start = start_date - delta - timedelta(days=1)
    prev_end = start_date - timedelta(days=1)

    # مدل گزارش بر اساس بخش
    if section == 'circular':
        ReportModel = CircularReport
        value_field = ReportModel.footage
        label = 'متراژ'
        unit = 'متر'
        standard_per_machine = 800  # میانگین استاندارد، می‌توانید از STANDARD_FOOTAGE استفاده کنید
    elif section == 'extruder':
        ReportModel = ExtruderReport
        value_field = ReportModel.material_weight  # یا فیلد مناسب
        label = 'وزن مواد'
        unit = 'کیلو'
        standard_per_machine = 100  # فرضی، تنظیم کنید
    elif section == 'sewing':
        ReportModel = SewingReport
        value_field = ReportModel.bags_produced
        label = 'کیسه'
        unit = 'کیسه'
        standard_per_machine = 5000  # فرضی
    else:
        return jsonify({'error': 'بخش نامعتبر'}), 400

    # فیلتر پایه
    filters = [ReportModel.date.between(start_date, end_date)]
    if shift:
        filters.append(ReportModel.shift == shift)
    if machine:
        filters.append(ReportModel.machine_number == int(machine))

    prev_filters = [ReportModel.date.between(prev_start, prev_end)]
    if shift:
        prev_filters.append(ReportModel.shift == shift)
    if machine:
        prev_filters.append(ReportModel.machine_number == int(machine))

    # مجموع ارزش (total_value)
    total_value = db.session.query(func.sum(value_field)).filter(*filters).scalar() or 0
    prev_total = db.session.query(func.sum(value_field)).filter(*prev_filters).scalar() or 0

    # میانگین روزانه
    days = (end_date - start_date).days + 1
    avg_value = total_value / days if days > 0 else 0
    prev_days = (prev_end - prev_start).days + 1
    prev_avg = prev_total / prev_days if prev_days > 0 else 0

    # ⭐ محاسبه استاندارد بر اساس دستگاه‌های انتخابی
    if section == 'circular':
        if machine:
            # اگر دستگاه خاص انتخاب شده، استاندارد همان دستگاه
            selected_machine = Machine.query.filter_by(id=int(machine)).first()
            standard_per_day = selected_machine.standard_footage if selected_machine else STANDARD_FOOTAGE.get(int(machine), 800)
            # برای هر شیفت، استاندارد یکبار محاسبه می‌شود
            # اگر فیلتر شیفت داریم، فقط یک شیفت، وگرنه سه شیفت
            shifts_per_day = 1 if shift else 3
            standard_per_day = standard_per_day * shifts_per_day
        else:
            # اگر دستگاه خاص انتخاب نشده، کل دستگاه‌ها
            all_machines = Machine.query.filter_by(section='circular').all()
            total_standard = sum(m.standard_footage or STANDARD_FOOTAGE.get(m.machine_number, 800) for m in all_machines)
            shifts_per_day = 1 if shift else 3
            standard_per_day = total_standard * shifts_per_day
    else:
        # برای سایر بخش‌ها (extruder, sewing)
        num_machines = 1 if machine else (Machine.query.filter_by(section=section).count() or 1)
        shifts_per_day = 1 if shift else 3
        standard_per_day = standard_per_machine * num_machines * shifts_per_day

    # داده روزانه (با استاندارد)
    daily_data = db.session.query(
        ReportModel.date,
        func.sum(value_field).label('total'),
        func.avg(value_field).label('avg')
    ).filter(*filters).group_by(ReportModel.date).order_by(ReportModel.date).all()

    # اضافه کردن استاندارد به هر روز
    daily_data = [
        {'date': d.date, 'total': d.total or 0, 'standard': standard_per_day}
        for d in daily_data
    ]

    # داده شیفت‌ها
    shift_data = db.session.query(
        ReportModel.shift,
        func.avg(value_field).label('avg')
    ).filter(*filters).group_by(ReportModel.shift).all()
    shift_data = [{'shift': s.shift, 'avg': s.avg or 0} for s in shift_data]

    # اپراتورهای برتر
    top_operators = db.session.query(
        ReportModel.operator_name,
        func.sum(value_field).label('total')
    ).filter(*filters).group_by(ReportModel.operator_name).order_by(desc('total')).limit(5).all()
    top_operators = [{'operator': op.operator_name, 'total': op.total or 0} for op in top_operators]

    # مسائل پرتکرار
    issues = db.session.query(
        MachineIssue.issue_type,
        func.count(MachineIssue.id).label('count')
    ).filter(
        MachineIssue.section == section,
        MachineIssue.date.between(start_date, end_date)
    ).group_by(MachineIssue.issue_type).order_by(desc('count')).limit(3).all()
    issues = [{'issue_type': i.issue_type, 'count': i.count} for i in issues]

    # ⭐ راندمان کلی (overall_efficiency)
    # محاسبه راندمان بر اساس مجموع تولید واقعی و استاندارد کل دوره
    total_standard_period = standard_per_day * days
    overall_efficiency = (total_value / total_standard_period * 100) if total_standard_period > 0 else 0

    return jsonify({
        'section': section,
        'start_date': str(start_date),
        'end_date': str(end_date),
        'total_value': total_value,
        'prev_total': prev_total,
        'avg_value': avg_value,
        'prev_avg': prev_avg,
        'daily_data': daily_data,
        'shift_data': shift_data,
        'top_operators': top_operators,
        'issues': issues,
        'overall_efficiency': overall_efficiency,
        'label': label,
        'unit': unit
    })

# Export Routes
@app.route('/export/<report_type>/<format>')
@login_required
def export_reports(report_type, format):
    models = {'circular': CircularReport, 'extruder': ExtruderReport, 'sewing': SewingReport}
    model = models.get(report_type)
    reports = model.query.all()

    data = []
    for report in reports:
        row = {column.name: getattr(report, column.name) for column in report.__table__.columns}
        data.append(row)

    df = pd.DataFrame(data)

    if format == 'excel':
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=report_type)
        output.seek(0)
        return send_file(output, download_name=f'{report_type}_report.xlsx', as_attachment=True)

    elif format == 'csv':
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        return send_file(io.BytesIO(output.getvalue().encode('utf-8-sig')),
                         download_name=f'{report_type}_report.csv', as_attachment=True, mimetype='text/csv')


def init_db():
    with app.app_context():
        db.create_all()

        if User.query.filter_by(username='admin').first() is None:
            admin = User(username='admin', full_name='مدیر سیستم', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        if Machine.query.count() == 0:
            for i in range(1, 16):
                machine = Machine(machine_number=i, section='circular')
                db.session.add(machine)

        db.session.commit()


# --- اضافه کن به انتهای app.py، قبل از if __name__ ---
@app.route('/api/operator-machine-matrix')
@login_required
def operator_machine_matrix():
    """ماتریس عملکرد اپراتور-دستگاه (فقط گردباف)"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    days = int(request.args.get('days', 30))
    today = date.today()

    if start_date and end_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except:
            start_date = today - timedelta(days=days)
            end_date = today
    else:
        start_date = today - timedelta(days=days)
        end_date = today

    # ماتریس: اپراتور × دستگاه → میانگین footage
    matrix = db.session.query(
        CircularReport.operator_name,
        CircularReport.machine_number,
        func.avg(CircularReport.footage).label('avg_footage'),
        func.count(CircularReport.id).label('shift_count')
    ).filter(
        CircularReport.date >= start_date,
        CircularReport.date <= end_date
    ).group_by(
        CircularReport.operator_name, CircularReport.machine_number
    ).having(func.count(CircularReport.id) >= 1).all()

    operators = list(set(m.operator_name for m in matrix))
    machines = sorted(list(set(m.machine_number for m in matrix)))

    # ساخت ماتریس 2 بعدی
    data_matrix = []
    for op in operators:
        row = {'operator': op}
        for mach in machines:
            val = next((m for m in matrix if m.operator_name == op and m.machine_number == mach), None)
            row[f'm{mach}'] = round(float(val.avg_footage), 1) if val else 0
            row[f'c{mach}'] = int(val.shift_count) if val else 0
        data_matrix.append(row)

    return jsonify({
        'operators': operators,
        'machines': machines,
        'matrix': data_matrix,
        'start_date': str(start_date),
        'end_date': str(end_date)
    })


@app.route('/api/machine-diagnostics')
@login_required
def machine_diagnostics():
    """تشخیص مشکلات دستگاه (گردباف)"""
    days = int(request.args.get('days', 30))
    today = date.today()
    start_date = today - timedelta(days=days)

    # میانگین downtime و footage برای هر دستگاه
    perf = db.session.query(
        CircularReport.machine_number,
        func.avg(CircularReport.footage).label('avg_footage'),
        func.avg(CircularReport.downtime_hours).label('avg_downtime'),
        func.count(CircularReport.id).label('shifts')
    ).filter(CircularReport.date >= start_date) \
        .group_by(CircularReport.machine_number).all()

    # مسائل گزارش شده
    issues = db.session.query(
        MachineIssue.machine_number,
        MachineIssue.issue_type,
        func.count(MachineIssue.id).label('count')
    ).filter(
        MachineIssue.section == 'circular',
        MachineIssue.date >= start_date
    ).group_by(MachineIssue.machine_number, MachineIssue.issue_type).all()

    # ساخت خروجی
    result = []
    for p in perf:
        machine_issues = [i for i in issues if i.machine_number == p.machine_number]
        top_issue = max(machine_issues, key=lambda x: x.count) if machine_issues else None
        result.append({
            'machine': int(p.machine_number),
            'avg_footage': round(float(p.avg_footage or 0), 1),
            'avg_downtime': round(float(p.avg_downtime or 0), 1),
            'shifts': int(p.shifts),
            'top_issue': top_issue.issue_type if top_issue else 'بدون مشکل',
            'issue_count': top_issue.count if top_issue else 0
        })

    # پیشنهاد هوشمند
    suggestions = []
    for r in result:
        if r['avg_downtime'] > 2:
            suggestions.append(f"دستگاه {r['machine']}: توقف بالا ({r['avg_downtime']} ساعت) → بررسی فنی فوری")
        if r['avg_footage'] < 1500 and r['shifts'] > 3:
            suggestions.append(f"دستگاه {r['machine']}: تولید پایین → آموزش اپراتور یا تعمیر")
        if r['issue_count'] > 2:
            suggestions.append(f"دستگاه {r['machine']}: تکرار مشکل «{r['top_issue']}» → برنامه تعمیر")

    return jsonify({
        'diagnostics': result,
        'suggestions': suggestions,
        'period': f'{start_date} تا {end_date}'
    })

if __name__ == '__main__':
    if not os.path.exists('factory_monitoring.db'):
        init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
