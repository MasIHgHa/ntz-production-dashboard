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

    /* اعمال فونت فارسی فقط به عناصر متنی معمول — اجازه بدید آیکون‌ها فونت خودشون رو نگه دارن */
    body, .stApp, .css-1d391kg, .css-1v3fvcr {
        font-family: 'Vazirmatn', sans-serif;
    }

    /* بازگرداندن فونت آیکون‌های Material (تا متن آیکون‌ها به glyph تبدیل بشه) */
    .material-icons, .material-icons-outlined, .material-icons-round, .material-icons-two-tone {
        font-family: "Material Icons" !important;
        speak: none;
        font-style: normal;
        font-weight: normal;
        font-variant: normal;
        text-transform: none;
        line-height: 1;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
    }

    /* نمونه استایل کارت‌ها و دکمه‌ها شما (بدون تغییر) */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-right: 4px solid #667eea;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_role' not in st.session_state:
    st.session_state.user_role = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'data' not in st.session_state:
    st.session_state.data = []

# Sample users database (in production, use proper database)
USERS = {
    'admin': {'password': 'admin123', 'role': 'مدیر', 'name': 'مدیر سیستم'},
    'shift_morning': {'password': 'shift123', 'role': 'سرپرست شیفت صبح', 'name': 'سرپرست صبح'},
    'shift_evening': {'password': 'shift123', 'role': 'سرپرست شیفت عصر', 'name': 'سرپرست عصر'},
    'shift_night': {'password': 'shift123', 'role': 'سرپرست شیفت شب', 'name': 'سرپرست شب'},
}

# Sample production data
def load_sample_data():
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    shifts = ['صبح', 'عصر', 'شب']
    machines = ['اکسترودر', 'بافندگی', 'دوخت و برش']
    shift_leaders = {
        'صبح': 'احمد رضایی',
        'عصر': 'محمد کریمی',
        'شب': 'علی محمدی'
    }

    data = []
    for date in dates:
        for shift in shifts:
            for machine in machines:
                record = {
                    'تاریخ': date.strftime('%Y/%m/%d'),
                    'شیفت': shift,
                    'سرپرست': shift_leaders[shift],
                    'دستگاه': machine,
                    'تعداد گونی': np.random.randint(500, 2000),
                    'عرض (cm)': np.random.choice([50, 60, 70, 80, 90]),
                    'طول (cm)': np.random.choice([80, 90, 100, 110, 120]),
                    'وزن کل (kg)': np.random.randint(1000, 5000),
                    'ضایعات (kg)': np.random.randint(50, 200),
                    'زمان توقف (دقیقه)': np.random.randint(0, 120),
                }
                data.append(record)

    return pd.DataFrame(data)

import numpy as np

