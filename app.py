import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

st.set_page_config(
    page_title="Call Center Dashboard 2025",
    page_icon="📞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Global */
    .main { background-color: #0f1117; }
    [data-testid="stAppViewContainer"] { background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #161929 0%, #1e2235 100%); border-right: 1px solid #2d3154; }

    /* KPI Cards */
    .kpi-card {
        background: linear-gradient(135deg, #1e2235 0%, #252942 100%);
        border: 1px solid #3a3f6e;
        border-radius: 16px;
        padding: 20px 24px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        margin-bottom: 8px;
    }
    .kpi-label { color: #8b92c4; font-size: 12px; font-weight: 600; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 8px; }
    .kpi-value { color: #ffffff; font-size: 32px; font-weight: 700; line-height: 1; margin-bottom: 4px; }
    .kpi-sub   { font-size: 13px; font-weight: 500; margin-top: 4px; }
    .kpi-green { color: #4ade80; }
    .kpi-red   { color: #f87171; }
    .kpi-blue  { color: #60a5fa; }
    .kpi-purple { color: #a78bfa; }
    .kpi-yellow { color: #facc15; }

    /* Section headers */
    .section-header {
        color: #c7cdff;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 0.8px;
        text-transform: uppercase;
        padding: 6px 0 2px 0;
        border-bottom: 2px solid #3a3f6e;
        margin-bottom: 12px;
    }

    /* Highlight agent box */
    .agent-box {
        background: linear-gradient(135deg, #1e2235 0%, #252942 100%);
        border: 1px solid #3a3f6e;
        border-radius: 12px;
        padding: 18px 20px;
        text-align: center;
    }
    .agent-name { color: #ffffff; font-size: 20px; font-weight: 700; }
    .agent-stat { color: #a78bfa; font-size: 14px; margin-top: 4px; }

    /* Performance badge */
    .perf-badge {
        display: inline-block;
        padding: 8px 24px;
        border-radius: 50px;
        font-size: 22px;
        font-weight: 700;
        margin: 10px 0;
    }

    h1, h2, h3 { color: #c7cdff !important; }
    [data-testid="stMetricLabel"] { color: #8b92c4 !important; }
    [data-testid="stMetricValue"] { color: #ffffff !important; }
</style>
""", unsafe_allow_html=True)

# ─── Load & Prepare Data ───────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("call_center_dataset_1000_records.csv")
    df['DATE'] = pd.to_datetime(df['DATE'], format='%m/%d/%Y')
    df['MONTH']     = df['DATE'].dt.month
    df['MONTH_NAME'] = df['DATE'].dt.strftime('%B')
    df['DAY_NAME']  = df['DATE'].dt.strftime('%A')
    df['DAY_NUM']   = df['DATE'].dt.dayofweek
    df['MONTH_ORDER'] = df['DATE'].dt.month

    df['CALL_ANSWERED']  = (df['ANSWERED'] == 'Y').astype(int)
    df['CALL_RESOLVED']  = (df['RESOLVED'] == 'Y').astype(int)
    df['CALL_UNRESOLVED']= (df['RESOLVED'] == 'N').astype(int)
    return df

df_raw = load_data()

# ─── Sidebar – Slicers ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎛️ Filters")
    st.markdown("---")

    month_order = sorted(df_raw['MONTH'].unique())
    month_names = {m: pd.Timestamp(2025, m, 1).strftime('%B') for m in month_order}
    month_options = ["All Months"] + [month_names[m] for m in month_order]
    sel_month = st.selectbox("📅 Month", month_options)

    day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    available_days = [d for d in day_order if d in df_raw['DAY_NAME'].unique()]
    day_options = ["All Days"] + available_days
    sel_day = st.selectbox("📆 Day of Week", day_options)

    agents = ["All Agents"] + sorted(df_raw['AGENT'].unique().tolist())
    sel_agent = st.selectbox("👤 Agent", agents)

    topics = ["All Topics"] + sorted(df_raw['TOPIC'].unique().tolist())
    sel_topic = st.selectbox("💬 Topic", topics)

    st.markdown("---")
    st.markdown("<p style='color:#8b92c4;font-size:12px;'>📞 Call Center Analytics 2025</p>", unsafe_allow_html=True)

# ─── Apply Filters ─────────────────────────────────────────────────────────────
df = df_raw.copy()
if sel_month != "All Months":
    mn = {v: k for k, v in {m: pd.Timestamp(2025, m, 1).strftime('%B') for m in range(1,13)}.items()}
    df = df[df['MONTH'] == mn[sel_month]]
if sel_day != "All Days":
    df = df[df['DAY_NAME'] == sel_day]
if sel_agent != "All Agents":
    df = df[df['AGENT'] == sel_agent]
if sel_topic != "All Topics":
    df = df[df['TOPIC'] == sel_topic]

# ─── Computed Metrics ─────────────────────────────────────────────────────────
total          = len(df)
answered       = df['CALL_ANSWERED'].sum()
resolved       = df['CALL_RESOLVED'].sum()
unresolved     = df['CALL_UNRESOLVED'].sum()
pct_answered   = (answered / total * 100) if total else 0
pct_resolved   = (resolved / answered * 100) if answered else 0
pct_unresolved = (unresolved / answered * 100) if answered else 0

agent_calls    = df.groupby('AGENT')['CALL_ANSWERED'].sum()
top_agent_calls= agent_calls.idxmax() if not agent_calls.empty else "N/A"
top_agent_num  = int(agent_calls.max()) if not agent_calls.empty else 0

agent_sat      = df[df['SATISFACTION RATE'].notna() & (df['ANSWERED']=='Y')]\
                    .groupby('AGENT')['SATISFACTION RATE'].mean()
top_agent_sat  = agent_sat.idxmax() if not agent_sat.empty else "N/A"
top_agent_sat_val = round(float(agent_sat.max()), 2) if not agent_sat.empty else 0

avg_sat        = df['SATISFACTION RATE'].mean() if total else 0
overall_sat    = round(df_raw['SATISFACTION RATE'].mean(), 2)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style='text-align:center; font-size:30px; margin-bottom:4px;'>
    📞 Call Center Performance Dashboard
</h1>
<p style='text-align:center; color:#8b92c4; font-size:14px; margin-top:0;'>
    2025 Analytics Overview — Use sidebar filters to slice the data
</p>
""", unsafe_allow_html=True)
st.markdown("---")

# ─── KPI Row 1 ────────────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6 = st.columns(6)
kpis = [
    (c1, "TOTAL CALLS",     total,        f"Filtered dataset",                        "kpi-blue"),
    (c2, "CALLS ANSWERED",  answered,     f"<span class='kpi-green'>{pct_answered:.1f}%</span> of total", "kpi-green"),
    (c3, "CALLS RESOLVED",  resolved,     f"<span class='kpi-green'>{pct_resolved:.1f}%</span> of answered","kpi-purple"),
    (c4, "NOT RESOLVED",    unresolved,   f"<span class='kpi-red'>{pct_unresolved:.1f}%</span> of answered","kpi-yellow"),
    (c5, "AVG SAT RATE",    f"{avg_sat:.2f}", "Out of 5.0 ⭐",                         "kpi-blue"),
]
for col, label, value, sub, cls in kpis:
    with col:
        st.markdown(f"""
        <div class='kpi-card'>
            <div class='kpi-label'>{label}</div>
            <div class='kpi-value {cls}'>{value}</div>
            <div class='kpi-sub'>{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 2: Top Agents ────────────────────────────────────────────────────────
a1, a2 = st.columns(2)
with a1:
    st.markdown("<div class='section-header'>🏆 Top Agent — Most Calls Answered</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='agent-box'>
        <div style='font-size:40px;margin-bottom:4px;'>🥇</div>
        <div class='agent-name'>{top_agent_calls}</div>
        <div class='agent-stat'>{top_agent_num:,} calls answered</div>
    </div>""", unsafe_allow_html=True)

with a2:
    st.markdown("<div class='section-header'>⭐ Top Agent — Highest Satisfaction Rate</div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div class='agent-box'>
        <div style='font-size:40px;margin-bottom:4px;'>🌟</div>
        <div class='agent-name'>{top_agent_sat}</div>
        <div class='agent-stat'>Average satisfaction: {top_agent_sat_val} / 5.0</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Row 3: Topic Chart + Answered/Resolved Donut ─────────────────────────────
st.markdown("<div class='section-header'>📊 Call Volume by Topic</div>", unsafe_allow_html=True)
col_topic, col_donut = st.columns([2, 1])

with col_topic:
    topic_df = df.groupby('TOPIC').agg(
        Answered=('CALL_ANSWERED','sum'),
        Resolved=('CALL_RESOLVED','sum')
    ).reset_index().sort_values('Answered', ascending=True)

    fig_topic = go.Figure()
    fig_topic.add_trace(go.Bar(
        y=topic_df['TOPIC'], x=topic_df['Answered'], name='Answered',
        orientation='h', marker_color='#60a5fa',
        text=topic_df['Answered'], textposition='outside'
    ))
    fig_topic.add_trace(go.Bar(
        y=topic_df['TOPIC'], x=topic_df['Resolved'], name='Resolved',
        orientation='h', marker_color='#a78bfa',
        text=topic_df['Resolved'], textposition='outside'
    ))
    fig_topic.update_layout(
        barmode='stack', height=420,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#c7cdff')),
        xaxis=dict(gridcolor='#2d3154', title='Number of Calls'),
        yaxis=dict(gridcolor='#2d3154'),
        margin=dict(l=10, r=40, t=20, b=20)
    )
    st.plotly_chart(fig_topic, use_container_width=True)

with col_donut:
    fig_donut = go.Figure(go.Pie(
        labels=['Answered', 'Resolved'],
        values=[answered, resolved],
        hole=0.65,
        marker=dict(colors=['#4ade80', '#a78bfa']),
        textinfo='label+percent',
        textfont=dict(color='white', size=13),
        hovertemplate='%{label}: %{value} (%{percent})<extra></extra>'
    ))
    fig_donut.add_annotation(
        text=f"<b>{pct_answered:.1f}%</b><br><span style='font-size:10px'>Answered</span>",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=18, color='white'),
        align='center'
    )
    fig_donut.update_layout(
        height=420, title=dict(text='Answered vs Resolved', font=dict(color='#c7cdff', size=14), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_donut, use_container_width=True)

# ─── Row 4: Duration by Agent + Resolution Funnel ─────────────────────────────
st.markdown("<div class='section-header'>⏱️ Call Duration by Agent</div>", unsafe_allow_html=True)
col_dur, col_res = st.columns([2, 1])

with col_dur:
    dur_df = df[df['ANSWERED']=='Y'].groupby('AGENT')['AVG. TALK DURATION'].agg(['mean','sum','count']).reset_index()
    dur_df.columns = ['AGENT','AVG_DUR','TOTAL_DUR','CALLS']
    dur_df = dur_df.sort_values('AVG_DUR', ascending=False)

    fig_dur = go.Figure()
    fig_dur.add_trace(go.Bar(
        x=dur_df['AGENT'], y=dur_df['AVG_DUR'], name='Avg Duration (s)',
        marker_color='#a78bfa',
        text=dur_df['AVG_DUR'].round(1), textposition='outside'
    ))
    fig_dur.add_trace(go.Scatter(
        x=dur_df['AGENT'], y=dur_df['TOTAL_DUR'], name='Total Duration (s)',
        mode='lines+markers', yaxis='y2',
        line=dict(color='#facc15', width=2),
        marker=dict(size=8, color='#facc15')
    ))
    fig_dur.update_layout(
        height=380,
        yaxis=dict(title='Avg Duration (sec)', gridcolor='#2d3154'),
        yaxis2=dict(title='Total Duration (sec)', overlaying='y', side='right', gridcolor='#2d3154'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=10, r=60, t=20, b=80),
        xaxis=dict(tickangle=-30)
    )
    st.plotly_chart(fig_dur, use_container_width=True)

with col_res:
    fig_funnel = go.Figure(go.Funnel(
        y=["Total Calls", "Answered", "Resolved"],
        x=[total, answered, resolved],
        textinfo="value+percent initial",
        marker=dict(color=['#3b82f6','#4ade80','#a78bfa']),
        connector=dict(line=dict(color='#2d3154', width=2))
    ))
    fig_funnel.update_layout(
        height=380, title=dict(text='Call Resolution Funnel', font=dict(color='#c7cdff', size=14), x=0.5),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        margin=dict(l=10, r=10, t=50, b=10)
    )
    st.plotly_chart(fig_funnel, use_container_width=True)

# ─── Row 5: Calls by Month + Calls by Day ─────────────────────────────────────
st.markdown("<div class='section-header'>📅 Total Calls by Month & Day of Week</div>", unsafe_allow_html=True)
col_mon, col_day = st.columns([3, 2])

with col_mon:
    month_df = df.groupby(['MONTH_ORDER','MONTH_NAME']).agg(
        Answered=('CALL_ANSWERED','sum'),
        Resolved=('CALL_RESOLVED','sum'),
        Total=('CALLER ID','count')
    ).reset_index().sort_values('MONTH_ORDER')

    fig_month = go.Figure()
    fig_month.add_trace(go.Bar(x=month_df['MONTH_NAME'], y=month_df['Answered'], name='Answered', marker_color='#60a5fa'))
    fig_month.add_trace(go.Bar(x=month_df['MONTH_NAME'], y=month_df['Resolved'], name='Resolved', marker_color='#4ade80'))
    fig_month.add_trace(go.Scatter(
        x=month_df['MONTH_NAME'], y=month_df['Total'], name='Total',
        mode='lines+markers', line=dict(color='#facc15', width=2), marker=dict(size=8)
    ))
    fig_month.update_layout(
        barmode='stack', height=340,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        legend=dict(bgcolor='rgba(0,0,0,0)'),
        xaxis=dict(gridcolor='#2d3154'),
        yaxis=dict(gridcolor='#2d3154'),
        margin=dict(l=10, r=10, t=20, b=20)
    )
    st.plotly_chart(fig_month, use_container_width=True)

with col_day:
    day_order_list = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    day_df = df.groupby('DAY_NAME').agg(Total=('CALLER ID','count')).reindex(day_order_list).dropna().reset_index()

    fig_day = go.Figure(go.Bar(
        x=day_df['DAY_NAME'], y=day_df['Total'],
        marker=dict(color=day_df['Total'], colorscale='Viridis', showscale=False),
        text=day_df['Total'], textposition='outside'
    ))
    fig_day.update_layout(
        height=340,
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        xaxis=dict(gridcolor='#2d3154', tickangle=-30),
        yaxis=dict(gridcolor='#2d3154'),
        margin=dict(l=10, r=10, t=20, b=60)
    )
    st.plotly_chart(fig_day, use_container_width=True)

# ─── Row 6: Agent Satisfaction Heatmap ────────────────────────────────────────
st.markdown("<div class='section-header'>🌡️ Agent × Topic Satisfaction Heatmap</div>", unsafe_allow_html=True)

heat_df = df[df['ANSWERED']=='Y'].groupby(['AGENT','TOPIC'])['SATISFACTION RATE'].mean().reset_index()
heat_pivot = heat_df.pivot(index='AGENT', columns='TOPIC', values='SATISFACTION RATE')

fig_heat = go.Figure(go.Heatmap(
    z=heat_pivot.values,
    x=heat_pivot.columns.tolist(),
    y=heat_pivot.index.tolist(),
    colorscale='RdYlGn',
    zmin=1, zmax=5,
    text=[[f"{v:.1f}" if not np.isnan(v) else "" for v in row] for row in heat_pivot.values],
    texttemplate="%{text}",
    hovertemplate='Agent: %{y}<br>Topic: %{x}<br>Avg Satisfaction: %{z:.2f}<extra></extra>'
))
fig_heat.update_layout(
    height=380,
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color="#da1647"),
    xaxis=dict(tickangle=-30),
    margin=dict(l=10, r=10, t=10, b=80)
)
st.plotly_chart(fig_heat, use_container_width=True)

# ─── Row 7: Overall 2025 Performance Rating (Gauge + Radar) ───────────────────
st.markdown("<div class='section-header'>🎯 Overall 2025 Performance Rating</div>", unsafe_allow_html=True)
col_gauge, col_radar, col_perf = st.columns([1, 2, 1])

# Use full dataset for overall rating
ov_answered_pct = df_raw['CALL_ANSWERED'].mean() * 100
ov_resolved_pct = (df_raw[df_raw['ANSWERED']=='Y']['CALL_RESOLVED'].mean()) * 100
ov_sat = df_raw['SATISFACTION RATE'].mean()
ov_sat_pct = (ov_sat / 5) * 100
avg_speed = df_raw[df_raw['ANSWERED']=='Y']['SPEED OF ANSWER IN SECOND'].mean()
speed_score = max(0, 100 - (avg_speed / 3))  # lower is better; cap at 100

overall_score = (ov_answered_pct * 0.30 + ov_resolved_pct * 0.35 + ov_sat_pct * 0.25 + speed_score * 0.100)

def get_grade(score):
    if score >= 90: return "A+", "#4ade80", "Exceptional"
    elif score >= 80: return "A", "#86efac", "Excellent"
    elif score >= 70: return "B", "#facc15", "Good"
    elif score >= 60: return "C", "#fb923c", "Average"
    else: return "D", "#f87171", "Needs Improvement"

grade, grade_color, grade_label = get_grade(overall_score)

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=round(overall_score, 1),
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'suffix': '%', 'font': {'size': 28, 'color': 'white'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#8b92c4', 'tickfont': {'color': '#8b92c4'}},
            'bar': {'color': grade_color},
            'bgcolor': "#1939d4",
            'bordercolor': '#3a3f6e',
            'steps': [
                {'range': [0, 60], 'color': '#2a1f2d'},
                {'range': [60, 70], 'color': '#2a2520'},
                {'range': [70, 80], 'color': '#252a1f'},
                {'range': [80, 90], 'color': '#1f2a2a'},
                {'range': [90, 100], 'color': '#1f2a1f'},
            ],
            'threshold': {'line': {'color': grade_color, 'width': 4}, 'thickness': 0.85, 'value': overall_score}
        },
        title={'text': "Overall Score", 'font': {'color': '#c7cdff', 'size': 14}}
    ))
    fig_gauge.update_layout(
        height=300,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#3c4cd6"),
        margin=dict(l=20, r=20, t=40, b=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_radar:
    categories = ['Answer Rate', 'Resolution Rate', 'Satisfaction', 'Response Speed', 'Call Volume']
    values = [
        ov_answered_pct,
        ov_resolved_pct,
        ov_sat_pct,
        speed_score,
        min(100, len(df_raw) / 15)
    ]
    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=values + [values[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(96, 165, 250, 0.2)',
        line=dict(color='#60a5fa', width=2),
        name='2025 Performance',
        marker=dict(size=8, color='#60a5fa')
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[80]*5 + [80],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(250, 204, 21, 0.05)',
        line=dict(color='#facc15', width=1, dash='dash'),
        name='Target (80%)'
    ))
    fig_radar.update_layout(
        polar=dict(
            bgcolor='rgba(30,34,53,0.8)',
            radialaxis=dict(visible=True, range=[0,100], gridcolor='#3a3f6e', tickcolor='#8b92c4', tickfont=dict(color='#8b92c4', size=10)),
            angularaxis=dict(gridcolor='#3a3f6e', tickcolor='#c7cdff', tickfont=dict(color='#c7cdff', size=12))
        ),
        height=340,
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#c7cdff'),
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#c7cdff')),
        margin=dict(l=40, r=40, t=20, b=20)
    )
    st.plotly_chart(fig_radar, use_container_width=True)

with col_perf:
    st.markdown(f"""
    <div class='agent-box' style='margin-top:30px;'>
        <div style='font-size:14px; color:#8b92c4; text-transform:uppercase; letter-spacing:1px; margin-bottom:8px;'>2025 Grade</div>
        <div style='font-size:72px; font-weight:900; color:{grade_color}; line-height:1;'>{grade}</div>
        <div style='font-size:16px; color:{grade_color}; font-weight:600; margin-top:8px;'>{grade_label}</div>
        <hr style='border-color:#3a3f6e; margin:14px 0;'>
        <div style='font-size:12px; color:#8b92c4;'>Answer Rate</div>
        <div style='font-size:18px; color:#4ade80; font-weight:700;'>{ov_answered_pct:.1f}%</div>
        <div style='font-size:12px; color:#8b92c4; margin-top:6px;'>Resolution Rate</div>
        <div style='font-size:18px; color:#a78bfa; font-weight:700;'>{ov_resolved_pct:.1f}%</div>
        <div style='font-size:12px; color:#8b92c4; margin-top:6px;'>Avg Satisfaction</div>
        <div style='font-size:18px; color:#facc15; font-weight:700;'>{ov_sat:.2f} / 5.0 ⭐</div>
    </div>
    """, unsafe_allow_html=True)

# ─── Row 8: Agent Comparison Bar ──────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<div class='section-header'>👥 Agent Performance Comparison</div>", unsafe_allow_html=True)

agent_perf = df.groupby('AGENT').agg(
    Answered=('CALL_ANSWERED','sum'),
    Resolved=('CALL_RESOLVED','sum'),
    AvgSat=('SATISFACTION RATE','mean'),
    AvgDur=('AVG. TALK DURATION','mean')
).reset_index().sort_values('Answered', ascending=False)

fig_agent = make_subplots(
    rows=1, cols=2,
    subplot_titles=["Calls Handled per Agent", "Avg Satisfaction per Agent"]
)
fig_agent.add_trace(go.Bar(
    x=agent_perf['AGENT'], y=agent_perf['Answered'], name='Answered', marker_color='#60a5fa'
), row=1, col=1)
fig_agent.add_trace(go.Bar(
    x=agent_perf['AGENT'], y=agent_perf['Resolved'], name='Resolved', marker_color='#4ade80'
), row=1, col=1)
fig_agent.add_trace(go.Bar(
    x=agent_perf['AGENT'], y=agent_perf['AvgSat'].round(2),
    name='Avg Satisfaction', marker_color='#facc15',
    text=agent_perf['AvgSat'].round(2), textposition='outside'
), row=1, col=2)

fig_agent.update_layout(
    height=380, barmode='group',
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color='#c7cdff'),
    legend=dict(bgcolor='rgba(0,0,0,0)'),
    margin=dict(l=10, r=10, t=40, b=80)
)
for ann in fig_agent['layout']['annotations']:
    ann['font'] = dict(color='#c7cdff', size=13)
fig_agent.update_xaxes(gridcolor='#2d3154', tickangle=-30)
fig_agent.update_yaxes(gridcolor='#2d3154')
st.plotly_chart(fig_agent, use_container_width=True)

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<p style='text-align:center; color:#8b92c4; font-size:12px;'>
    📞 Call Center Dashboard 2025 &nbsp;|&nbsp; 
    Total Records: {len(df_raw):,} &nbsp;|&nbsp; 
    Agents: {df_raw['AGENT'].nunique()} &nbsp;|&nbsp; 
    Topics: {df_raw['TOPIC'].nunique()}
</p>
""", unsafe_allow_html=True)