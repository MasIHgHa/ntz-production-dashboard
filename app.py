import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import numpy as np

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

    /* Move sidebar to right */
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

    .stApp {
        direction: rtl;
        text-align: right;
    }

    /* Style improvements */
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

    .main-header p {
        font-size: 1.1rem;
        opacity: 0.95;
    }

    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-right: 5px solid #667eea;
        transition: transform 0.2s;
    }

    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }

    .stButton>button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 8px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(102, 126, 234, 0.4);
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f8f9ff 0%, #ffffff 100%);
    }

    /* DataFrames RTL */
    .dataframe {
        direction: rtl;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        direction: rtl;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 12px 24px;
        font-weight: 600;
    }

    /* Success/Error messages RTL */
    .stAlert {
        direction: rtl;
        text-align: right;
    }
</style>
""", unsafe_allow_html=True)

# Data persistence directory
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


# Load/Save functions for data persistence
def load_users():
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Default users
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


# Load users
USERS = load_users()


# Login Page
def login_page():
    # Logo section
    col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
    with col_logo2:
        # Try to load logo if exists
        logo_path = Path("logo.png")
        if logo_path.exists():
            st.image(str(logo_path), width=200)
        else:
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
        password = st.text_input("🔒 رمز عبور", type="password", key="login_password")

        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("✅ ورود", key="login_button", use_container_width=True):
                if username in USERS and USERS[username]['password'] == password:
                    st.session_state.logged_in = True
                    st.session_state.user_role = USERS[username]['role']
                    st.session_state.user_display_name = USERS[username]['name']
                    st.session_state.username = username
                    st.success("✅ ورود موفقیت‌آمیز! در حال انتقال...")
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


# Dashboard Page
def dashboard_page():
    df = load_production_data()

    # Header with logo
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        logo_path = Path("logo.png")
        if logo_path.exists():
            st.image(str(logo_path), width=100)

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

    # Convert date column
    if 'تاریخ' in df.columns:
        df['تاریخ'] = pd.to_datetime(df['تاریخ'])

    # Sidebar Filters - ENHANCED
    with st.sidebar:
        st.markdown("### 🔍 فیلترهای پیشرفته")

        # Time period selector
        time_period = st.selectbox(
            "📅 بازه زمانی",
            ["امروز", "هفته جاری", "ماه جاری", "7 روز گذشته", "30 روز گذشته",
             "90 روز گذشته", "سال جاری", "بازه دلخواه"],
            index=4
        )

        # Custom date range
        if time_period == "بازه دلخواه":
            start_date = st.date_input("از تاریخ", datetime.now() - timedelta(days=30))
            end_date = st.date_input("تا تاریخ", datetime.now())
        else:
            end_date = datetime.now()
            if time_period == "امروز":
                start_date = datetime.now()
            elif time_period == "هفته جاری":
                start_date = datetime.now() - timedelta(days=datetime.now().weekday())
            elif time_period == "ماه جاری":
                start_date = datetime.now().replace(day=1)
            elif time_period == "7 روز گذشته":
                start_date = datetime.now() - timedelta(days=7)
            elif time_period == "30 روز گذشته":
                start_date = datetime.now() - timedelta(days=30)
            elif time_period == "90 روز گذشته":
                start_date = datetime.now() - timedelta(days=90)
            elif time_period == "سال جاری":
                start_date = datetime.now().replace(month=1, day=1)

        shift_filter = st.multiselect(
            "⏰ انتخاب شیفت",
            options=['صبح', 'عصر', 'شب'],
            default=['صبح', 'عصر', 'شب']
        )

        machine_filter = st.multiselect(
            "🏭 انتخاب دستگاه",
            options=['اکسترودر', 'بافندگی', 'دوخت و برش'],
            default=['اکسترودر', 'بافندگی', 'دوخت و برش']
        )

        # Supervisor filter
        if 'سرپرست' in df.columns:
            supervisors = df['سرپرست'].unique().tolist()
            supervisor_filter = st.multiselect(
                "👥 انتخاب سرپرست",
                options=supervisors,
                default=supervisors
            )

        st.markdown("---")
        if st.button("🔄 بروزرسانی داده‌ها", use_container_width=True):
            st.rerun()

    # Apply filters
    df_filtered = df.copy()
    if 'تاریخ' in df.columns:
        df_filtered = df_filtered[
            (df_filtered['تاریخ'] >= pd.to_datetime(start_date)) &
            (df_filtered['تاریخ'] <= pd.to_datetime(end_date))
            ]
    if 'شیفت' in df.columns:
        df_filtered = df_filtered[df_filtered['شیفت'].isin(shift_filter)]
    if 'دستگاه' in df.columns:
        df_filtered = df_filtered[df_filtered['دستگاه'].isin(machine_filter)]
    if 'سرپرست' in df.columns and 'supervisor_filter' in locals():
        df_filtered = df_filtered[df_filtered['سرپرست'].isin(supervisor_filter)]

    if df_filtered.empty:
        st.warning("⚠️ با فیلترهای انتخاب شده، داده‌ای یافت نشد.")
        return

    # === SECTION 1: KEY METRICS WITH COMPARISON ===
    st.markdown("## 📈 شاخص‌های کلیدی")

    # Calculate previous period for comparison
    days_diff = (end_date - start_date).days
    prev_start = start_date - timedelta(days=days_diff)
    prev_end = start_date

    df_previous = df[
        (df['تاریخ'] >= pd.to_datetime(prev_start)) &
        (df['تاریخ'] < pd.to_datetime(prev_end))
        ]

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        total_sacks = df_filtered['تعداد_گونی'].sum() if 'تعداد_گونی' in df_filtered.columns else 0
        prev_sacks = df_previous['تعداد_گونی'].sum() if 'تعداد_گونی' in df_previous.columns else 0
        delta_sacks = total_sacks - prev_sacks
        st.metric("🎯 تعداد گونی", f"{total_sacks:,}", f"{delta_sacks:+,}")

    with col2:
        total_weight = df_filtered['وزن_کل'].sum() if 'وزن_کل' in df_filtered.columns else 0
        prev_weight = df_previous['وزن_کل'].sum() if 'وزن_کل' in df_previous.columns else 0
        delta_weight = total_weight - prev_weight
        st.metric("⚖️ وزن کل (kg)", f"{total_weight:,.0f}", f"{delta_weight:+,.0f}")

    with col3:
        total_waste = df_filtered['ضایعات'].sum() if 'ضایعات' in df_filtered.columns else 0
        waste_percent = (total_waste / total_weight * 100) if total_weight > 0 else 0
        st.metric("♻️ ضایعات", f"{total_waste:,.0f} kg", f"{waste_percent:.1f}%")

    with col4:
        efficiency = ((total_weight - total_waste) / total_weight * 100) if total_weight > 0 else 0
        st.metric("✅ راندمان", f"{efficiency:.1f}%")

    with col5:
        avg_daily = total_sacks / max(days_diff, 1)
        st.metric("📊 میانگین روزانه", f"{avg_daily:,.0f}")

    st.markdown("---")

    # === SECTION 2: MACHINE PERFORMANCE PIE CHARTS ===
    st.markdown("## 🏭 سهم تولید دستگاه‌ها")

    col1, col2 = st.columns(2)

    with col1:
        if 'دستگاه' in df_filtered.columns and 'تعداد_گونی' in df_filtered.columns:
            st.markdown("### 📊 بر اساس تعداد گونی")
            machine_data = df_filtered.groupby('دستگاه')['تعداد_گونی'].sum().reset_index()
            machine_data['درصد'] = (machine_data['تعداد_گونی'] / machine_data['تعداد_گونی'].sum() * 100).round(1)

            fig1 = px.pie(
                machine_data,
                values='تعداد_گونی',
                names='دستگاه',
                hole=0.5,
                color_discrete_sequence=['#667eea', '#764ba2', '#f093fb']
            )
            fig1.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>تعداد: %{value:,}<br>درصد: %{percent}<extra></extra>'
            )
            fig1.update_layout(height=400, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        if 'دستگاه' in df_filtered.columns and 'وزن_کل' in df_filtered.columns:
            st.markdown("### ⚖️ بر اساس وزن تولید")
            machine_weight = df_filtered.groupby('دستگاه')['وزن_کل'].sum().reset_index()

            fig2 = px.pie(
                machine_weight,
                values='وزن_کل',
                names='دستگاه',
                hole=0.5,
                color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
            )
            fig2.update_traces(
                textposition='inside',
                textinfo='percent+label',
                hovertemplate='<b>%{label}</b><br>وزن: %{value:,.0f} kg<br>درصد: %{percent}<extra></extra>'
            )
            fig2.update_layout(height=400, showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # === SECTION 3: SUPERVISOR PERFORMANCE BAR CHART ===
    if 'سرپرست' in df_filtered.columns:
        st.markdown("## 👥 مقایسه عملکرد سرپرستان")

        supervisor_data = df_filtered.groupby('سرپرست').agg({
            'تعداد_گونی': 'sum',
            'وزن_کل': 'sum',
            'ضایعات': 'sum'
        }).reset_index()

        supervisor_data['راندمان (%)'] = (
                (supervisor_data['وزن_کل'] - supervisor_data['ضایعات']) /
                supervisor_data['وزن_کل'] * 100
        ).round(1)

        supervisor_data = supervisor_data.sort_values('تعداد_گونی', ascending=False)

        fig3 = go.Figure()

        fig3.add_trace(go.Bar(
            name='تعداد گونی',
            x=supervisor_data['سرپرست'],
            y=supervisor_data['تعداد_گونی'],
            marker_color='#667eea',
            text=supervisor_data['تعداد_گونی'],
            texttemplate='%{text:,.0f}',
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>تعداد گونی: %{y:,}<extra></extra>'
        ))

        fig3.add_trace(go.Scatter(
            name='راندمان (%)',
            x=supervisor_data['سرپرست'],
            y=supervisor_data['راندمان (%)'],
            mode='lines+markers+text',
            yaxis='y2',
            marker=dict(size=12, color='#FF6B6B'),
            line=dict(width=3, color='#FF6B6B'),
            text=supervisor_data['راندمان (%)'].apply(lambda x: f'{x:.1f}%'),
            textposition='top center',
            hovertemplate='<b>%{x}</b><br>راندمان: %{y:.1f}%<extra></extra>'
        ))

        fig3.update_layout(
            title='مقایسه تعداد تولید و راندمان سرپرستان',
            xaxis_title='سرپرست',
            yaxis_title='تعداد گونی',
            yaxis2=dict(
                title='راندمان (%)',
                overlaying='y',
                side='left',
                range=[0, 100]
            ),
            height=500,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("---")

    # === SECTION 4: WIDTH DISTRIBUTION ===
    if 'عرض' in df_filtered.columns:
        st.markdown("## 📏 توزیع عرض‌های تولید شده")

        col1, col2 = st.columns([2, 1])

        with col1:
            width_data = df_filtered.groupby('عرض').agg({
                'تعداد_گونی': 'sum'
            }).reset_index()
            width_data = width_data[width_data['عرض'] > 0]  # Remove zeros
            width_data = width_data.sort_values('تعداد_گونی', ascending=False)

            fig4 = px.bar(
                width_data,
                x='عرض',
                y='تعداد_گونی',
                color='تعداد_گونی',
                color_continuous_scale='Viridis',
                text='تعداد_گونی',
                title='عرض‌های پرتولید'
            )
            fig4.update_traces(
                texttemplate='%{text:,.0f}',
                textposition='outside',
                hovertemplate='<b>عرض: %{x} cm</b><br>تعداد: %{y:,}<extra></extra>'
            )
            fig4.update_layout(height=400, xaxis_title='عرض (سانتی‌متر)', yaxis_title='تعداد گونی')
            st.plotly_chart(fig4, use_container_width=True)

        with col2:
            st.markdown("### 🏆 برترین عرض‌ها")
            top_widths = width_data.head(5)
            for idx, row in top_widths.iterrows():
                st.metric(
                    f"#{list(top_widths.index).index(idx) + 1} - عرض {int(row['عرض'])} cm",
                    f"{int(row['تعداد_گونی']):,} عدد"
                )

        st.markdown("---")

    # === SECTION 5: TIMELINE CHARTS (Production + Waste) ===
    st.markdown("## 📉 تحلیل زمانی تولید و ضایعات")

    if 'تاریخ' in df_filtered.columns:
        # Daily aggregation
        daily_data = df_filtered.groupby('تاریخ').agg({
            'تعداد_گونی': 'sum',
            'وزن_کل': 'sum',
            'ضایعات': 'sum'
        }).reset_index()
        daily_data = daily_data.sort_values('تاریخ')
        daily_data['راندمان (%)'] = (
                (daily_data['وزن_کل'] - daily_data['ضایعات']) / daily_data['وزن_کل'] * 100
        ).round(1)

        # Create dual-axis timeline
        fig5 = go.Figure()

        # Production line
        fig5.add_trace(go.Scatter(
            x=daily_data['تاریخ'],
            y=daily_data['تعداد_گونی'],
            mode='lines+markers',
            name='تعداد گونی',
            line=dict(color='#667eea', width=3),
            marker=dict(size=8),
            fill='tozeroy',
            fillcolor='rgba(102, 126, 234, 0.1)',
            hovertemplate='<b>تاریخ: %{x}</b><br>تعداد: %{y:,}<extra></extra>'
        ))

        # Weight line
        fig5.add_trace(go.Scatter(
            x=daily_data['تاریخ'],
            y=daily_data['وزن_کل'],
            mode='lines+markers',
            name='وزن کل (kg)',
            yaxis='y2',
            line=dict(color='#4ECDC4', width=3),
            marker=dict(size=8),
            hovertemplate='<b>تاریخ: %{x}</b><br>وزن: %{y:,.0f} kg<extra></extra>'
        ))

        # Waste line
        fig5.add_trace(go.Scatter(
            x=daily_data['تاریخ'],
            y=daily_data['ضایعات'],
            mode='lines+markers',
            name='ضایعات (kg)',
            yaxis='y2',
            line=dict(color='#FF6B6B', width=2, dash='dash'),
            marker=dict(size=6),
            hovertemplate='<b>تاریخ: %{x}</b><br>ضایعات: %{y:,.0f} kg<extra></extra>'
        ))

        fig5.update_layout(
            title='روند زمانی تولید، متراژ و ضایعات',
            xaxis_title='تاریخ',
            yaxis_title='تعداد گونی',
            yaxis2=dict(
                title='وزن (کیلوگرم)',
                overlaying='y',
                side='left'
            ),
            height=500,
            hovermode='x unified',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )

        st.plotly_chart(fig5, use_container_width=True)

        st.markdown("---")

    # === SECTION 6: SHIFT COMPARISON HEATMAP ===
    if 'شیفت' in df_filtered.columns and 'تاریخ' in df_filtered.columns:
        st.markdown("## 🔥 نقشه حرارتی عملکرد شیفت‌ها")

        # Create pivot table
        heatmap_data = df_filtered.pivot_table(
            values='تعداد_گونی',
            index='شیفت',
            columns=df_filtered['تاریخ'].dt.date,
            aggfunc='sum',
            fill_value=0
        )

        fig6 = go.Figure(data=go.Heatmap(
            z=heatmap_data.values,
            x=heatmap_data.columns,
            y=heatmap_data.index,
            colorscale='RdYlGn',
            text=heatmap_data.values,
            texttemplate='%{text:,.0f}',
            textfont={"size": 10},
            hovertemplate='<b>تاریخ: %{x}</b><br>شیفت: %{y}<br>تعداد: %{z:,}<extra></extra>'
        ))

        fig6.update_layout(
            title='مقایسه عملکرد شیفت‌ها در طول زمان',
            xaxis_title='تاریخ',
            yaxis_title='شیفت',
            height=300
        )

        st.plotly_chart(fig6, use_container_width=True)

        st.markdown("---")

    # === SECTION 7: SUMMARY TABLE ===
    st.markdown("## 📋 جدول خلاصه آماری")

    col1, col2 = st.columns(2)

    with col1:
        if 'دستگاه' in df_filtered.columns:
            st.markdown("### 🏭 آمار دستگاه‌ها")
            machine_summary = df_filtered.groupby('دستگاه').agg({
                'تعداد_گونی': ['sum', 'mean', 'max'],
                'وزن_کل': 'sum',
                'ضایعات': 'sum'
            }).round(0)
            machine_summary.columns = ['جمع', 'میانگین', 'بیشترین', 'وزن کل', 'ضایعات']
            st.dataframe(machine_summary, use_container_width=True)

    with col2:
        if 'شیفت' in df_filtered.columns:
            st.markdown("### ⏰ آمار شیفت‌ها")
            shift_summary = df_filtered.groupby('شیفت').agg({
                'تعداد_گونی': ['sum', 'mean', 'max'],
                'وزن_کل': 'sum',
                'ضایعات': 'sum'
            }).round(0)
            shift_summary.columns = ['جمع', 'میانگین', 'بیشترین', 'وزن کل', 'ضایعات']
            st.dataframe(shift_summary, use_container_width=True)


# Data Entry Page
def data_entry_page():
    st.markdown(f"""
    <div class="main-header">
        <h1>📝 ثبت اطلاعات جدید</h1>
        <p>{st.session_state.user_display_name} | {st.session_state.user_role}</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🔧 اکسترودر", "🧵 بافندگی", "✂️ دوخت و برش"])

    with tab1:
        st.markdown("### ثبت گزارش دستگاه اکسترودر")
        with st.form("extruder_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("📅 تاریخ", datetime.now())
                shift = st.selectbox("⏰ شیفت کاری", ["صبح", "عصر", "شب"])
                operator = st.text_input("👤 نام اپراتور")

            with col2:
                production_kg = st.number_input("⚖️ تولید (کیلوگرم)", min_value=0, value=1000, step=100)
                waste_kg = st.number_input("♻️ ضایعات (کیلوگرم)", min_value=0, value=0, step=10)
                downtime = st.number_input("⏱️ زمان توقف (دقیقه)", min_value=0, value=0)

            notes = st.text_area("📝 توضیحات و یادداشت")

            submitted = st.form_submit_button("💾 ثبت اطلاعات", use_container_width=True)

            if submitted:
                record = {
                    'تاریخ': date.strftime('%Y-%m-%d'),
                    'شیفت': shift,
                    'سرپرست': st.session_state.user_display_name,
                    'دستگاه': 'اکسترودر',
                    'اپراتور': operator,
                    'تعداد_گونی': 0,
                    'عرض': 0,
                    'طول': 0,
                    'وزن_کل': production_kg,
                    'ضایعات': waste_kg,
                    'زمان_توقف': downtime,
                    'توضیحات': notes,
                    'ثبت_کننده': st.session_state.username
                }
                add_production_record(record)
                st.success("✅ اطلاعات با موفقیت ثبت شد!")
                st.balloons()

    with tab2:
        st.markdown("### ثبت گزارش دستگاه بافندگی")
        with st.form("knitting_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("📅 تاریخ", datetime.now(), key="knit_date")
                shift = st.selectbox("⏰ شیفت کاری", ["صبح", "عصر", "شب"], key="knit_shift")
                operator_name = st.text_input("👤 نام اپراتور / سرشیفت", value="", placeholder="مثال: احمد رضایی")
                width = st.number_input("📏 عرض گونی (سانتی‌متر)", min_value=0, value=70, step=5)
                length = st.number_input("📐 طول گونی (سانتی‌متر)", min_value=0, value=100, step=5)

            with col2:
                sacks_count = st.number_input("🎯 تعداد گونی", min_value=0, value=500, step=50)
                weight = st.number_input("⚖️ وزن کل (کیلوگرم)", min_value=0, value=2000, step=100)
                defects = st.number_input("❌ تعداد معیوب", min_value=0, value=0)
                downtime = st.number_input("⏱️ زمان توقف (دقیقه)", min_value=0, value=0, key="knit_downtime")

            notes = st.text_area("📝 توضیحات", key="knit_notes")

            submitted = st.form_submit_button("💾 ثبت اطلاعات", use_container_width=True)

            if submitted:
                if not operator_name.strip():
                    st.error("❌ لطفاً نام اپراتور را وارد کنید")
                else:
                    record = {
                        'تاریخ': date.strftime('%Y-%m-%d'),
                        'شیفت': shift,
                        'اپراتور': operator_name.strip(),
                        'سرپرست': st.session_state.user_display_name,
                        'دستگاه': 'بافندگی',
                        'تعداد_گونی': sacks_count,
                        'عرض': width,
                        'طول': length,
                        'وزن_کل': weight,
                        'ضایعات': 0,
                        'تعداد_معیوب': defects,
                        'زمان_توقف': downtime,
                        'توضیحات': notes,
                        'ثبت_کننده': st.session_state.username
                    }
                    add_production_record(record)
                    st.success(f"✅ اطلاعات {operator_name} با موفقیت ثبت شد!")
                    st.balloons()

    with tab3:
        st.markdown("### ثبت گزارش دوخت و برش")
        with st.form("sewing_form", clear_on_submit=True):
            col1, col2 = st.columns(2)

            with col1:
                date = st.date_input("📅 تاریخ", datetime.now(), key="sew_date")
                shift = st.selectbox("⏰ شیفت کاری", ["صبح", "عصر", "شب"], key="sew_shift")
                sack_type = st.selectbox("📦 نوع گونی", ["تک‌لایه", "دولایه", "لمینت"])
                width = st.number_input("📏 عرض (سانتی‌متر)", min_value=0, value=50, step=5, key="sew_width")

            with col2:
                length = st.number_input("📐 طول (سانتی‌متر)", min_value=0, value=80, step=5, key="sew_length")
                quantity = st.number_input("🎯 تعداد تولید", min_value=0, value=1000, step=100)
                defects = st.number_input("❌ تعداد معیوب", min_value=0, value=0, key="sew_defects")
                downtime = st.number_input("⏱️ زمان توقف (دقیقه)", min_value=0, value=0, key="sew_downtime")

            quality_check = st.checkbox("✅ کنترل کیفی انجام شده")
            notes = st.text_area("📝 توضیحات", key="sew_notes")

            submitted = st.form_submit_button("💾 ثبت اطلاعات", use_container_width=True)

            if submitted:
                record = {
                    'تاریخ': date.strftime('%Y-%m-%d'),
                    'شیفت': shift,
                    'سرپرست': st.session_state.user_display_name,
                    'دستگاه': 'دوخت و برش',
                    'نوع_گونی': sack_type,
                    'تعداد_گونی': quantity,
                    'عرض': width,
                    'طول': length,
                    'وزن_کل': 0,
                    'ضایعات': 0,
                    'تعداد_معیوب': defects,
                    'زمان_توقف': downtime,
                    'کنترل_کیفی': 'انجام شده' if quality_check else 'انجام نشده',
                    'توضیحات': notes,
                    'ثبت_کننده': st.session_state.username
                }
                add_production_record(record)
                st.success("✅ اطلاعات با موفقیت ثبت شد!")
                st.balloons()


# Reports Page - NOW COMPLETE!
def reports_page():
    st.markdown("""
    <div class="main-header">
        <h1>📈 گزارش‌های تحلیلی</h1>
        <p>مشاهده، ویرایش و مدیریت رکوردهای تولید</p>
    </div>
    """, unsafe_allow_html=True)

    df = load_production_data()

    if df.empty:
        st.warning("⚠️ هیچ داده‌ای برای نمایش وجود ندارد.")
        return

    # Tabs for different report views
    tab1, tab2, tab3 = st.tabs(["📋 همه رکوردها", "✏️ ویرایش/حذف", "📊 گزارش خلاصه"])

    with tab1:
        st.markdown("### 📋 لیست کامل رکوردهای ثبت شده")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_shift = st.multiselect(
                "فیلتر شیفت",
                options=df['شیفت'].unique().tolist() if 'شیفت' in df.columns else [],
                default=df['شیفت'].unique().tolist() if 'شیفت' in df.columns else []
            )
        with col2:
            filter_machine = st.multiselect(
                "فیلتر دستگاه",
                options=df['دستگاه'].unique().tolist() if 'دستگاه' in df.columns else [],
                default=df['دستگاه'].unique().tolist() if 'دستگاه' in df.columns else []
            )
        with col3:
            search = st.text_input("🔍 جستجو در توضیحات")

        # Apply filters
        df_filtered = df.copy()
        if filter_shift and 'شیفت' in df.columns:
            df_filtered = df_filtered[df_filtered['شیفت'].isin(filter_shift)]
        if filter_machine and 'دستگاه' in df.columns:
            df_filtered = df_filtered[df_filtered['دستگاه'].isin(filter_machine)]
        if search and 'توضیحات' in df.columns:
            df_filtered = df_filtered[df_filtered['توضیحات'].str.contains(search, na=False, case=False)]

        st.dataframe(df_filtered, use_container_width=True, height=500)

        # Export options
        st.markdown("### 📥 دانلود گزارش")
        col1, col2, col3 = st.columns(3)
        with col1:
            csv = df_filtered.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                "📄 دانلود CSV",
                csv,
                f"production_report_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv",
                use_container_width=True
            )
        with col2:
            excel_buffer = pd.io.excel.ExcelWriter('temp.xlsx', engine='openpyxl')
            df_filtered.to_excel(excel_buffer, index=False)
            excel_buffer.close()
            with open('temp.xlsx', 'rb') as f:
                st.download_button(
                    "📊 دانلود Excel",
                    f,
                    f"production_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                    "application/vnd.ms-excel",
                    use_container_width=True
                )

    with tab2:
        st.markdown("### ✏️ ویرایش یا حذف رکوردها")

        if 'شناسه' not in df.columns:
            st.error("ستون 'شناسه' در داده‌ها وجود ندارد.")
            return

        record_id = st.selectbox(
            "🔍 انتخاب شناسه رکورد",
            options=df['شناسه'].tolist(),
            format_func=lambda
                x: f"شناسه {x} - {df[df['شناسه'] == x]['تاریخ'].values[0]} - {df[df['شناسه'] == x]['دستگاه'].values[0]}"
        )

        if record_id:
            selected_record = df[df['شناسه'] == record_id].iloc[0].to_dict()

            st.info(f"📝 در حال ویرایش رکورد شماره: {record_id}")

            with st.form("edit_form"):
                col1, col2 = st.columns(2)

                with col1:
                    edit_date = st.date_input(
                        "📅 تاریخ",
                        value=datetime.strptime(selected_record['تاریخ'],
                                                '%Y-%m-%d') if 'تاریخ' in selected_record else datetime.now()
                    )
                    edit_shift = st.selectbox(
                        "⏰ شیفت",
                        ["صبح", "عصر", "شب"],
                        index=["صبح", "عصر", "شب"].index(selected_record['شیفت']) if 'شیفت' in selected_record else 0
                    )
                    edit_machine = st.selectbox(
                        "🏭 دستگاه",
                        ["اکسترودر", "بافندگی", "دوخت و برش"],
                        index=["اکسترودر", "بافندگی", "دوخت و برش"].index(
                            selected_record['دستگاه']) if 'دستگاه' in selected_record else 0
                    )

                with col2:
                    edit_sacks = st.number_input(
                        "🎯 تعداد گونی",
                        value=int(selected_record.get('تعداد_گونی', 0)),
                        min_value=0
                    )
                    edit_weight = st.number_input(
                        "⚖️ وزن کل (کیلوگرم)",
                        value=float(selected_record.get('وزن_کل', 0)),
                        min_value=0.0
                    )
                    edit_waste = st.number_input(
                        "♻️ ضایعات (کیلوگرم)",
                        value=float(selected_record.get('ضایعات', 0)),
                        min_value=0.0
                    )

                edit_notes = st.text_area(
                    "📝 توضیحات",
                    value=selected_record.get('توضیحات', '')
                )

                col_btn1, col_btn2 = st.columns(2)

                with col_btn1:
                    update_btn = st.form_submit_button("✅ بروزرسانی", use_container_width=True)

                with col_btn2:
                    delete_btn = st.form_submit_button("🗑️ حذف", use_container_width=True, type="secondary")

                if update_btn:
                    updated_record = {
                        'تاریخ': edit_date.strftime('%Y-%m-%d'),
                        'شیفت': edit_shift,
                        'دستگاه': edit_machine,
                        'تعداد_گونی': edit_sacks,
                        'وزن_کل': edit_weight,
                        'ضایعات': edit_waste,
                        'توضیحات': edit_notes
                    }
                    if update_production_record(record_id, updated_record):
                        st.success("✅ رکورد با موفقیت بروزرسانی شد!")
                        st.rerun()
                    else:
                        st.error("❌ خطا در بروزرسانی رکورد")

                if delete_btn:
                    if delete_production_record(record_id):
                        st.success("🗑️ رکورد با موفقیت حذف شد!")
                        st.rerun()
                    else:
                        st.error("❌ خطا در حذف رکورد")

    with tab3:
        st.markdown("### 📊 گزارش خلاصه و آمار")

        # Date range filter
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("📅 از تاریخ", datetime.now() - timedelta(days=30))
        with col2:
            end_date = st.date_input("📅 تا تاریخ", datetime.now())

        # Filter by date range
        df['تاریخ'] = pd.to_datetime(df['تاریخ'])
        df_period = df[(df['تاریخ'] >= pd.to_datetime(start_date)) & (df['تاریخ'] <= pd.to_datetime(end_date))]

        if df_period.empty:
            st.warning("⚠️ در بازه زمانی انتخاب شده داده‌ای وجود ندارد.")
            return

        # Summary statistics
        st.markdown("#### 📈 آمار کلی")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_records = len(df_period)
            st.metric("📝 تعداد رکوردها", f"{total_records:,}")

        with col2:
            total_sacks = df_period['تعداد_گونی'].sum() if 'تعداد_گونی' in df_period.columns else 0
            st.metric("🎯 کل گونی تولیدی", f"{total_sacks:,}")

        with col3:
            total_weight = df_period['وزن_کل'].sum() if 'وزن_کل' in df_period.columns else 0
            st.metric("⚖️ کل وزن (کیلوگرم)", f"{total_weight:,.0f}")

        with col4:
            total_waste = df_period['ضایعات'].sum() if 'ضایعات' in df_period.columns else 0
            efficiency = ((total_weight - total_waste) / total_weight * 100) if total_weight > 0 else 0
            st.metric("✅ راندمان", f"{efficiency:.1f}%")

        st.markdown("---")

        # Charts
        col1, col2 = st.columns(2)

        with col1:
            if 'دستگاه' in df_period.columns and 'تعداد_گونی' in df_period.columns:
                st.markdown("#### 🏭 تولید به تفکیک دستگاه")
                machine_summary = df_period.groupby('دستگاه')['تعداد_گونی'].sum().reset_index()
                fig = px.bar(
                    machine_summary,
                    x='دستگاه',
                    y='تعداد_گونی',
                    color='دستگاه',
                    text='تعداد_گونی'
                )
                fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            if 'شیفت' in df_period.columns and 'تعداد_گونی' in df_period.columns:
                st.markdown("#### ⏰ تولید به تفکیک شیفت")
                shift_summary = df_period.groupby('شیفت')['تعداد_گونی'].sum().reset_index()
                fig = px.pie(
                    shift_summary,
                    values='تعداد_گونی',
                    names='شیفت',
                    hole=0.4,
                    color_discrete_map={'صبح': '#FF6B6B', 'عصر': '#4ECDC4', 'شب': '#45B7D1'}
                )
                st.plotly_chart(fig, use_container_width=True)

        # Daily trend
        if 'تاریخ' in df_period.columns and 'تعداد_گونی' in df_period.columns:
            st.markdown("#### 📉 روند تولید روزانه")
            daily_trend = df_period.groupby('تاریخ')['تعداد_گونی'].sum().reset_index()
            daily_trend = daily_trend.sort_values('تاریخ')
            fig = px.line(
                daily_trend,
                x='تاریخ',
                y='تعداد_گونی',
                markers=True,
                line_shape='spline'
            )
            fig.update_traces(line_color='#667eea', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

        # Performance by supervisor
        if 'سرپرست' in df_period.columns:
            st.markdown("#### 👥 رتبه‌بندی سرپرستان")
            supervisor_perf = df_period.groupby('سرپرست').agg({
                'تعداد_گونی': 'sum',
                'وزن_کل': 'sum',
                'ضایعات': 'sum'
            }).reset_index()

            if 'وزن_کل' in supervisor_perf.columns and 'ضایعات' in supervisor_perf.columns:
                supervisor_perf['راندمان (%)'] = (
                        (supervisor_perf['وزن_کل'] - supervisor_perf['ضایعات']) /
                        supervisor_perf['وزن_کل'] * 100
                ).round(1)

            supervisor_perf = supervisor_perf.sort_values('تعداد_گونی', ascending=False)

            # Add ranking
            supervisor_perf.insert(0, 'رتبه', range(1, len(supervisor_perf) + 1))

            st.dataframe(
                supervisor_perf,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "رتبه": st.column_config.NumberColumn("🏆 رتبه", format="%d"),
                    "تعداد_گونی": st.column_config.NumberColumn("تعداد گونی", format="%d"),
                    "وزن_کل": st.column_config.NumberColumn("وزن کل", format="%.0f kg"),
                    "ضایعات": st.column_config.NumberColumn("ضایعات", format="%.0f kg"),
                    "راندمان (%)": st.column_config.ProgressColumn("راندمان", format="%.1f%%", min_value=0,
                                                                   max_value=100)
                }
            )


# Settings Page
def settings_page():
    st.markdown("""
    <div class="main-header">
        <h1>⚙️ تنظیمات سیستم</h1>
        <p>مدیریت کاربران و پیکربندی سیستم</p>
    </div>
    """, unsafe_allow_html=True)

    # Only admin can access settings
    if st.session_state.user_role != 'مدیر':
        st.error("⛔ شما دسترسی به این بخش را ندارید. فقط مدیر سیستم می‌تواند تنظیمات را تغییر دهد.")
        return

    tab1, tab2, tab3 = st.tabs(["👥 مدیریت کاربران", "💾 پشتیبان‌گیری", "🎨 ظاهر"])

    with tab1:
        st.markdown("### 👥 مدیریت کاربران")

        # Add new user
        with st.expander("➕ افزودن کاربر جدید"):
            with st.form("add_user_form"):
                new_username = st.text_input("نام کاربری")
                new_password = st.text_input("رمز عبور", type="password")
                new_role = st.selectbox("نقش", ["مدیر", "سرپرست شیفت صبح", "سرپرست شیفت عصر", "سرپرست شیفت شب"])
                new_name = st.text_input("نام نمایشی")

                if st.form_submit_button("➕ افزودن کاربر"):
                    if new_username and new_password:
                        users = load_users()
                        if new_username in users:
                            st.error("❌ این نام کاربری قبلاً وجود دارد")
                        else:
                            users[new_username] = {
                                'password': new_password,
                                'role': new_role,
                                'name': new_name
                            }
                            save_users(users)
                            st.success(f"✅ کاربر {new_username} با موفقیت اضافه شد!")
                            st.rerun()
                    else:
                        st.error("❌ لطفاً تمام فیلدها را پر کنید")

        # List existing users
        st.markdown("### 📋 لیست کاربران")
        users = load_users()
        users_df = pd.DataFrame([
            {
                'نام کاربری': username,
                'نام نمایشی': info['name'],
                'نقش': info['role']
            }
            for username, info in users.items()
        ])
        st.dataframe(users_df, use_container_width=True, hide_index=True)

    with tab2:
        st.markdown("### 💾 پشتیبان‌گیری و بازیابی")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### 📥 دانلود نسخه پشتیبان")
            if st.button("💾 دانلود تمام داده‌ها", use_container_width=True):
                df = load_production_data()
                if not df.empty:
                    backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    json_str = df.to_json(orient='records', force_ascii=False, indent=2)
                    st.download_button(
                        "📥 دانلود فایل JSON",
                        json_str,
                        backup_name,
                        "application/json",
                        use_container_width=True
                    )
                else:
                    st.warning("⚠️ داده‌ای برای پشتیبان‌گیری وجود ندارد")

        with col2:
            st.markdown("#### 📤 بازیابی از نسخه پشتیبان")
            uploaded_file = st.file_uploader("فایل JSON را انتخاب کنید", type=['json'])
            if uploaded_file:
                if st.button("♻️ بازیابی داده‌ها", use_container_width=True):
                    try:
                        backup_data = json.load(uploaded_file)
                        df_backup = pd.DataFrame(backup_data)
                        save_production_data(df_backup)
                        st.success("✅ داده‌ها با موفقیت بازیابی شدند!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ خطا در بازیابی: {str(e)}")

        st.markdown("---")
        st.markdown("#### ⚠️ پاک‌سازی داده‌ها")
        st.warning("⚠️ هشدار: این عملیات غیرقابل بازگشت است!")

        if st.button("🗑️ حذف تمام داده‌های تولید", type="secondary"):
            if st.checkbox("✅ مطمئنم که می‌خواهم تمام داده‌ها را حذف کنم"):
                save_production_data(pd.DataFrame())
                st.success("✅ تمام داده‌ها حذف شدند")
                st.rerun()

    with tab3:
        st.markdown("### 🎨 تنظیمات ظاهری")

        st.info("💡 برای تغییر لوگو، یک فایل تصویر با نام `logo.png` در کنار فایل `app.py` قرار دهید.")

        # Logo upload
        logo_file = st.file_uploader("📤 آپلود لوگو جدید", type=['png', 'jpg', 'jpeg'])
        if logo_file:
            if st.button("💾 ذخیره لوگو"):
                with open("logo.png", "wb") as f:
                    f.write(logo_file.getbuffer())
                st.success("✅ لوگو با موفقیت ذخیره شد! صفحه را رفرش کنید.")

        # Show current logo
        logo_path = Path("logo.png")
        if logo_path.exists():
            st.markdown("#### 🖼️ لوگو فعلی:")
            st.image(str(logo_path), width=200)


# Main App Logic
def main():
    if not st.session_state.logged_in:
        login_page()
    else:
        # Sidebar Navigation
        with st.sidebar:
            # Logo in sidebar
            logo_path = Path("logo.png")
            if logo_path.exists():
                st.image(str(logo_path), width=150)

            st.markdown(f"### 👤 {st.session_state.user_display_name}")
            st.markdown(f"**نقش:** {st.session_state.user_role}")
            st.markdown("---")

            page = st.radio(
                "📱 منوی اصلی",
                ["📊 داشبورد", "📝 ثبت اطلاعات", "📈 گزارش‌ها", "⚙️ تنظیمات"],
                label_visibility="collapsed"
            )

            st.markdown("---")

            # Statistics in sidebar
            df = load_production_data()
            if not df.empty:
                st.markdown("### 📊 آمار کلی")
                total_records = len(df)
                st.metric("📝 کل رکوردها", f"{total_records:,}")

                if 'تعداد_گونی' in df.columns:
                    total_sacks = df['تعداد_گونی'].sum()
                    st.metric("🎯 کل گونی", f"{total_sacks:,}")

            st.markdown("---")

            # Logout button
            if st.button("🚪 خروج از سیستم", use_container_width=True):
                st.session_state.logged_in = False
                st.session_state.user_role = None
                st.session_state.username = None
                st.session_state.user_display_name = None
                st.rerun()

        # Page routing
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