# Login Page
def login_page():
    st.markdown("""
    <div class="main-header">
        <h1>🏭 سیستم مدیریت تولید</h1>
        <h2>شرکت نخ تابان زرین دست</h2>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown("### ورود به سیستم")
        username = st.text_input("نام کاربری", key="login_username")
        password = st.text_input("رمز عبور", type="password", key="login_password")

        if st.button("ورود", key="login_button"):
            if username in USERS and USERS[username]['password'] == password:
                st.session_state.logged_in = True
                st.session_state.user_role = USERS[username]['role']
                st.session_state.username = USERS[username]['name']
                st.rerun()
            else:
                st.error("نام کاربری یا رمز عبور اشتباه است")

        with st.expander("اطلاعات ورود نمونه"):
            st.info("""
            **مدیر:**
            - نام کاربری: admin
            - رمز عبور: admin123

            **سرپرست شیفت صبح:**
            - نام کاربری: shift_morning
            - رمز عبور: shift123

            **سرپرست شیفت عصر:**
            - نام کاربری: shift_evening
            - رمز عبور: shift123

            **سرپرست شیفت شب:**
            - نام کاربری: shift_night
            - رمز عبور: shift123
            """)

# Dashboard Page
def dashboard_page():
    # Load data
    df = load_sample_data()

    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>🏭 داشبورد مدیریتی</h1>
        <p>خوش آمدید {st.session_state.username} | نقش: {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)

    # Logout button in sidebar
    with st.sidebar:
        if st.button("خروج از سیستم"):
            st.session_state.logged_in = False
            st.session_state.user_role = None
            st.session_state.username = None
            st.rerun()

        st.markdown("---")
        date_filter = st.date_input(
            "انتخاب بازه زمانی",
            value=(datetime.now() - timedelta(days=7), datetime.now())
        )

        shift_filter = st.multiselect(
            "انتخاب شیفت",
            options=['صبح', 'عصر', 'شب'],
            default=['صبح', 'عصر', 'شب']
        )

        machine_filter = st.multiselect(
            "انتخاب دستگاه",
            options=['اکسترودر', 'بافندگی', 'دوخت و برش'],
            default=['اکسترودر', 'بافندگی', 'دوخت و برش']
        )

    # Filter data
    df_filtered = df[
        (df['شیفت'].isin(shift_filter)) &
        (df['دستگاه'].isin(machine_filter))
    ]

    # Key Metrics
    st.markdown("## 📊 شاخص‌های کلیدی")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_sacks = df_filtered['تعداد گونی'].sum()
        st.metric("تعداد کل گونی تولیدی", f"{total_sacks:,}")

    with col2:
        total_weight = df_filtered['وزن کل (kg)'].sum()
        st.metric("وزن کل تولید (کیلوگرم)", f"{total_weight:,}")

    with col3:
        total_waste = df_filtered['ضایعات (kg)'].sum()
        waste_percent = (total_waste / total_weight * 100) if total_weight > 0 else 0
        st.metric("ضایعات کل", f"{total_waste:,} kg", f"{waste_percent:.1f}%")

    with col4:
        total_downtime = df_filtered['زمان توقف (دقیقه)'].sum()
        avg_downtime = df_filtered['زمان توقف (دقیقه)'].mean()
        st.metric("زمان توقف کل (دقیقه)", f"{total_downtime:,}", f"میانگین: {avg_downtime:.0f}")

    st.markdown("---")

    # Charts Row 1
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 📈 تولید به تفکیک شیفت")
        shift_production = df_filtered.groupby('شیفت')['تعداد گونی'].sum().reset_index()
        fig1 = px.bar(
            shift_production,
            x='شیفت',
            y='تعداد گونی',
            color='شیفت',
            title='مقایسه تولید شیفت‌ها',
            color_discrete_map={'صبح': '#FF6B6B', 'عصر': '#4ECDC4', 'شب': '#45B7D1'}
        )
        fig1.update_layout(showlegend=False)
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.markdown("### 🏭 تولید به تفکیک دستگاه")
        machine_production = df_filtered.groupby('دستگاه')['تعداد گونی'].sum().reset_index()
        fig2 = px.pie(
            machine_production,
            values='تعداد گونی',
            names='دستگاه',
            title='توزیع تولید بین دستگاه‌ها',
            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb']
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Charts Row 2
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 👥 عملکرد سرپرستان")
        leader_performance = df_filtered.groupby('سرپرست').agg({
            'تعداد گونی': 'sum',
            'وزن کل (kg)': 'sum',
            'ضایعات (kg)': 'sum'
        }).reset_index()
        leader_performance['راندمان (%)'] = (
            (leader_performance['وزن کل (kg)'] - leader_performance['ضایعات (kg)']) /
            leader_performance['وزن کل (kg)'] * 100
        )

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            name='تعداد گونی',
            x=leader_performance['سرپرست'],
            y=leader_performance['تعداد گونی'],
            marker_color='#667eea'
        ))
        fig3.update_layout(
            title='مقایسه عملکرد سرپرستان',
            xaxis_title='سرپرست',
            yaxis_title='تعداد گونی'
        )
        st.plotly_chart(fig3, use_container_width=True)

    with col2:
        st.markdown("### 📏 توزیع ابعاد گونی‌ها")
        dimensions = df_filtered.groupby(['عرض (cm)', 'طول (cm)']).size().reset_index(name='تعداد')
        dimensions['ابعاد'] = dimensions['عرض (cm)'].astype(str) + 'x' + dimensions['طول (cm)'].astype(str)

        fig4 = px.bar(
            dimensions.nlargest(10, 'تعداد'),
            x='ابعاد',
            y='تعداد',
            title='محبوب‌ترین ابعاد گونی‌ها',
            color='تعداد',
            color_continuous_scale='Viridis'
        )
        st.plotly_chart(fig4, use_container_width=True)

    # Trend Chart
    st.markdown("### 📉 روند تولید در طول زمان")
    daily_production = df_filtered.groupby('تاریخ')['تعداد گونی'].sum().reset_index()
    fig5 = px.line(
        daily_production,
        x='تاریخ',
        y='تعداد گونی',
        title='روند روزانه تولید',
        markers=True
    )
    fig5.update_traces(line_color='#667eea', line_width=3)
    st.plotly_chart(fig5, use_container_width=True)

    # Detailed Table
    st.markdown("### 📋 جزئیات تولید")
    st.dataframe(
        df_filtered.sort_values('تاریخ', ascending=False).head(50),
        use_container_width=True
    )

# Data Entry Page
def data_entry_page():
    st.markdown(f"""
    <div class="main-header">
        <h1>📝 ثبت اطلاعات تولید</h1>
        <p>{st.session_state.username} | {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        if st.button("بازگشت به داشبورد"):
            st.rerun()

    tab1, tab2, tab3 = st.tabs(["🔧 اکسترودر", "🧵 بافندگی", "✂️ دوخت و برش"])

    with tab1:
        st.markdown("### ثبت اطلاعات دستگاه اکسترودر")
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("تاریخ", datetime.now())
            shift = st.selectbox("شیفت کاری", ["صبح", "عصر", "شب"])
            operator = st.text_input("نام اپراتور")

        with col2:
            production_kg = st.number_input("تولید (کیلوگرم)", min_value=0, value=1000)
            waste_kg = st.number_input("ضایعات (کیلوگرم)", min_value=0, value=50)
            downtime = st.number_input("زمان توقف (دقیقه)", min_value=0, value=0)

        notes = st.text_area("توضیحات")

        if st.button("ثبت اطلاعات اکسترودر"):
            st.success("✅ اطلاعات با موفقیت ثبت شد!")

    with tab2:
        st.markdown("### ثبت اطلاعات دستگاه بافندگی")
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("تاریخ", datetime.now(), key="knit_date")
            shift = st.selectbox("شیفت کاری", ["صبح", "عصر", "شب"], key="knit_shift")
            width = st.number_input("عرض (سانتی‌متر)", min_value=0, value=70)
            length = st.number_input("طول (سانتی‌متر)", min_value=0, value=100)

        with col2:
            sacks_count = st.number_input("تعداد گونی", min_value=0, value=500)
            weight = st.number_input("وزن (کیلوگرم)", min_value=0, value=2000)
            defects = st.number_input("تعداد معیوب", min_value=0, value=0)

        notes = st.text_area("توضیحات", key="knit_notes")

        if st.button("ثبت اطلاعات بافندگی"):
            st.success("✅ اطلاعات با موفقیت ثبت شد!")

    with tab3:
        st.markdown("### ثبت اطلاعات دوخت و برش")
        col1, col2 = st.columns(2)

        with col1:
            date = st.date_input("تاریخ", datetime.now(), key="sew_date")
            shift = st.selectbox("شیفت کاری", ["صبح", "عصر", "شب"], key="sew_shift")
            sack_type = st.selectbox("نوع گونی", ["تک‌لایه", "دو لایه", "لمینت"])
            width = st.number_input("عرض (سانتی‌متر)", min_value=0, value=50, key="sew_width")

        with col2:
            length = st.number_input("طول (سانتی‌متر)", min_value=0, value=80, key="sew_length")
            quantity = st.number_input("تعداد تولید", min_value=0, value=1000)
            defects = st.number_input("تعداد معیوب", min_value=0, value=0, key="sew_defects")

        quality_check = st.checkbox("کنترل کیفی انجام شده")
        notes = st.text_area("توضیحات", key="sew_notes")

        if st.button("ثبت اطلاعات دوخت و برش"):
            st.success("✅ اطلاعات با موفقیت ثبت شد!")

# Main App Logic
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar Navigation
        with st.sidebar:
            st.markdown(f"### سلام {st.session_state.username}")
            st.markdown(f"**نقش:** {st.session_state.user_role}")
            st.markdown("---")

            page = st.radio(
                "منوی اصلی",
                ["📊 داشبورد", "📝 ثبت اطلاعات", "📈 گزارش‌ها", "⚙️ تنظیمات"]
            )

        if page == "📊 داشبورد":
            dashboard_page()
        elif page == "📝 ثبت اطلاعات":
            data_entry_page()
        elif page == "📈 گزارش‌ها":
            st.markdown("""
            <div class="main-header">
                <h1>📈 گزارش‌های تحلیلی</h1>
            </div>
            """, unsafe_allow_html=True)
            st.info("این بخش در حال توسعه است...")
        else:
            st.markdown("""
            <div class="main-header">
                <h1>⚙️ تنظیمات سیستم</h1>
            </div>
            """, unsafe_allow_html=True)
            st.info("این بخش در حال توسعه است...")

if __name__ == "__main__":
    main()