import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
from pathlib import Path

# Page Configuration
st.set_page_config(
    page_title="سیستم مدیریت تولید - نخ تابان زرین دست",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for RTL and Persian fonts
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@400;700&display=swap');

    * {
        font-family: 'Vazirmatn', sans-serif !important;
        direction: rtl;
    }

    section[data-testid="stSidebar"] {
        right: 0;
        left: auto;
    }

    section[data-testid="stSidebar"] > div {
        direction: rtl;
        text-align: right;
    }

    .main .block-container {
        direction: rtl;
        text-align: right;
        padding-right: 5rem;
        padding-left: 1rem;
    }

    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }

    .main-header h1 {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }

    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9ff 0%, #ffffff 100%);
    }
</style>
""", unsafe_allow_html=True)

# Data persistence
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
PRODUCTION_FILE = DATA_DIR / "production_data.json"
USERS_FILE = DATA_DIR / "users.json"

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_display_name' not in st.session_state:
    st.session_state.user_display_name = None


def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        default_users = {
            'admin': {'password': 'admin123', 'role': 'مدیر', 'name': 'مدیر سیستم'},
            'shift_morning': {'password': 'shift123', 'role': 'سرپرست شیفت صبح', 'name': 'سرپرست صبح'},
            'shift_evening': {'password': 'shift123', 'role': 'سرپرست شیفت عصر', 'name': 'سرپرست عصر'},
            'shift_night': {'password': 'shift123', 'role': 'سرپرست شیفت شب', 'name': 'سرپرست شب'},
        }
        save_users(default_users)
        return default_users


def save_users(users):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def load_production_data():
    if PRODUCTION_FILE.exists():
        with open(PRODUCTION_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if data:
                return pd.DataFrame(data)
    return pd.DataFrame()


def save_production_data(df):
    with open(PRODUCTION_FILE, 'w', encoding='utf-8') as f:
        json.dump(df.to_dict('records'), f, ensure_ascii=False, indent=2)


def add_production_record(record):
    df = load_production_data()
    record['شناسه'] = len(df) + 1
    record['تاریخ_ثبت'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    save_production_data(df)
    return True


def update_production_record(record_id, updated_record):
    df = load_production_data()
    idx = df[df['شناسه'] == record_id].index
    if len(idx) > 0:
        for key, value in updated_record.items():
            df.loc[idx[0], key] = value
        df.loc[idx[0], 'تاریخ_ویرایش'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        save_production_data(df)
        return True
    return False


def delete_production_record(record_id):
    df = load_production_data()
    df = df[df['شناسه'] != record_id]
    save_production_data(df)
    return True


USERS = load_users()


def login_page():
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        st.markdown("### 🏭")

    st.markdown("""
    <div class="main-header">
        <h1>سیستم مدیریت تولید</h1>
        <h2>شرکت نخ تابان زرین دست</h2>
        <p style="font-size: 0.9rem; margin-top: 1rem;">سیستم جامع مدیریت و گزارش‌گیری تولید</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### 🔐 ورود به سیستم")
        username = st.text_input("👤 نام کاربری", key="login_username")
        password = st.text_input("🔑 رمز عبور", type="password", key="login_password")

        if st.button("✅ ورود", key="login_button", use_container_width=True):
            if username in USERS and USERS[username]['password'] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USERS[username]['role']
                st.session_state.user_display_name = USERS[username]['name']
                st.session_state.username = username
                st.success("✅ ورود موفقیت‌آمیز!")
                st.rerun()
            else:
                st.error("❌ نام کاربری یا رمز عبور اشتباه است")

        with st.expander("📋 راهنمای ورود"):
            st.info("""
            **حساب مدیر:**
            - نام کاربری: `admin`
            - رمز عبور: `admin123`

            **حساب‌های سرپرست:**
            - نام کاربری: `shift_morning` / `shift_evening` / `shift_night`
            - رمز عبور: `shift123`
            """)


