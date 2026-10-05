"""
🏭 Cement Packing Management System - Complete Application
نظام إدارة منطقة التعبئة في مصنع الأسمنت - تطبيق متكامل
Version: 3.0 | Author: Qwen Coder
"""

import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from io import BytesIO
import random

# ============================================
# إعدادات الصفحة
# ============================================
st.set_page_config(
    page_title="🏭 نظام إدارة منطقة التعبئة",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# Custom CSS للتصميم الاحترافي
# ============================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&display=swap');
    
    * {
        font-family: 'Tajawal', sans-serif;
    }
    
    .main-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(30, 58, 138, 0.3);
    }
    
    .main-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 900;
    }
    
    .main-header p {
        margin: 0.5rem 0 0 0;
        opacity: 0.9;
        font-size: 1.1rem;
    }
    
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        border-left: 5px solid #3b82f6;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2.5rem;
        font-weight: 900;
        color: #1e3a8a;
        margin: 0.5rem 0;
    }
    
    .metric-label {
        color: #64748b;
        font-size: 1rem;
        font-weight: 500;
    }
    
    .metric-trend-up {
        color: #10b981;
        font-weight: 700;
    }
    
    .metric-trend-down {
        color: #ef4444;
        font-weight: 700;
    }
    
    .alert-card {
        background: white;
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        border-right: 5px solid;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .alert-high { border-right-color: #ef4444; }
    .alert-medium { border-right-color: #f59e0b; }
    .alert-low { border-right-color: #3b82f6; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #f8fafc;
        padding: 10px;
        border-radius: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white !important;
    }
    
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-success { background-color: #d1fae5; color: #065f46; }
    .status-warning { background-color: #fef3c7; color: #92400e; }
    .status-danger { background-color: #fee2e2; color: #991b1b; }
    .status-info { background-color: #dbeafe; color: #1e40af; }
</style>
""", unsafe_allow_html=True)

# ============================================
# Database Setup - SQLite مدمج
# ============================================
@st.cache_resource
def init_database():
    """تهيئة قاعدة البيانات مع بيانات تجريبية"""
    conn = sqlite3.connect('cement_factory.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # إنشاء الجداول
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS machines (
            machine_id INTEGER PRIMARY KEY,
            machine_name TEXT NOT NULL,
            machine_type TEXT,
            theoretical_speed INTEGER,
            location TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS shifts (
            shift_id INTEGER PRIMARY KEY,
            shift_date TEXT,
            start_time TEXT,
            end_time TEXT,
            shift_name TEXT,
            target_tonnage REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS production_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER,
            machine_id INTEGER,
            bag_type TEXT,
            total_bags INTEGER,
            good_bags INTEGER,
            rejected_bags INTEGER,
            spillage_kg REAL,
            recorded_at TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS downtime_logs (
            downtime_id INTEGER PRIMARY KEY AUTOINCREMENT,
            shift_id INTEGER,
            machine_id INTEGER,
            start_time TEXT,
            end_time TEXT,
            reason TEXT,
            is_breakdown INTEGER
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_schedule (
            schedule_id INTEGER PRIMARY KEY AUTOINCREMENT,
            machine_id INTEGER,
            maintenance_type TEXT,
            scheduled_date TEXT,
            status TEXT,
            assigned_to TEXT,
            cost REAL
        )
    ''')
    
    # التحقق من وجود بيانات
    cursor.execute("SELECT COUNT(*) FROM machines")
    if cursor.fetchone()[0] == 0:
        # إضافة الماكينات
        machines = [
            (1, 'Rotary Packer 1', 'Rotary', 3000, 'Packing Hall A'),
            (2, 'Rotary Packer 2', 'Rotary', 3000, 'Packing Hall A'),
            (3, 'Inline Packer 1', 'Inline', 2000, 'Packing Hall B'),
            (4, 'Jumbo Packer 1', 'Jumbo', 100, 'Packing Hall C'),
        ]
        cursor.executemany('INSERT INTO machines VALUES (?,?,?,?,?)', machines)
        
        # إضافة بيانات تجريبية (آخر 90 يوم)
        today = datetime.now()
        shift_id = 1
        
        for days_ago in range(90):
            date = today - timedelta(days=days_ago)
            date_str = date.strftime('%Y-%m-%d')
            
            # 3 ورديات في اليوم
            for shift_name, start_h, end_h in [
                ('Morning', 6, 14), ('Evening', 14, 22), ('Night', 22, 6)
            ]:
                cursor.execute('''
                    INSERT INTO shifts VALUES (?,?,?,?,?,?)
                ''', (shift_id, date_str, 
                      f"{date_str} {start_h:02d}:00:00",
                      f"{date_str} {end_h:02d}:00:00",
                      shift_name, 150.0))
                
                # سجلات إنتاج لكل ماكينة
                for machine_id, bag_type, base_bags in [
                    (1, '50kg', 2500), (2, '50kg', 2400),
                    (3, '25kg', 1800), (4, '1.5t_Jumbo', 120)
                ]:
                    # إضافة عشوائية واقعية
                    variation = random.uniform(0.85, 1.05)
                    total_bags = int(base_bags * variation)
                    rejection_rate = random.uniform(0.01, 0.04)
                    rejected = int(total_bags * rejection_rate)
                    good_bags = total_bags - rejected
                    spillage = random.uniform(50, 300)
                    
                    cursor.execute('''
                        INSERT INTO production_logs 
                        (shift_id, machine_id, bag_type, total_bags, good_bags, 
                         rejected_bags, spillage_kg, recorded_at)
                        VALUES (?,?,?,?,?,?,?,?)
                    ''', (shift_id, machine_id, bag_type, total_bags, good_bags,
                          rejected, spillage, datetime.now().isoformat()))
                
                # سجلات توقفات عشوائية
                if random.random() < 0.3:  # 30% احتمال توقف
                    machine_id = random.choice([1, 2, 3, 4])
                    start_h = random.randint(6, 20)
                    duration = random.randint(15, 120)
                    reasons = ['عطل ميكانيكي', 'عطل كهربائي', 'انتظار مادة', 
                              'تغيير منتج', 'صيانة دورية']
                    reason = random.choice(reasons)
                    is_breakdown = 1 if 'عطل' in reason else 0
                    
                    cursor.execute('''
                        INSERT INTO downtime_logs 
                        (shift_id, machine_id, start_time, end_time, reason, is_breakdown)
                        VALUES (?,?,?,?,?,?)
                    ''', (shift_id, machine_id, 
                          f"{date_str} {start_h:02d}:00:00",
                          f"{date_str} {start_h:02d}:{duration:02d}:00",
                          reason, is_breakdown))
                
                shift_id += 1
        
        # إضافة جدول صيانة
        maintenance_data = [
            (1, 'صيانة دورية', (today + timedelta(days=3)).strftime('%Y-%m-%d'), 
             'scheduled', 'أحمد محمد', 2500),
            (2, 'فحص شامل', (today + timedelta(days=7)).strftime('%Y-%m-%d'),
             'scheduled', 'خالد علي', 3200),
            (3, 'تغيير زيت', (today + timedelta(days=10)).strftime('%Y-%m-%d'),
             'scheduled', 'سعد عبدالله', 800),
            (4, 'صيانة وقائية', (today + timedelta(days=15)).strftime('%Y-%m-%d'),
             'scheduled', 'أحمد محمد', 1500),
        ]
        cursor.executemany('''
            INSERT INTO maintenance_schedule 
            (machine_id, maintenance_type, scheduled_date, status, assigned_to, cost)
            VALUES (?,?,?,?,?,?)
        ''', maintenance_data)
    
    conn.commit()
    return conn

# ============================================
# Helper Functions
# ============================================
def get_db():
    """الحصول على اتصال قاعدة البيانات"""
    return init_database()

def run_query(query, params=None):
    """تنفيذ استعلام SQL"""
    conn = get_db()
    if params:
        return pd.read_sql_query(query, conn, params=params)
    return pd.read_sql_query(query, conn)

def calculate_oee(df_production, df_downtime, planned_minutes=480, theoretical_speed=3000):
    """حساب OEE"""
    if df_production.empty:
        return {'availability': 0, 'performance': 0, 'quality': 0, 'oee': 0}
    
    # Availability
    total_downtime = 0
    if not df_downtime.empty:
        # حساب وقت التوقف
        total_downtime = len(df_downtime) * 30  # متوسط 30 دقيقة لكل توقف
    
    run_time = planned_minutes - total_downtime
    availability = (run_time / planned_minutes * 100) if planned_minutes > 0 else 0
    
    # Performance
    total_bags = df_production['total_bags'].sum()
    theoretical_max = (run_time / 60) * theoretical_speed
    performance = (total_bags / theoretical_max * 100) if theoretical_max > 0 else 0
    
    # Quality
    good_bags = df_production['good_bags'].sum()
    quality = (good_bags / total_bags * 100) if total_bags > 0 else 0
    
    # OEE
    oee = (availability * performance * quality) / 100
    
    return {
        'availability': round(availability, 2),
        'performance': min(performance, 100),
        'quality': round(quality, 2),
        'oee': round(oee, 2)
    }

def calculate_tonnage(df):
    """حساب الطوناج"""
    if df.empty:
        return 0
    
    tonnage = 0
    for _, row in df.iterrows():
        weight = {'50kg': 0.050, '25kg': 0.025, '1.5t_Jumbo': 1.500}.get(row['bag_type'], 0)
        tonnage += row['good_bags'] * weight
    
    return round(tonnage, 2)

# ============================================
# Header
# ============================================
st.markdown("""
<div class="main-header">
    <h1>🏭 نظام إدارة منطقة التعبئة</h1>
    <p>Cement Packing Management System | الإصدار 3.0</p>
</div>
""", unsafe_allow_html=True)

# ============================================
# Sidebar - القائمة الجانبية
# ============================================
with st.sidebar:
    st.markdown("### 🎛️ لوحة التحكم")
    
    # اختيار اللغة
    language = st.selectbox("🌐 اللغة / Language", 
                           ["العربية", "English"],
                           index=0)
    
    st.markdown("---")
    
    # الفلاتر
    st.markdown("### 🔍 الفلاتر")
    
    # الفترة الزمنية
    period = st.selectbox("📅 الفترة الزمنية",
                         ["اليوم", "آخر 7 أيام", "آخر 30 يوم", "آخر 90 يوم", "مخصص"],
                         index=2)
    
    # الماكينة
    machines_df = run_query("SELECT machine_id, machine_name FROM machines")
    selected_machines = st.multiselect(
        "🏭 الماكينات",
        machines_df['machine_name'].tolist(),
        default=machines_df['machine_name'].tolist()
    )
    
    # نوع الشيكار
    bag_types = st.multiselect(
        "🎒 نوع الشيكار",
        ["50kg", "25kg", "1.5t_Jumbo"],
        default=["50kg", "25kg", "1.5t_Jumbo"]
    )
    
    st.markdown("---")
    
    # معلومات النظام
    st.markdown("### ℹ️ معلومات النظام")
    st.info(f"""
    **التاريخ:** {datetime.now().strftime('%Y-%m-%d')}  
    **الوقت:** {datetime.now().strftime('%H:%M:%S')}  
    **الحالة:** ✅ متصل  
    **الإصدار:** 3.0
    """)
    
    st.markdown("---")
    
    # أزرار سريعة
    if st.button("🔄 تحديث البيانات", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("📥 تصدير التقرير", use_container_width=True):
        st.session_state['show_export'] = True

# ============================================
# حساب الفترة الزمنية
# ============================================
if period == "اليوم":
    days_back = 1
elif period == "آخر 7 أيام":
    days_back = 7
elif period == "آخر 30 يوم":
    days_back = 30
elif period == "آخر 90 يوم":
    days_back = 90
else:
    days_back = 30

start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

# ============================================
# جلب البيانات
# ============================================
@st.cache_data(ttl=300)
def load_data(start_date, days_back):
    """تحميل جميع البيانات"""
    query = f"""
        SELECT p.*, m.machine_name, m.machine_type, s.shift_name, s.shift_date
        FROM production_logs p
        JOIN machines m ON p.machine_id = m.machine_id
        JOIN shifts s ON p.shift_id = s.shift_id
        WHERE s.shift_date >= '{start_date}'
    """
    df_prod = run_query(query)
    
    query_dt = f"""
        SELECT d.*, m.machine_name, s.shift_date
        FROM downtime_logs d
        JOIN machines m ON d.machine_id = m.machine_id
        JOIN shifts s ON d.shift_id = s.shift_id
        WHERE s.shift_date >= '{start_date}'
    """
    df_down = run_query(query_dt)
    
    query_machines = "SELECT * FROM machines"
    df_machines = run_query(query_machines)
    
    query_maintenance = """
        SELECT ms.*, m.machine_name
        FROM maintenance_schedule ms
        JOIN machines m ON ms.machine_id = m.machine_id
        WHERE ms.status = 'scheduled'
        ORDER BY ms.scheduled_date
    """
    df_maintenance = run_query(query_maintenance)
    
    return df_prod, df_down, df_machines, df_maintenance

df_production, df_downtime, df_machines, df_maintenance = load_data(start_date, days_back)

# ============================================
# Tabs - التبويبات الرئيسية
# ============================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 لوحة التحكم",
    "📦 تقرير الإنتاج",
    "🔧 تحليل التوقفات",
    "🔮 التنبؤ بالإنتاج",
    "🚨 الإنذارات",
    "🛠️ الصيانة الوقائية",
    "📥 تصدير التقارير"
])

# ============================================
# Tab 1: Dashboard - لوحة التحكم
# ============================================
with tab1:
    st.markdown("## 📊 نظرة عامة على الأداء")
    
    # حساب KPIs
    oee_metrics = calculate_oee(df_production, df_downtime)
    total_tonnage = calculate_tonnage(df_production)
    total_bags = df_production['total_bags'].sum()
    good_bags = df_production['good_bags'].sum()
    rejected_bags = df_production['rejected_bags'].sum()
    breakage_rate = (rejected_bags / total_bags * 100) if total_bags > 0 else 0
    
    # بطاقات KPI
    st.markdown("### 🎯 مؤشرات الأداء الرئيسية")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">🎯 الكفاءة الشاملة (OEE)</div>
            <div class="metric-value">{oee_metrics['oee']:.1f}%</div>
            <div class="metric-trend-up">↑ 2.3% عن الشهر الماضي</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">📦 إجمالي الإنتاج</div>
            <div class="metric-value">{total_tonnage:,.1f}</div>
            <div class="metric-label">طن</div>
            <div class="metric-trend-up">↑ 3.2% عن المستهدف</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">✅ الشكائر الجيدة</div>
            <div class="metric-value">{good_bags:,}</div>
            <div class="metric-label">شيكار</div>
            <div class="metric-trend-up">↑ 1.5%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        status_class = "metric-trend-down" if breakage_rate > 2 else "metric-trend-up"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">❌ نسبة التكسر</div>
            <div class="metric-value">{breakage_rate:.2f}%</div>
            <div class="{status_class}">الحد الأقصى: 2.0%</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # الرسوم البيانية
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎯 مكونات OEE")
        
        fig_radar = go.Figure()
        
        fig_radar.add_trace(go.Scatterpolar(
            r=[oee_metrics['availability'], oee_metrics['performance'], 
               oee_metrics['quality'], oee_metrics['availability']],
            theta=['التوافر', 'الأداء', 'الجودة', 'التوافر'],
            fill='toself',
            name='OEE',
            line_color='#3b82f6',
            fillcolor='rgba(59, 130, 246, 0.3)'
        ))
        
        fig_radar.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100])
            ),
            showlegend=False,
            height=400
        )
        
        st.plotly_chart(fig_radar, use_container_width=True)
    
    with col2:
        st.markdown("### 📊 الكفاءة الشاملة - Gauge")
        
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=oee_metrics['oee'],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "OEE %", 'font': {'size': 24}},
            delta={'reference': 85, 'increasing': {'color': "#10b981"}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#3b82f6"},
                'steps': [
                    {'range': [0, 70], 'color': '#fee2e2'},
                    {'range': [70, 85], 'color': '#fef3c7'},
                    {'range': [85, 100], 'color': '#d1fae5'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # اتجاه الإنتاج
    st.markdown("### 📈 اتجاه الإنتاج اليومي")
    
    if not df_production.empty:
        daily_production = df_production.groupby('shift_date').apply(
            lambda x: calculate_tonnage(x)
        ).reset_index()
        daily_production.columns = ['date', 'tonnage']
        daily_production['date'] = pd.to_datetime(daily_production['date'])
        daily_production = daily_production.sort_values('date')
        
        fig_line = go.Figure()
        
        fig_line.add_trace(go.Scatter(
            x=daily_production['date'],
            y=daily_production['tonnage'],
            mode='lines+markers',
            name='الإنتاج الفعلي',
            line=dict(color='#3b82f6', width=3),
            marker=dict(size=8)
        ))
        
        fig_line.add_trace(go.Scatter(
            x=daily_production['date'],
            y=[150] * len(daily_production),
            mode='lines',
            name='المستهدف',
            line=dict(color='#ef4444', width=2, dash='dash')
        ))
        
        fig_line.update_layout(
            xaxis_title="التاريخ",
            yaxis_title="الطناج (طن)",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_line, use_container_width=True)
    
    # توزيع الإنتاج حسب الماكينة
    st.markdown("### 🏭 الإنتاج حسب الماكينة")
    
    if not df_production.empty:
        machine_production = df_production.groupby('machine_name').apply(
            lambda x: calculate_tonnage(x)
        ).reset_index()
        machine_production.columns = ['machine', 'tonnage']
        
        fig_bar = px.bar(
            machine_production,
            x='machine',
            y='tonnage',
            color='machine',
            color_discrete_sequence=px.colors.qualitative.Set2,
            title="الطناج حسب الماكينة"
        )
        
        fig_bar.update_layout(
            xaxis_title="الماكينة",
            yaxis_title="الطناج (طن)",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_bar, use_container_width=True)

# ============================================
# Tab 2: Production Report - تقرير الإنتاج
# ============================================
with tab2:
    st.markdown("## 📦 تقرير الإنتاج التفصيلي")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 إجمالي التوناج", f"{total_tonnage:,.1f} طن", "3.2%")
    
    with col2:
        st.metric("🎒 إجمالي الشكائر", f"{total_bags:,}", "2.8%")
    
    with col3:
        st.metric("✅ الشكائر الجيدة", f"{good_bags:,}", "2.5%")
    
    with col4:
        st.metric("❌ الشكائر المرفوضة", f"{rejected_bags:,}", "-5.2%")
    
    st.markdown("---")
    
    # الرسوم البيانية
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 توزيع أنواع الشكائر")
        
        bag_distribution = df_production.groupby('bag_type')['good_bags'].sum().reset_index()
        
        fig_pie = px.pie(
            bag_distribution,
            values='good_bags',
            names='bag_type',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig_pie.update_layout(height=400)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("### 🏭 الإنتاج حسب الماكينة")
        
        machine_bags = df_production.groupby('machine_name')['good_bags'].sum().reset_index()
        
        fig_bar2 = px.bar(
            machine_bags,
            x='machine_name',
            y='good_bags',
            color='machine_name',
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig_bar2.update_layout(
            xaxis_title="الماكينة",
            yaxis_title="عدد الشكائر",
            height=400,
            showlegend=False
        )
        
        st.plotly_chart(fig_bar2, use_container_width=True)
    
    # جدول البيانات
    st.markdown("### 📋 سجلات الإنتاج")
    
    display_df = df_production[['shift_date', 'machine_name', 'bag_type', 
                                'total_bags', 'good_bags', 'rejected_bags', 
                                'spillage_kg']].copy()
    
    # حساب الطوناج
    display_df['tonnage'] = display_df.apply(
        lambda row: row['good_bags'] * {'50kg': 0.050, '25kg': 0.025, '1.5t_Jumbo': 1.500}.get(row['bag_type'], 0),
        axis=1
    )
    
    display_df = display_df.sort_values('shift_date', ascending=False)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        height=400
    )

# ============================================
# Tab 3: Downtime Analysis - تحليل التوقفات
# ============================================
with tab3:
    st.markdown("## 🔧 تحليل التوقفات والموثوقية")
    
    # KPIs
    total_downtime_hours = len(df_downtime) * 0.5  # تقدير
    num_breakdowns = df_downtime['is_breakdown'].sum() if not df_downtime.empty else 0
    mtbf = 24.5  # تقدير
    mttr = 1.8   # تقدير
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("⏱️ إجمالي وقت التوقف", f"{total_downtime_hours:.1f} ساعة", "-8.3%")
    
    with col2:
        st.metric("🔧 عدد الأعطال", f"{num_breakdowns}", "-2")
    
    with col3:
        st.metric("⚡ MTBF", f"{mtbf:.1f} ساعة", "5.2%")
    
    with col4:
        st.metric("🛠️ MTTR", f"{mttr:.1f} ساعة", "-12.5%")
    
    st.markdown("---")
    
    # الرسوم البيانية
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 توزيع أسباب التوقف")
        
        if not df_downtime.empty:
            reasons = df_downtime['reason'].value_counts().reset_index()
            reasons.columns = ['reason', 'count']
            
            fig_pie2 = px.pie(
                reasons,
                values='count',
                names='reason',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            
            fig_pie2.update_layout(height=400)
            st.plotly_chart(fig_pie2, use_container_width=True)
    
    with col2:
        st.markdown("### 🏭 التوقفات حسب الماكينة")
        
        if not df_downtime.empty:
            machine_down = df_downtime.groupby('machine_name').size().reset_index(name='count')
            
            fig_bar3 = px.bar(
                machine_down,
                x='machine_name',
                y='count',
                color='machine_name',
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            
            fig_bar3.update_layout(
                xaxis_title="الماكينة",
                yaxis_title="عدد التوقفات",
                height=400,
                showlegend=False
            )
            
            st.plotly_chart(fig_bar3, use_container_width=True)
    
    # خريطة التوقفات
    st.markdown("### 🗺️ خريطة التوقفات (أيام × ورديات)")
    
    if not df_downtime.empty:
        heatmap_data = df_downtime.groupby(['shift_date', 'shift_name'] if 'shift_name' in df_downtime.columns 
                                           else ['shift_date']).size()
        
        # بيانات تجريبية للheatmap
        days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة']
        shifts = ['صباحي', 'مسائي', 'ليلي']
        
        heatmap_matrix = np.random.randint(0, 10, size=(3, 7))
        
        fig_heatmap = go.Figure(data=go.Heatmap(
            z=heatmap_matrix,
            x=days,
            y=shifts,
            colorscale='YlOrRd',
            showscale=True
        ))
        
        fig_heatmap.update_layout(
            xaxis_title="اليوم",
            yaxis_title="الوردية",
            height=300
        )
        
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # جدول التوقفات
    st.markdown("### 📋 سجلات التوقفات")
    
    if not df_downtime.empty:
        st.dataframe(
            df_downtime[['shift_date', 'machine_name', 'start_time', 'end_time', 'reason']],
            use_container_width=True,
            height=400
        )

# ============================================
# Tab 4: Forecasting - التنبؤ بالإنتاج
# ============================================
with tab4:
    st.markdown("## 🔮 التنبؤ بالإنتاج المستقبلي")
    
    # إعدادات التنبؤ
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forecast_machine = st.selectbox(
            "🏭 اختر الماكينة",
            ["جميع الماكينات"] + df_machines['machine_name'].tolist()
        )
    
    with col2:
        forecast_days = st.slider("📅 أيام التنبؤ", 7, 90, 30)
    
    with col3:
        confidence_level = st.selectbox("📊 مستوى الثقة", ["80%", "90%", "95%"], index=1)
    
    st.markdown("---")
    
    # توليد التنبؤ (محاكاة)
    historical_days = 60
    historical_dates = pd.date_range(end=datetime.now(), periods=historical_days)
    
    # بيانات تاريخية مع اتجاه وموسمية
    trend = np.linspace(450, 480, historical_days)
    seasonal = 20 * np.sin(np.linspace(0, 4*np.pi, historical_days))
    noise = np.random.normal(0, 15, historical_days)
    historical = trend + seasonal + noise
    
    # التنبؤ
    forecast_dates = pd.date_range(start=datetime.now(), periods=forecast_days+1)[1:]
    forecast_trend = np.linspace(480, 490, forecast_days)
    forecast_seasonal = 20 * np.sin(np.linspace(4*np.pi, 6*np.pi, forecast_days))
    forecast = forecast_trend + forecast_seasonal
    
    # فترة الثقة
    conf_mult = {'80%': 1.28, '90%': 1.64, '95%': 1.96}[confidence_level]
    upper = forecast + conf_mult * 20
    lower = forecast - conf_mult * 20
    
    # KPIs التنبؤ
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 متوسط الإنتاج المتوقع", f"{forecast.mean():.1f} طن/يوم")
    
    with col2:
        st.metric("📈 إجمالي الفترة", f"{forecast.sum():,.0f} طن")
    
    with col3:
        st.metric("📉 الحد الأدنى", f"{lower.min():.1f} طن")
    
    with col4:
        st.metric("📈 الحد الأقصى", f"{upper.max():.1f} طن")
    
    # مخطط التنبؤ
    st.markdown("### 📈 التنبؤ بالإنتاج")
    
    fig_forecast = go.Figure()
    
    # البيانات التاريخية
    fig_forecast.add_trace(go.Scatter(
        x=historical_dates,
        y=historical,
        mode='lines',
        name='البيانات التاريخية',
        line=dict(color='#3b82f6', width=2)
    ))
    
    # التنبؤ
    fig_forecast.add_trace(go.Scatter(
        x=forecast_dates,
        y=forecast,
        mode='lines',
        name='التنبؤ',
        line=dict(color='#ef4444', width=2, dash='dash')
    ))
    
    # فترة الثقة
    fig_forecast.add_trace(go.Scatter(
        x=forecast_dates.tolist() + forecast_dates.tolist()[::-1],
        y=upper.tolist() + lower.tolist()[::-1],
        fill='toself',
        fillcolor='rgba(239, 68, 68, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name=f'فترة الثقة ({confidence_level})'
    ))
    
    # خط الآن
    fig_forecast.add_vline(
        x=datetime.now(),
        line_dash="dot",
        line_color="gray",
        annotation_text="الآن"
    )
    
    fig_forecast.update_layout(
        xaxis_title="التاريخ",
        yaxis_title="الإنتاج (طن)",
        height=500,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig_forecast, use_container_width=True)
    
    # التوصيات
    st.markdown("### 💡 التوصيات الذكية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.success("✅ اتجاه الإنتاج مستقر وإيجابي")
        st.info("📅 أقل إنتاج متوقع يوم الجمعة - يُنصح بجدولة الصيانة")
    
    with col2:
        st.warning("⚠️ تغير عالي في التنبؤ - راجع أسباب التقلبات")
        st.info(f"🎯 الإنتاج المتوقع للشهر: {forecast.sum():,.0f} طن (±8%)")
    
    # جدول التنبؤ
    st.markdown("### 📋 تفاصيل التنبؤ اليومي")
    
    forecast_df = pd.DataFrame({
        'التاريخ': forecast_dates.strftime('%Y-%m-%d'),
        'اليوم': forecast_dates.strftime('%A'),
        'التنبؤ (طن)': forecast.round(1),
        'الحد الأدنى': lower.round(1),
        'الحد الأقصى': upper.round(1),
        'الثقة': confidence_level
    })
    
    st.dataframe(forecast_df, use_container_width=True, height=400)

# ============================================
# Tab 5: Alerts - الإنذارات
# ============================================
with tab5:
    st.markdown("## 🚨 الإنذارات والإشعارات")
    
    # ملخص الإنذارات
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-card" style="border-left-color: #ef4444;">
            <div class="metric-label">🔴 إنذارات حرجة</div>
            <div class="metric-value" style="color: #ef4444;">2</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card" style="border-left-color: #f59e0b;">
            <div class="metric-label">🟠 إنذارات متوسطة</div>
            <div class="metric-value" style="color: #f59e0b;">5</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card" style="border-left-color: #3b82f6;">
            <div class="metric-label">🔵 معلومات</div>
            <div class="metric-value" style="color: #3b82f6;">8</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-card" style="border-left-color: #10b981;">
            <div class="metric-label">✅ تم الحل</div>
            <div class="metric-value" style="color: #10b981;">15</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # فلاتر
    col1, col2 = st.columns(2)
    
    with col1:
        severity_filter = st.selectbox("🔍 مستوى الخطورة", 
                                      ["الكل", "حرج", "متوسط", "منخفض"])
    
    with col2:
        machine_filter = st.selectbox("🏭 الماكينة",
                                     ["جميع الماكينات"] + df_machines['machine_name'].tolist())
    
    st.markdown("---")
    
    # قائمة الإنذارات
    st.markdown("### 📋 قائمة الإنذارات")
    
    alerts = [
        {
            "severity": "HIGH",
            "type": "انخفاض الكفاءة OEE",
            "message": "الكفاءة الشاملة انخفضت إلى 78.5% وهو أقل من الحد الأدنى (85%)",
            "machine": "Rotary Packer 1",
            "time": "منذ 15 دقيقة"
        },
        {
            "severity": "HIGH",
            "type": "ارتفاع نسبة التكسر",
            "message": "نسبة تكسر الشكائر وصلت إلى 3.2% (الحد الأقصى 2%)",
            "machine": "Inline Packer 1",
            "time": "منذ 45 دقيقة"
        },
        {
            "severity": "MEDIUM",
            "type": "تأخر الصيانة",
            "message": "وقت الإصلاح تجاوز ساعتين (MTTR = 2.5 ساعة)",
            "machine": "Rotary Packer 2",
            "time": "منذ ساعتين"
        },
        {
            "severity": "MEDIUM",
            "type": "ارتفاع الفاقد",
            "message": "الفاقد من الأسمنت وصل إلى 650 كجم في الوردية",
            "machine": "Jumbo Packer 1",
            "time": "منذ 3 ساعات"
        },
        {
            "severity": "LOW",
            "type": "صيانة وقائية قادمة",
            "message": "الصيانة الدورية لـ Rotary Packer 1 بعد 3 أيام",
            "machine": "Rotary Packer 1",
            "time": "منذ 5 ساعات"
        },
        {
            "severity": "LOW",
            "type": "تحديث النظام",
            "message": "يتوفر تحديث جديد للنظام - الإصدار 3.1",
            "machine": "النظام",
            "time": "منذ يوم"
        },
    ]
    
    for alert in alerts:
        severity_class = {
            "HIGH": "alert-high",
            "MEDIUM": "alert-medium",
            "LOW": "alert-low"
        }[alert['severity']]
        
        severity_badge = {
            "HIGH": '<span class="status-badge status-danger">🔴 حرج</span>',
            "MEDIUM": '<span class="status-badge status-warning">🟠 متوسط</span>',
            "LOW": '<span class="status-badge status-info">🔵 منخفض</span>'
        }[alert['severity']]
        
        st.markdown(f"""
        <div class="alert-card {severity_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4 style="margin: 0 0 0.5rem 0;">🚨 {alert['type']}</h4>
                    <p style="margin: 0; color: #64748b;">{alert['message']}</p>
                    <div style="margin-top: 0.5rem;">
                        <span style="color: #64748b;">🏭 {alert['machine']}</span>
                        <span style="color: #94a3b8; margin: 0 10px;">|</span>
                        <span style="color: #64748b;">⏰ {alert['time']}</span>
                    </div>
                </div>
                <div>{severity_badge}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================
# Tab 6: Maintenance - الصيانة الوقائية
# ============================================
with tab6:
    st.markdown("## 🛠️ الصيانة الوقائية")
    
    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🔧 صيانة هذا الشهر", "8 عمليات", "12.5%")
    
    with col2:
        st.metric("⏱️ إجمالي الساعات", "24.5 ساعة", "-5.2%")
    
    with col3:
        st.metric("💰 التكلفة", "12,500 ريال", "8.3%")
    
    with col4:
        st.metric("📊 متوسط المدة", "3.1 ساعة", "-10.0%")
    
    st.markdown("---")
    
    # الصيانة القادمة
    st.markdown("### 📅 الصيانة القادمة")
    
    if not df_maintenance.empty:
        for _, row in df_maintenance.iterrows():
            scheduled_date = datetime.strptime(row['scheduled_date'], '%Y-%m-%d')
            days_until = (scheduled_date - datetime.now()).days
            
            priority = "HIGH" if days_until <= 5 else "MEDIUM" if days_until <= 10 else "LOW"
            priority_color = {
                "HIGH": "#ef4444",
                "MEDIUM": "#f59e0b",
                "LOW": "#3b82f6"
            }[priority]
            
            st.markdown(f"""
            <div style="background: white; padding: 1.2rem; border-radius: 12px; 
                        margin: 0.5rem 0; border-right: 5px solid {priority_color};
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <h4 style="margin: 0 0 0.5rem 0;">🏭 {row['machine_name']} - {row['maintenance_type']}</h4>
                        <p style="margin: 0; color: #64748b;">
                            📅 {row['scheduled_date']} | ⏰ بعد {days_until} أيام | 
                            👤 {row['assigned_to']} | 💰 {row['cost']:,} ريال
                        </p>
                    </div>
                    <div>
                        <span class="status-badge" style="background-color: {priority_color}20; 
                              color: {priority_color};">
                            {priority}
                        </span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # الرسوم البيانية
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 اتجاه الصيانة (آخر 6 أشهر)")
        
        months = ['مايو', 'يونيو', 'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر']
        counts = [5, 7, 6, 8, 7, 8]
        
        fig_bar_m = px.bar(
            x=months,
            y=counts,
            labels={'x': 'الشهر', 'y': 'عدد العمليات'},
            color_discrete_sequence=['#3b82f6']
        )
        
        fig_bar_m.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig_bar_m, use_container_width=True)
    
    with col2:
        st.markdown("### 💰 تكاليف الصيانة حسب الماكينة")
        
        machines_cost = ['RP-1', 'RP-2', 'IP-1', 'JP-1']
        costs = [40, 30, 20, 10]
        
        fig_pie_cost = px.pie(
            values=costs,
            names=machines_cost,
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        
        fig_pie_cost.update_layout(height=400)
        st.plotly_chart(fig_pie_cost, use_container_width=True)

# ============================================
# Tab 7: Export - تصدير التقارير
# ============================================
with tab7:
    st.markdown("## 📥 تصدير التقارير")
    
    # إعدادات التصدير
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📅 فترة التقرير")
        
        report_year = st.selectbox("السنة", [2025, 2026, 2027], index=1)
        report_month = st.selectbox(
            "الشهر",
            ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو",
             "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
            index=9
        )
    
    with col2:
        st.markdown("### 📊 اختر التقارير")
        
        include_production = st.checkbox("📦 تقرير الإنتاج", value=True)
        include_oee = st.checkbox("📊 تقرير OEE", value=True)
        include_downtime = st.checkbox("🔧 تقرير التوقفات", value=True)
        include_alerts = st.checkbox("🚨 تقرير الإنذارات", value=True)
        include_forecast = st.checkbox("🔮 تقرير التنبؤ", value=True)
        include_maintenance = st.checkbox("🛠️ تقرير الصيانة", value=True)
    
    st.markdown("---")
    
    # صيغة التصدير
    st.markdown("### 📄 صيغة التصدير")
    
    export_format = st.radio(
        "اختر الصيغة",
        ["📄 PDF", "📊 Excel", "📋 CSV"],
        horizontal=True
    )
    
    # خيارات إضافية
    st.markdown("### ⚙️ خيارات إضافية")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_charts = st.checkbox("📈 تضمين الرسوم البيانية", value=True)
        include_summary = st.checkbox("📋 تضمين الملخص التنفيذي", value=True)
    
    with col2:
        email_copy = st.checkbox("📧 إرسال نسخة بالبريد", value=False)
        add_signature = st.checkbox("✍️ إضافة توقيع المدير", value=False)
    
    st.markdown("---")
    
    # زر التصدير
    if st.button("📥 تصدير التقرير", type="primary", use_container_width=True):
        selected_reports = []
        if include_production: selected_reports.append("الإنتاج")
        if include_oee: selected_reports.append("OEE")
        if include_downtime: selected_reports.append("التوقفات")
        if include_alerts: selected_reports.append("الإنذارات")
        if include_forecast: selected_reports.append("التنبؤ")
        if include_maintenance: selected_reports.append("الصيانة")
        
        if not selected_reports:
            st.error("❌ يرجى اختيار تقرير واحد على الأقل")
        else:
            # إنشاء ملف تجريبي للتحميل
            if "Excel" in export_format:
                # إنشاء Excel
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    if include_production:
                        df_production.to_excel(writer, sheet_name='الإنتاج', index=False)
                    if include_downtime and not df_downtime.empty:
                        df_downtime.to_excel(writer, sheet_name='التوقفات', index=False)
                
                st.download_button(
                    label="📥 تحميل ملف Excel",
                    data=output.getvalue(),
                    file_name=f"تقرير_{report_month}_{report_year}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            
            elif "CSV" in export_format:
                csv = df_production.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 تحميل ملف CSV",
                    data=csv,
                    file_name=f"تقرير_{report_month}_{report_year}.csv",
                    mime="text/csv"
                )
            
            else:  # PDF
                # إنشاء PDF بسيط
                pdf_content = f"""
                تقرير منطقة التعبئة
                الفترة: {report_month} {report_year}
                
                التقارير المضمنة:
                {chr(10).join(['- ' + r for r in selected_reports])}
                
                ملخص الأداء:
                - إجمالي الإنتاج: {total_tonnage:,.1f} طن
                - الكفاءة الشاملة (OEE): {oee_metrics['oee']:.1f}%
                - عدد الشكائر: {total_bags:,}
                - نسبة التكسر: {breakage_rate:.2f}%
                """
                
                st.download_button(
                    label="📥 تحميل ملف PDF",
                    data=pdf_content.encode('utf-8'),
                    file_name=f"تقرير_{report_month}_{report_year}.txt",
                    mime="text/plain"
                )
            
            st.success(f"✅ تم تصدير {len(selected_reports)} تقرير بنجاح!")
    
    st.markdown("---")
    
    # التصديرات الأخيرة
    st.markdown("### 📂 التصديرات الأخيرة")
    
    recent_exports = [
        ("📄 تقرير_أكتوبر_2026.pdf", "2026-10-05 14:30", "2.5 MB"),
        ("📊 تقرير_الإنتاج.xlsx", "2026-10-04 10:15", "1.8 MB"),
        ("📋 تقرير_التوقفات.pdf", "2026-10-03 16:45", "1.2 MB"),
        ("📊 تقرير_OEE.xlsx", "2026-10-02 09:20", "1.5 MB"),
    ]
    
    for file, date, size in recent_exports:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"**{file}**")
        with col2:
            st.markdown(f"<span style='color: #64748b;'>{date}</span>", 
                       unsafe_allow_html=True)
        with col3:
            st.markdown(f"<span style='color: #94a3b8;'>{size}</span>", 
                       unsafe_allow_html=True)

# ============================================
# Footer
# ============================================
st.markdown("---")
st.markdown(f"""
<div style='text-align: center; color: #64748b; padding: 1rem;'>
    <small>© 2026 نظام إدارة منطقة التعبئة | الإصدار 3.0 | 
    آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
</div>
""", unsafe_allow_html=True)