def dashboard_page():
    df = load_production_data()

    st.markdown(f"""
    <div class="main-header">
        <h1>📊 داشبورد مدیریتی پیشرفته</h1>
        <p>خوش آمدید {st.session_state.user_display_name} | نقش: {st.session_state.user_role}</p>
        <p style="font-size: 0.9em; opacity: 0.9;">آخرین بروزرسانی: {datetime.now().strftime('%Y/%m/%d - %H:%M')}</p>
    </div>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("⚠️ هنوز داده‌ای ثبت نشده است. لطفاً از بخش 'ثبت اطلاعات' داده وارد کنید.")
        return

    if 'تاریخ' in df.columns:
        df['تاریخ'] = pd.to_datetime(df['تاریخ'])

    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 نمای کلی",
        "👤 پایش اپراتورها",
        "🏭 پایش دستگاه‌های گردباف",
        "⏰ تحلیل شیفت‌ها"
    ])

    with tab1:
        show_overview_dashboard(df)

    with tab2:
        show_operator_monitoring(df)

    with tab3:
        show_machine_monitoring(df)

    with tab4:
        show_shift_analysis(df)


def show_overview_dashboard(df):
    """نمای کلی سیستم با مقایسه دوره قبل"""

    with st.sidebar:
        st.markdown("### 🔍 فیلترها")
        time_period = st.selectbox(
            "📅 بازه زمانی",
            ["امروز", "7 روز گذشته", "30 روز گذشته", "ماه جاری", "بازه دلخواه"],
            index=1
        )

        if time_period == "بازه دلخواه":
            start_date = st.date_input("از تاریخ", datetime.now() - timedelta(days=30))
            end_date = st.date_input("تا تاریخ", datetime.now())
        else:
            end_date = datetime.now()
            if time_period == "امروز":
                start_date = datetime.now()
            elif time_period == "7 روز گذشته":
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == "30 روز گذشته":
                start_date = datetime.now() - timedelta(days=30)
            else:
                start_date = datetime.now().replace(day=1)

    df_filtered = df[
        (df['تاریخ'] >= pd.to_datetime(start_date)) &
        (df['تاریخ'] <= pd.to_datetime(end_date))
        ].copy()

    if df_filtered.empty:
        st.warning("⚠️ داده‌ای یافت نشد.")
        return

    # محاسبه دوره قبل
    days_diff = (end_date - start_date).days
    prev_start = start_date - timedelta(days=days_diff)
    prev_end = start_date

    df_previous = df[
        (df['تاریخ'] >= pd.to_datetime(prev_start)) &
        (df['تاریخ'] < pd.to_datetime(prev_end))
        ].copy()

    st.markdown("## 📈 شاخص‌های کلیدی (با مقایسه دوره قبل)")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_sacks = df_filtered['تعداد_گونی'].sum() if 'تعداد_گونی' in df_filtered.columns else 0
        prev_sacks = df_previous[
            'تعداد_گونی'].sum() if 'تعداد_گونی' in df_previous.columns and not df_previous.empty else 0
        delta_sacks = total_sacks - prev_sacks
        delta_percent = (delta_sacks / prev_sacks * 100) if prev_sacks > 0 else 0
        st.metric("🎯 کل تولید", f"{total_sacks:,}", f"{delta_sacks:+,} ({delta_percent:+.1f}%)")

    with col2:
        total_weight = df_filtered['وزن_کل'].sum() if 'وزن_کل' in df_filtered.columns else 0
        prev_weight = df_previous['وزن_کل'].sum() if 'وزن_کل' in df_previous.columns and not df_previous.empty else 0
        delta_weight = total_weight - prev_weight
        st.metric("⚖️ وزن کل", f"{total_weight:,.0f} kg", f"{delta_weight:+,.0f} kg")

    with col3:
        total_waste = df_filtered['ضایعات'].sum() if 'ضایعات' in df_filtered.columns else 0
        prev_waste = df_previous['ضایعات'].sum() if 'ضایعات' in df_previous.columns and not df_previous.empty else 0
        delta_waste = total_waste - prev_waste
        st.metric("♻️ ضایعات", f"{total_waste:,.0f} kg", f"{delta_waste:+,.0f} kg", delta_color="inverse")

    with col4:
        efficiency = ((total_weight - total_waste) / total_weight * 100) if total_weight > 0 else 0
        prev_efficiency = ((prev_weight - prev_waste) / prev_weight * 100) if prev_weight > 0 else 0
        delta_eff = efficiency - prev_efficiency
        st.metric("✅ راندمان", f"{efficiency:.1f}%", f"{delta_eff:+.1f}%")

    with col5:
        unique_ops = df_filtered['اپراتور'].nunique() if 'اپراتور' in df_filtered.columns else 0
        st.metric("👥 اپراتورها", f"{unique_ops}")

    st.markdown("---")

    # متراژ گردباف
    if 'دستگاه' in df_filtered.columns:
        df_gardbaf = df_filtered[df_filtered['دستگاه'] == 'گردباف']
        if not df_gardbaf.empty and 'متراژ' in df_gardbaf.columns:
            st.markdown("### 📏 شاخص‌های گردباف")
            col1, col2, col3 = st.columns(3)

            with col1:
                total_metraj = df_gardbaf['متراژ'].sum()
                st.metric("📏 متراژ کل بافت", f"{total_metraj:,.0f} متر")

            with col2:
                active_machines = df_gardbaf['شماره_دستگاه'].nunique() if 'شماره_دستگاه' in df_gardbaf.columns else 0
                st.metric("🏭 دستگاه‌های فعال", f"{active_machines} از 15")

            with col3:
                avg_metraj = total_metraj / active_machines if active_machines > 0 else 0
                st.metric("📊 میانگین متراژ/دستگاه", f"{avg_metraj:,.0f} متر")

            st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        if 'دستگاه' in df_filtered.columns:
            st.markdown("### 🏭 تولید دستگاه‌ها")
            machine_data = df_filtered.groupby('دستگاه')['تعداد_گونی'].sum().reset_index()
            fig = px.pie(machine_data, values='تعداد_گونی', names='دستگاه', hole=0.5)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        if 'شیفت' in df_filtered.columns:
            st.markdown("### ⏰ تولید شیفت‌ها")
            shift_data = df_filtered.groupby('شیفت')['تعداد_گونی'].sum().reset_index()
            fig = px.pie(shift_data, values='تعداد_گونی', names='شیفت', hole=0.5,
                         color_discrete_map={'صبح': '#FF6B6B', 'عصر': '#4ECDC4', 'شب': '#45B7D1'})
            st.plotly_chart(fig, use_container_width=True)


def show_operator_monitoring(df):
    """پایش اپراتورها"""

    st.markdown("## 👤 پایش عملکرد اپراتورها")

    if 'اپراتور' not in df.columns:
        st.warning("⚠️ ستون 'اپراتور' وجود ندارد.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        date_range = st.selectbox("📅 بازه زمانی", ["7 روز گذشته", "30 روز گذشته", "بازه دلخواه"], key="op_range")

    if date_range == "بازه دلخواه":
        with col2:
            start_date = st.date_input("از", datetime.now() - timedelta(days=30), key="op_start")
    else:
        start_date = datetime.now() - timedelta(days=7 if date_range == "7 روز گذشته" else 30)

    end_date = datetime.now()

    df_period = df[
        (df['تاریخ'] >= pd.to_datetime(start_date)) &
        (df['تاریخ'] <= pd.to_datetime(end_date))
        ].copy()

    df_period = df_period[df_period['اپراتور'].notna() & (df_period['اپراتور'] != '')]

    if df_period.empty:
        st.warning("⚠️ داده‌ای یافت نشد.")
        return

    st.markdown("### 📊 رتبه‌بندی اپراتورها")

    op_stats = df_period.groupby('اپراتور').agg({
        'تعداد_گونی': 'sum',
        'وزن_کل': 'sum',
        'ضایعات': 'sum',
        'زمان_توقف': 'sum',
        'شناسه': 'count'
    }).reset_index()

    op_stats.columns = ['اپراتور', 'کل_تولید', 'وزن_کل', 'ضایعات', 'زمان_توقف', 'تعداد_شیفت']
    op_stats['راندمان (%)'] = ((op_stats['وزن_کل'] - op_stats['ضایعات']) / op_stats['وزن_کل'] * 100).round(1)
    op_stats['میانگین/شیفت'] = (op_stats['کل_تولید'] / op_stats['تعداد_شیفت']).round(0)
    op_stats = op_stats.sort_values('کل_تولید', ascending=False)
    op_stats.insert(0, '🏆', range(1, len(op_stats) + 1))

    st.dataframe(op_stats, use_container_width=True, hide_index=True,
                 column_config={
                     "راندمان (%)": st.column_config.ProgressColumn("راندمان", format="%.1f%%", min_value=0,
                                                                    max_value=100)
                 })

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📊 مقایسه تولید")
        fig = px.bar(op_stats.head(10), x='اپراتور', y='کل_تولید',
                     color='راندمان (%)', color_continuous_scale='RdYlGn', text='کل_تولید')
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### ⚡ میانگین تولید")
        fig = px.bar(op_stats.head(10), x='اپراتور', y='میانگین/شیفت', text='میانگین/شیفت')
        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)


def show_machine_monitoring(df):
    """پایش دستگاه‌های گردباف - نسخه کامل"""

    st.markdown("## 🏭 پایش دستگاه‌های گردباف (15 دستگاه)")

    if 'دستگاه' not in df.columns:
        st.warning("⚠️ ستون 'دستگاه' وجود ندارد.")
        return

    df_gardbaf = df[df['دستگاه'] == 'گردباف'].copy()

    if df_gardbaf.empty:
        st.warning("⚠️ هنوز گزارشی برای دستگاه‌های گردباف ثبت نشده است.")
        return

    # فیلتر تاریخ
    date_range = st.sidebar.selectbox("📅 بازه زمانی",
                                      ["7 روز گذشته", "30 روز گذشته", "90 روز گذشته"],
                                      key="machine_date_main")

    days = {'7 روز گذشته': 7, '30 روز گذشته': 30, '90 روز گذشته': 90}[date_range]
    start_date = datetime.now() - timedelta(days=days)
    end_date = datetime.now()

    df_period = df_gardbaf[
        (df_gardbaf['تاریخ'] >= pd.to_datetime(start_date)) &
        (df_gardbaf['تاریخ'] <= pd.to_datetime(end_date))
        ].copy()

    if df_period.empty:
        st.warning("⚠️ در بازه زمانی انتخاب شده داده‌ای یافت نشد.")
        return

    # محاسبه دوره قبل
    prev_start = start_date - timedelta(days=days)
    prev_end = start_date
    df_previous = df_gardbaf[
        (df_gardbaf['تاریخ'] >= pd.to_datetime(prev_start)) &
        (df_gardbaf['تاریخ'] < pd.to_datetime(prev_end))
        ].copy()

    # تب‌ها
    tab1, tab2, tab3 = st.tabs([
        "📊 نمای کلی همه دستگاه‌ها",
        "🔍 پایش تک‌تک دستگاه‌ها",
        "🎯 ماتریس اپراتور-دستگاه"
    ])

    with tab1:
        show_machines_overview(df_period, df_previous)

    with tab2:
        show_individual_machine_details(df_period, df_gardbaf, start_date)

    with tab3:
        show_operator_machine_matrix(df_period)


def show_machines_overview(df_period, df_previous):
    """نمای کلی همه دستگاه‌ها"""

    st.markdown("### 📊 عملکرد 15 دستگاه گردباف")

    if 'شماره_دستگاه' not in df_period.columns:
        st.warning("⚠️ ستون 'شماره_دستگاه' وجود ندارد.")
        return

    machine_stats = df_period.groupby('شماره_دستگاه').agg({
        'تعداد_گونی': 'sum',
        'متراژ': 'sum',
        'وزن_کل': 'sum',
        'ضایعات': 'sum',
        'زمان_توقف': 'sum',
        'تعداد_معیوب': 'sum',
        'شناسه': 'count'
    }).reset_index()

    machine_stats.columns = ['شماره', 'تعداد_گونی', 'متراژ', 'وزن', 'ضایعات', 'توقف', 'معیوب', 'تعداد_شیفت']
    machine_stats['راندمان (%)'] = ((machine_stats['وزن'] - machine_stats['ضایعات']) /
                                    machine_stats['وزن'] * 100).round(1).fillna(0)
    machine_stats['میانگین_تولید'] = (machine_stats['تعداد_گونی'] / machine_stats['تعداد_شیفت']).round(0)

    # محاسبه دوره قبل
    if not df_previous.empty and 'شماره_دستگاه' in df_previous.columns:
        prev_stats = df_previous.groupby('شماره_دستگاه')['تعداد_گونی'].sum()
        machine_stats['تولید_قبل'] = machine_stats['شماره'].map(prev_stats).fillna(0)
        machine_stats['تغییر'] = machine_stats['تعداد_گونی'] - machine_stats['تولید_قبل']
        machine_stats['تغییر_درصد'] = ((machine_stats['تغییر'] / machine_stats['تولید_قبل']) * 100).round(1).fillna(0)

    machine_stats = machine_stats.sort_values('شماره')

    # کارت‌های متریک
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏆 5 دستگاه برتر")
        top_5 = machine_stats.nlargest(5, 'تعداد_گونی')

        for idx, row in top_5.iterrows():
            delta = f"+{int(row['تغییر']):,} ({row['تغییر_درصد']:+.1f}%)" if 'تغییر' in row else ""
            st.success(f"**دستگاه {int(row['شماره'])}** → {int(row['تعداد_گونی']):,} گونی | "
                       f"راندمان: {row['راندمان (%)']}% | {int(row['متراژ']):,} متر {delta}")

    with col2:
        st.markdown("#### ⚠️ 5 دستگاه ضعیف‌تر")
        bottom_5 = machine_stats.nsmallest(5, 'تعداد_گونی')

        for idx, row in bottom_5.iterrows():
            st.warning(f"**دستگاه {int(row['شماره'])}** → {int(row['تعداد_گونی']):,} گونی | "
                       f"راندمان: {row['راندمان (%)']}% | توقف: {int(row['توقف'])} دقیقه")

    st.markdown("---")

    # جدول کامل
    st.markdown("### 📋 جدول کامل")
    display_cols = ['شماره', 'تعداد_گونی', 'متراژ', 'میانگین_تولید', 'راندمان (%)', 'توقف']
    if 'تغییر' in machine_stats.columns:
        display_cols.extend(['تغییر', 'تغییر_درصد'])

    st.dataframe(machine_stats[display_cols], use_container_width=True, hide_index=True,
                 column_config={
                     "شماره": st.column_config.NumberColumn("دستگاه", format="دستگاه %d"),
                     "راندمان (%)": st.column_config.ProgressColumn("راندمان", format="%.1f%%", min_value=0,
                                                                    max_value=100)
                 })

    st.markdown("---")

    # نمودارها
    col1, col2 = st.columns(2)

    with col1:
        fig1 = px.bar(machine_stats, x='شماره', y='تعداد_گونی',
                      color='راندمان (%)', color_continuous_scale='RdYlGn',
                      text='تعداد_گونی', title='تولید دستگاه‌ها')
        fig1.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        fig2 = px.bar(machine_stats, x='شماره', y='متراژ',
                      color='توقف', color_continuous_scale='Reds',
                      text='متراژ', title='متراژ بافت')
        fig2.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        st.plotly_chart(fig2, use_container_width=True)


def show_individual_machine_details(df_period, df_all, start_date):
    """پایش تک‌تک دستگاه‌ها"""

    st.markdown("### 🔍 انتخاب دستگاه برای پایش دقیق")

    if 'شماره_دستگاه' not in df_period.columns:
        st.warning("⚠️ ستون 'شماره_دستگاه' وجود ندارد.")
        return

    available_machines = sorted(df_period['شماره_دستگاه'].unique())
    selected_machine = st.selectbox(
        "🏭 انتخاب شماره دستگاه",
        available_machines,
        format_func=lambda x: f"دستگاه {x}",
        key="individual_machine_select"
    )

    if selected_machine:
        st.markdown(f"## 📊 گزارش کامل دستگاه {selected_machine}")

        machine_data = df_period[df_period['شماره_دستگاه'] == selected_machine].copy()

        # محاسبه دوره قبل
        days_diff = (datetime.now() - start_date).days
        prev_start = start_date - timedelta(days=days_diff)
        prev_machine_data = df_all[
            (df_all['شماره_دستگاه'] == selected_machine) &
            (df_all['تاریخ'] >= pd.to_datetime(prev_start)) &
            (df_all['تاریخ'] < pd.to_datetime(start_date))
            ]

        # متریک‌ها
        st.markdown("### 📈 شاخص‌های دستگاه (با مقایسه دوره قبل)")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_prod = machine_data['تعداد_گونی'].sum()
            prev_prod = prev_machine_data['تعداد_گونی'].sum() if not prev_machine_data.empty else 0
            delta_prod = total_prod - prev_prod
            st.metric("🎯 کل تولید", f"{total_prod:,}", f"{delta_prod:+,}")

        with col2:
            total_metraj = machine_data['متراژ'].sum() if 'متراژ' in machine_data.columns else 0
            prev_metraj = prev_machine_data[
                'متراژ'].sum() if not prev_machine_data.empty and 'متراژ' in prev_machine_data.columns else 0
            delta_metraj = total_metraj - prev_metraj
            st.metric("📏 متراژ", f"{total_metraj:,} متر", f"{delta_metraj:+,}")

        with col3:
            total_downtime = machine_data['زمان_توقف'].sum()
            prev_downtime = prev_machine_data['زمان_توقف'].sum() if not prev_machine_data.empty else 0
            delta_downtime = total_downtime - prev_downtime
            st.metric("⏱️ زمان توقف", f"{total_downtime:,} دقیقه", f"{delta_downtime:+,}", delta_color="inverse")

        with col4:
            weight = machine_data['وزن_کل'].sum()
            waste = machine_data['ضایعات'].sum()
            efficiency = ((weight - waste) / weight * 100) if weight > 0 else 0

            prev_weight = prev_machine_data['وزن_کل'].sum() if not prev_machine_data.empty else 0
            prev_waste = prev_machine_data['ضایعات'].sum() if not prev_machine_data.empty else 0
            prev_efficiency = ((prev_weight - prev_waste) / prev_weight * 100) if prev_weight > 0 else 0
            delta_efficiency = efficiency - prev_efficiency

            st.metric("✅ راندمان", f"{efficiency:.1f}%", f"{delta_efficiency:+.1f}%")

        st.markdown("---")

        # اپراتورهایی که روی این دستگاه کار کرده‌اند
        st.markdown(f"### 👥 اپراتورهایی که روی دستگاه {selected_machine} کار کرده‌اند")

        if 'اپراتور' in machine_data.columns:
            machine_data_clean = machine_data[
                machine_data['اپراتور'].notna() & (machine_data['اپراتور'] != '')
                ]

            if not machine_data_clean.empty:
                op_stats = machine_data_clean.groupby('اپراتور').agg({
                    'تعداد_گونی': ['sum', 'mean', 'count'],
                    'متراژ': 'sum',
                    'وزن_کل': 'sum',
                    'ضایعات': 'sum',
                    'زمان_توقف': 'sum'
                }).reset_index()

                op_stats.columns = ['اپراتور', 'کل_تولید', 'میانگین', 'تعداد_شیفت', 'متراژ', 'وزن', 'ضایعات', 'توقف']
                op_stats['راندمان (%)'] = ((op_stats['وزن'] - op_stats['ضایعات']) / op_stats['وزن'] * 100).round(
                    1).fillna(0)
                op_stats = op_stats.sort_values('کل_تولید', ascending=False)
                op_stats.insert(0, '🏆', range(1, len(op_stats) + 1))

                col1, col2 = st.columns([2, 1])

                with col1:
                    fig = px.bar(op_stats, x='اپراتور', y='کل_تولید',
                                 color='راندمان (%)', color_continuous_scale='RdYlGn',
                                 text='کل_تولید', title=f'رتبه‌بندی اپراتورها روی دستگاه {selected_machine}')
                    fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.markdown("#### 📋 جدول عملکرد")
                    st.dataframe(op_stats[['🏆', 'اپراتور', 'کل_تولید', 'متراژ', 'راندمان (%)']],
                                 use_container_width=True, hide_index=True,
                                 column_config={
                                     "راندمان (%)": st.column_config.ProgressColumn("راندمان", format="%.1f%%",
                                                                                    min_value=0, max_value=100)
                                 })

                    best_op = op_stats.iloc[0]
                    st.success(f"""
                    🏆 **بهترین اپراتور:**  
                    **{best_op['اپراتور']}**  
                    تولید: {int(best_op['کل_تولید']):,}  
                    راندمان: {best_op['راندمان (%)']:.1f}%
                    """)

                    if len(op_stats) > 1:
                        worst_op = op_stats.iloc[-1]
                        st.warning(f"⚠️ **نیاز به بهبود:** {worst_op['اپراتور']} ({worst_op['راندمان (%)']:.1f}%)")

                st.markdown("---")

                # عملکرد در شیفت‌های مختلف
                st.markdown(f"### ⏰ عملکرد دستگاه {selected_machine} در شیفت‌های مختلف")

                if 'شیفت' in machine_data.columns:
                    shift_stats = machine_data.groupby('شیفت').agg({
                        'تعداد_گونی': 'sum',
                        'متراژ': 'sum',
                        'زمان_توقف': 'sum'
                    }).reset_index()

                    col1, col2 = st.columns(2)

                    with col1:
                        fig_shift = px.bar(shift_stats, x='شیفت', y='تعداد_گونی',
                                           color='شیفت', text='تعداد_گونی', title='تولید در هر شیفت',
                                           color_discrete_map={'صبح': '#FF6B6B', 'عصر': '#4ECDC4', 'شب': '#45B7D1'})
                        fig_shift.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                        st.plotly_chart(fig_shift, use_container_width=True)

                    with col2:
                        fig_downtime = px.bar(shift_stats, x='شیفت', y='زمان_توقف',
                                              color='شیفت', text='زمان_توقف', title='زمان توقف در هر شیفت',
                                              color_discrete_map={'صبح': '#FF6B6B', 'عصر': '#4ECDC4', 'شب': '#45B7D1'})
                        fig_downtime.update_traces(texttemplate='%{text}', textposition='outside')
                        st.plotly_chart(fig_downtime, use_container_width=True)

                st.markdown("---")

                # روند تولید
                st.markdown(f"### 📉 روند تولید دستگاه {selected_machine}")

                daily_data = machine_data.groupby('تاریخ').agg({
                    'تعداد_گونی': 'sum',
                    'متراژ': 'sum',
                    'زمان_توقف': 'sum'
                }).reset_index().sort_values('تاریخ')

                fig_timeline = go.Figure()
                fig_timeline.add_trace(go.Scatter(
                    x=daily_data['تاریخ'], y=daily_data['تعداد_گونی'],
                    mode='lines+markers', name='تولید',
                    line=dict(color='#667eea', width=3), fill='tozeroy'))

                if 'متراژ' in daily_data.columns:
                    fig_timeline.add_trace(go.Scatter(
                        x=daily_data['تاریخ'], y=daily_data['متراژ'],
                        mode='lines+markers', name='متراژ', yaxis='y2',
                        line=dict(color='#4ECDC4', width=2)))

                fig_timeline.update_layout(
                    yaxis2=dict(title='متراژ (متر)', overlaying='y', side='right'),
                    height=400, hovermode='x unified')
                st.plotly_chart(fig_timeline, use_container_width=True)

                st.markdown("---")

                # یادداشت‌ها و مشکلات
                st.markdown(f"### 📝 یادداشت‌ها و مشکلات دستگاه {selected_machine}")

                if 'توضیحات' in machine_data.columns:
                    notes_data = machine_data[
                        machine_data['توضیحات'].notna() & (machine_data['توضیحات'] != '')
                        ][['تاریخ', 'شیفت', 'اپراتور', 'توضیحات']].sort_values('تاریخ', ascending=False)

                    if not notes_data.empty:
                        st.dataframe(notes_data.head(10), use_container_width=True, hide_index=True)
                    else:
                        st.info("✅ مشکل یا یادداشت خاصی ثبت نشده است.")
            else:
                st.info(f"ℹ️ برای دستگاه {selected_machine} هنوز گزارش اپراتوری ثبت نشده است.")


def show_operator_machine_matrix(df_period):
    """ماتریس اپراتور-دستگاه"""

    st.markdown("### 🎯 ماتریس کامل: کدام اپراتور با کدام دستگاه بهتر کار می‌کند؟")

    if 'اپراتور' not in df_period.columns or 'شماره_دستگاه' not in df_period.columns:
        st.warning("⚠️ ستون‌های 'اپراتور' یا 'شماره_دستگاه' وجود ندارد.")
        return

    df_clean = df_period[df_period['اپراتور'].notna() & (df_period['اپراتور'] != '')].copy()

    if df_clean.empty:
        st.info("ℹ️ برای نمایش ماتریس، گزارش‌های گردباف را با نام اپراتور و شماره دستگاه ثبت کنید.")
        return

    st.info("""
    📊 **راهنمای رنگ‌ها:**  
    🟢 **سبز**: راندمان بالای 90% (عالی)  
    🟡 **زرد**: راندمان 75-90% (خوب)  
    🟠 **نارنجی**: راندمان 60-75% (متوسط)  
    🔴 **قرمز**: راندمان کمتر از 60% (نیاز به بهبود)
    """)

    # ایجاد ماتریس عملکرد
    op_machine_matrix = df_clean.groupby(['اپراتور', 'شماره_دستگاه']).agg({
        'تعداد_گونی': 'sum',
        'متراژ': 'sum',
        'وزن_کل': 'sum',
        'ضایعات': 'sum',
        'شناسه': 'count'
    }).reset_index()

    op_machine_matrix.columns = ['اپراتور', 'دستگاه', 'تولید', 'متراژ', 'وزن', 'ضایعات', 'تعداد_شیفت']
    op_machine_matrix['راندمان'] = ((op_machine_matrix['وزن'] - op_machine_matrix['ضایعات']) /
                                    op_machine_matrix['وزن'] * 100).round(1).fillna(0)

    # نقشه حرارتی
    pivot_performance = op_machine_matrix.pivot_table(
        values='راندمان', index='اپراتور', columns='دستگاه', fill_value=0)

    fig_matrix = go.Figure(data=go.Heatmap(
        z=pivot_performance.values,
        x=[f'دستگاه {int(col)}' for col in pivot_performance.columns],
        y=pivot_performance.index,
        colorscale='RdYlGn',
        text=pivot_performance.values,
        texttemplate='%{text:.1f}%',
        textfont={"size": 9},
        hovertemplate='<b>اپراتور: %{y}</b><br>%{x}<br>راندمان: %{z:.1f}%<extra></extra>',
        zmid=85, zmin=0, zmax=100,
        colorbar=dict(title="راندمان (%)")
    ))

    fig_matrix.update_layout(
        title='نقشه حرارتی: راندمان هر اپراتور روی هر دستگاه',
        xaxis_title='شماره دستگاه',
        yaxis_title='اپراتور',
        height=max(500, len(pivot_performance) * 35),
        xaxis={'side': 'top'}
    )

    st.plotly_chart(fig_matrix, use_container_width=True)

    st.markdown("---")

    # بهترین و بدترین ترکیب‌ها
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏆 برترین ترکیب‌های اپراتور-دستگاه")
        best_combinations = op_machine_matrix.nlargest(15, 'راندمان')

        for idx, row in best_combinations.iterrows():
            rank = list(best_combinations.index).index(idx) + 1
            st.success(f"""
            **#{rank}** - **{row['اپراتور']}** + دستگاه **{int(row['دستگاه'])}**  
            ✅ راندمان: **{row['راندمان']:.1f}%** | تولید: {int(row['تولید']):,} | متراژ: {int(row['متراژ']):,} متر
            """)

    with col2:
        st.markdown("### ⚠️ ترکیب‌های نیازمند بهبود")
        worst_combinations = op_machine_matrix[op_machine_matrix['راندمان'] > 0].nsmallest(15, 'راندمان')

        for idx, row in worst_combinations.iterrows():
            st.warning(f"""
            **{row['اپراتور']}** + دستگاه **{int(row['دستگاه'])}**  
            ⚠️ راندمان: **{row['راندمان']:.1f}%** (نیاز به بررسی و آموزش)
            """)

    st.markdown("---")

    # توصیه‌ها
    st.markdown("### 💡 توصیه‌های بهینه‌سازی")

    recommendations = []
    for operator in pivot_performance.index:
        op_data = pivot_performance.loc[operator]
        op_data_sorted = op_data[op_data > 0].sort_values(ascending=False)

        if len(op_data_sorted) > 0:
            best_machines = op_data_sorted.head(3)
            worst_machines = op_data_sorted.tail(2)

            recommendations.append({
                'اپراتور': operator,
                'بهترین_دستگاه_1': f"{int(best_machines.index[0])} ({best_machines.iloc[0]:.1f}%)" if len(
                    best_machines) > 0 else "-",
                'بهترین_دستگاه_2': f"{int(best_machines.index[1])} ({best_machines.iloc[1]:.1f}%)" if len(
                    best_machines) > 1 else "-",
                'بهترین_دستگاه_3': f"{int(best_machines.index[2])} ({best_machines.iloc[2]:.1f}%)" if len(
                    best_machines) > 2 else "-",
                'ضعیف‌ترین': f"{int(worst_machines.index[-1])} ({worst_machines.iloc[-1]:.1f}%)" if len(
                    worst_machines) > 0 else "-"
            })

    recommendations_df = pd.DataFrame(recommendations)

    st.markdown("#### 📋 جدول توصیه‌های اختصاص دستگاه به اپراتورها")
    st.dataframe(recommendations_df, use_container_width=True, hide_index=True)

    st.success("""
    💡 **چگونه از این جدول استفاده کنیم؟**  
    - هر اپراتور را ترجیحاً روی **بهترین دستگاه‌های** خود قرار دهید
    - از قرار دادن اپراتور روی **ضعیف‌ترین دستگاه** خودداری کنید
    - اگر اپراتوری روی دستگاه خاصی راندمان پایین دارد، آموزش ببینید یا دستگاه را تعمیر کنید
    """)


def show_shift_analysis(df):
    """تحلیل شیفت‌ها"""

    st.markdown("## ⏰ تحلیل شیفت‌ها")

    if 'شیفت' not in df.columns:
        st.warning("⚠️ ستون 'شیفت' وجود ندارد.")
        return

    date_range = st.selectbox("📅 بازه", ["7 روز", "30 روز"], key="shift_range")
    days = 7 if date_range == "7 روز" else 30

    df_period = df[df['تاریخ'] >= pd.to_datetime(datetime.now() - timedelta(days=days))].copy()

    if df_period.empty:
        st.warning("⚠️ داده‌ای یافت نشد.")
        return

    st.markdown("### 📊 خلاصه شیفت‌ها")

    shift_stats = df_period.groupby('شیفت').agg({
        'تعداد_گونی': 'sum',
        'وزن_کل': 'sum',
        'ضایعات': 'sum'
    }).reset_index()

    shift_stats['راندمان'] = ((shift_stats['وزن_کل'] - shift_stats['ضایعات']) /
                              shift_stats['وزن_کل'] * 100).round(1)

    cols = st.columns(3)
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    shifts = ['صبح', 'عصر', 'شب']

    for i, shift in enumerate(shifts):
        if shift in shift_stats['شیفت'].values:
            data = shift_stats[shift_stats['شیفت'] == shift].iloc[0]
            with cols[i]:
                st.markdown(f"""
                <div style="background: {colors[i]}; padding: 20px; border-radius: 10px; 
                            color: white; text-align: center;">
                    <h3>شیفت {shift}</h3>
                    <h2>{int(data['تعداد_گونی']):,}</h2>
                    <p>راندمان: {data['راندمان']:.1f}%</p>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # بهترین شیفت برای هر اپراتور
    st.markdown("### 👥 بهترین شیفت برای هر اپراتور")

    if 'اپراتور' in df_period.columns:
        op_data = df_period[df_period['اپراتور'].notna() & (df_period['اپراتور'] != '')]

        if not op_data.empty:
            op_shift = op_data.groupby(['اپراتور', 'شیفت']).agg({
                'تعداد_گونی': 'sum',
                'وزن_کل': 'sum',
                'ضایعات': 'sum'
            }).reset_index()

            op_shift['راندمان'] = ((op_shift['وزن_کل'] - op_shift['ضایعات']) /
                                   op_shift['وزن_کل'] * 100).round(1)

            # نقشه حرارتی
            pivot = op_shift.pivot_table(values='راندمان', index='اپراتور', columns='شیفت', fill_value=0)
            pivot = pivot.reindex(columns=['صبح', 'عصر', 'شب'], fill_value=0)

            fig = go.Figure(data=go.Heatmap(
                z=pivot.values, x=pivot.columns, y=pivot.index,
                colorscale='RdYlGn', text=pivot.values,
                texttemplate='%{text:.1f}%', zmid=85, zmin=0, zmax=100))
            fig.update_layout(height=400, title='نقشه حرارتی راندمان اپراتورها در شیفت‌های مختلف')
            st.plotly_chart(fig, use_container_width=True)


def data_entry_page():
    st.markdown(f"""
    <div class="main-header">
        <h1>📝 ثبت اطلاعات جدید</h1>
        <p>{st.session_state.user_display_name} | {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔧 اکسترودر", "🧵 گردباف", "✂️ دوخت و برش"])

    with tab1:
        st.markdown("### ثبت گزارش اکسترودر")
        with st.form("extruder_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("📅 تاریخ", datetime.now())
                shift = st.selectbox("⏰ شیفت", ["صبح", "عصر", "شب"])
                operator = st.text_input("👤 نام اپراتور")

            with col2:
                production = st.number_input("⚖️ تولید (kg)", min_value=0, value=1000, step=100)
                waste = st.number_input("♻️ ضایعات (kg)", min_value=0, value=0, step=10)
                downtime = st.number_input("⏱️ توقف (دقیقه)", min_value=0, value=0)

            notes = st.text_area("📝 توضیحات")

            if st.form_submit_button("💾 ثبت", use_container_width=True):
                record = {
                    'تاریخ': date.strftime('%Y-%m-%d'),
                    'شیفت': shift,
                    'سرپرست': st.session_state.user_display_name,
                    'دستگاه': 'اکسترودر',
                    'اپراتور': operator,
                    'تعداد_گونی': 0,
                    'عرض': 0,
                    'طول': 0,
                    'وزن_کل': production,
                    'ضایعات': waste,
                    'زمان_توقف': downtime,
                    'توضیحات': notes,
                    'ثبت_کننده': st.session_state.username
                }
                add_production_record(record)
                st.success("✅ ثبت شد!")
                st.balloons()

    with tab2:
        st.markdown("### ثبت گزارش گردباف")
        with st.form("knitting_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)

            with col1:
                date = st.date_input("📅 تاریخ", datetime.now(), key="k_date")
                shift = st.selectbox("⏰ شیفت", ["صبح", "عصر", "شب"], key="k_shift")
                operator = st.text_input("👤 نام اپراتور", placeholder="مثال: احمد رضایی")
                machine_number = st.selectbox("🏭 شماره دستگاه گردباف",
                                              list(range(1, 16)), format_func=lambda x: f"دستگاه {x}")

            with col2:
                width = st.number_input("📐 عرض (cm)", min_value=0, value=70, step=5)
                length = st.number_input("📏 طول (cm)", min_value=0, value=100, step=5)
                sacks = st.number_input("🎯 تعداد گونی", min_value=0, value=500, step=50)
                weight = st.number_input("⚖️ وزن کل (kg)", min_value=0, value=2000, step=100)

            with col3:
                defects = st.number_input("❌ تعداد معیوب", min_value=0, value=0)
                waste = st.number_input("♻️ ضایعات (kg)", min_value=0, value=0, step=10)
                downtime = st.number_input("⏱️ زمان توقف (دقیقه)", min_value=0, value=0, key="k_down")
                meters = st.number_input("📏 متراژ بافت (متر)", min_value=0, value=0, step=50)

            notes = st.text_area("📝 توضیحات و مشکلات دستگاه", key="k_notes")

            if st.form_submit_button("💾 ثبت گزارش", use_container_width=True):
                if not operator.strip():
                    st.error("❌ نام اپراتور الزامی است")
                else:
                    record = {
                        'تاریخ': date.strftime('%Y-%m-%d'),
                        'شیفت': shift,
                        'اپراتور': operator.strip(),
                        'سرپرست': st.session_state.user_display_name,
                        'دستگاه': 'گردباف',
                        'شماره_دستگاه': machine_number,
                        'نام_کامل_دستگاه': f'گردباف-{machine_number}',
                        'تعداد_گونی': sacks,
                        'متراژ': meters,
                        'عرض': width,
                        'طول': length,
                        'وزن_کل': weight,
                        'ضایعات': waste,
                        'تعداد_معیوب': defects,
                        'زمان_توقف': downtime,
                        'توضیحات': notes,
                        'ثبت_کننده': st.session_state.username
                    }
                    add_production_record(record)
                    st.success(f"✅ گزارش {operator} برای دستگاه {machine_number} ثبت شد!")
                    st.balloons()

    with tab3:
        st.markdown("### ثبت گزارش دوخت و برش")
        with st.form("sewing_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("📅 تاریخ", datetime.now(), key="s_date")
                shift = st.selectbox("⏰ شیفت", ["صبح", "عصر", "شب"], key="s_shift")
                operator = st.text_input("👤 اپراتور", key="s_op")
                sack_type = st.selectbox("📦 نوع", ["تک‌لایه", "دولایه", "لمینت"])

            with col2:
                width = st.number_input("📐 عرض (cm)", min_value=0, value=50, step=5, key="s_w")
                length = st.number_input("📏 طول (cm)", min_value=0, value=80, step=5, key="s_l")
                quantity = st.number_input("🎯 تعداد", min_value=0, value=1000, step=100)
                defects = st.number_input("❌ معیوب", min_value=0, value=0, key="s_def")

            quality = st.checkbox("✅ کنترل کیفی")
            notes = st.text_area("📝 توضیحات", key="s_notes")

            if st.form_submit_button("💾 ثبت", use_container_width=True):
                record = {
                    'تاریخ': date.strftime('%Y-%m-%d'),
                    'شیفت': shift,
                    'اپراتور': operator,
                    'سرپرست': st.session_state.user_display_name,
                    'دستگاه': 'دوخت و برش',
                    'نوع_گونی': sack_type,
                    'تعداد_گونی': quantity,
                    'عرض': width,
                    'طول': length,
                    'وزن_کل': 0,
                    'ضایعات': 0,
                    'تعداد_معیوب': defects,
                    'زمان_توقف': 0,
                    'کنترل_کیفی': 'انجام شده' if quality else 'انجام نشده',
                    'توضیحات': notes,
                    'ثبت_کننده': st.session_state.username
                }
                add_production_record(record)
                st.success("✅ ثبت شد!")
                st.balloons()


def reports_page():
    st.markdown("""
    <div class="main-header">
        <h1>📈 گزارش‌های تحلیلی</h1>
        <p>مشاهده و مدیریت رکوردها</p>
    </div>
    """, unsafe_allow_html=True)

    df = load_production_data()

    if df.empty:
        st.warning("⚠️ داده‌ای وجود ندارد.")
        return

    tab1, tab2 = st.tabs(["📋 رکوردها", "✏️ ویرایش/حذف"])

    with tab1:
        st.markdown("### 📋 لیست رکوردها")

        col1, col2 = st.columns(2)
        with col1:
            if 'شیفت' in df.columns:
                shifts = st.multiselect("شیفت", df['شیفت'].unique().tolist(), df['شیفت'].unique().tolist())
        with col2:
            if 'دستگاه' in df.columns:
                machines = st.multiselect("دستگاه", df['دستگاه'].unique().tolist(), df['دستگاه'].unique().tolist())

        df_filtered = df.copy()
        if shifts and 'شیفت' in df.columns:
            df_filtered = df_filtered[df_filtered['شیفت'].isin(shifts)]
        if machines and 'دستگاه' in df.columns:
            df_filtered = df_filtered[df_filtered['دستگاه'].isin(machines)]

        st.dataframe(df_filtered, use_container_width=True, height=500)

        st.markdown("### 📥 دانلود")
        csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📄 دانلود CSV", csv, f"report_{datetime.now().strftime('%Y%m%d')}.csv",
                           "text/csv", use_container_width=True)

    with tab2:
        st.markdown("### ✏️ ویرایش/حذف")

        if 'شناسه' not in df.columns:
            st.error("ستون 'شناسه' وجود ندارد.")
            return

        record_id = st.selectbox("🔍 انتخاب رکورد", df['شناسه'].tolist(),
                                 format_func=lambda
                                     x: f"#{x} - {df[df['شناسه'] == x]['تاریخ'].values[0]} - {df[df['شناسه'] == x]['دستگاه'].values[0]}")

        if record_id:
            record = df[df['شناسه'] == record_id].iloc[0].to_dict()

            with st.form("edit_form"):
                col1, col2 = st.columns(2)

                with col1:
                    e_date = st.date_input("تاریخ", value=datetime.strptime(record['تاریخ'],
                                                                            '%Y-%m-%d') if 'تاریخ' in record else datetime.now())
                    e_shift = st.selectbox("شیفت", ["صبح", "عصر", "شب"],
                                           index=["صبح", "عصر", "شب"].index(record['شیفت']) if 'شیفت' in record else 0)

                with col2:
                    e_sacks = st.number_input("تعداد گونی", value=int(record.get('تعداد_گونی', 0)), min_value=0)
                    e_weight = st.number_input("وزن", value=float(record.get('وزن_کل', 0)), min_value=0.0)

                e_notes = st.text_area("توضیحات", value=record.get('توضیحات', ''))

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    if st.form_submit_button("✅ بروزرسانی", use_container_width=True):
                        updated = {
                            'تاریخ': e_date.strftime('%Y-%m-%d'),
                            'شیفت': e_shift,
                            'تعداد_گونی': e_sacks,
                            'وزن_کل': e_weight,
                            'توضیحات': e_notes
                        }
                        if update_production_record(record_id, updated):
                            st.success("✅ بروزرسانی شد!")
                            st.rerun()
                        else:
                            st.error("❌ خطا")

                with col_btn2:
                    if st.form_submit_button("🗑️ حذف", use_container_width=True):
                        if delete_production_record(record_id):
                            st.success("🗑️ حذف شد!")
                            st.rerun()


def settings_page():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ تنظیمات</h1>
        <p>مدیریت سیستم</p>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.user_role != 'مدیر':
        st.error("⛔ فقط مدیر دسترسی دارد.")
        return

    tab1, tab2 = st.tabs(["👥 کاربران", "💾 پشتیبان"])

    with tab1:
        st.markdown("### 👥 مدیریت کاربران")

        with st.expander("➕ افزودن کاربر"):
            with st.form("add_user"):
                username = st.text_input("نام کاربری")
                password = st.text_input("رمز", type="password")
                role = st.selectbox("نقش", ["مدیر", "سرپرست شیفت صبح", "سرپرست شیفت عصر", "سرپرست شیفت شب"])
                name = st.text_input("نام نمایشی")

                if st.form_submit_button("➕ افزودن"):
                    if username and password:
                        users = load_users()
                        if username in users:
                            st.error("❌ کاربر موجود است")
                        else:
                            users[username] = {'password': password, 'role': role, 'name': name}
                            save_users(users)
                            st.success(f"✅ {username} اضافه شد!")
                            st.rerun()

        st.markdown("### 📋 لیست کاربران")
        users = load_users()
        users_df = pd.DataFrame([
            {'نام کاربری': u, 'نام': i['name'], 'نقش': i['role']}
            for u, i in users.items()
        ])
        st.dataframe(users_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### 💾 پشتیبان‌گیری")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📥 دانلود")
            if st.button("💾 دانلود داده‌ها", use_container_width=True):
                df = load_production_data()
                if not df.empty:
                    backup = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    json_str = df.to_json(orient='records', force_ascii=False, indent=2)
                    st.download_button("📥 دانلود", json_str, backup, "application/json", use_container_width=True)

        with col2:
            st.markdown("#### 📤 بازیابی")
            uploaded = st.file_uploader("فایل JSON", type=['json'])
            if uploaded and st.button("♻️ بازیابی", use_container_width=True):
                try:
                    data = json.load(uploaded)
                    save_production_data(pd.DataFrame(data))
                    st.success("✅ بازیابی شد!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ خطا: {e}")


def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        with st.sidebar:
            st.markdown("### 🏭")
            st.markdown(f"### 👤 {st.session_state.user_display_name}")
            st.markdown(f"**نقش:** {st.session_state.user_role}")
            st.markdown("---")

            page = st.radio("📱 منو",
                            ["📊 داشبورد", "📝 ثبت اطلاعات", "📈 گزارش‌ها", "⚙️ تنظیمات"],
                            label_visibility="collapsed")

            st.markdown("---")

            df = load_production_data()
            if not df.empty:
                st.markdown("### 📊 آمار کلی")
                st.metric("📝 رکوردها", f"{len(df):,}")
                if 'تعداد_گونی' in df.columns:
                    st.metric("🎯 کل گونی", f"{df['تعداد_گونی'].sum():,}")

            st.markdown("---")

            if st.button("🚪 خروج", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.session_state.username = None
                st.session_state.user_display_name = None
                st.rerun()

        if page == "📊 داشبورد":
            dashboard_page()
        elif page == "📝 ثبت اطلاعات":
            data_entry_page()
        elif page == "📈 گزارش‌ها":
            reports_page()
        else:
            settings_page()


if __name__ == "__main__":
    main()