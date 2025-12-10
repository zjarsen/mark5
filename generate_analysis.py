import sqlite3
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json

# Connect to database
conn = sqlite3.connect('patient_bp.db')

# Load data
bp_df = pd.read_sql_query("SELECT * FROM blood_pressure_readings", conn)
med_df = pd.read_sql_query("SELECT * FROM medications", conn)

# Convert datetime strings to datetime objects
bp_df['datetime'] = pd.to_datetime(bp_df['datetime'])
med_df['datetime'] = pd.to_datetime(med_df['datetime'])

# Sort by datetime
bp_df = bp_df.sort_values('datetime')
med_df = med_df.sort_values('datetime')

conn.close()

# Calculate statistics
start_date = bp_df['datetime'].min().strftime('%Y-%m-%d')
end_date = bp_df['datetime'].max().strftime('%Y-%m-%d')
total_readings = len(bp_df)
avg_systolic = bp_df['systolic_bp'].mean()
avg_diastolic = bp_df['diastolic_bp'].mean()
avg_hr = bp_df['heart_rate'].mean()
total_meds = len(med_df)
normal_count = len(bp_df[(bp_df['systolic_bp'] < 120) & (bp_df['diastolic_bp'] < 80)])
normal_pct = normal_count / len(bp_df) * 100
elevated_count = len(bp_df[(bp_df['systolic_bp'] >= 120) & (bp_df['systolic_bp'] < 130) & (bp_df['diastolic_bp'] < 80)])
elevated_pct = elevated_count / len(bp_df) * 100
high_count = len(bp_df[(bp_df['systolic_bp'] >= 130) | (bp_df['diastolic_bp'] >= 80)])
high_pct = high_count / len(bp_df) * 100
days = (bp_df['datetime'].max() - bp_df['datetime'].min()).days

# Chart 1: Blood Pressure Trends Over Time
fig1 = go.Figure()

fig1.add_trace(go.Scatter(
    x=bp_df['datetime'],
    y=bp_df['systolic_bp'],
    mode='lines+markers',
    name='Systolic BP',
    line=dict(color='#e74c3c', width=2),
    marker=dict(size=6)
))

fig1.add_trace(go.Scatter(
    x=bp_df['datetime'],
    y=bp_df['diastolic_bp'],
    mode='lines+markers',
    name='Diastolic BP',
    line=dict(color='#3498db', width=2),
    marker=dict(size=6)
))

fig1.add_hline(y=120, line_dash="dash", line_color="orange",
               annotation_text="Systolic: Elevated (120)", annotation_position="right")
fig1.add_hline(y=130, line_dash="dash", line_color="red",
               annotation_text="Systolic: High (130)", annotation_position="right")
fig1.add_hline(y=80, line_dash="dash", line_color="orange",
               annotation_text="Diastolic: High (80)", annotation_position="right")

fig1.update_layout(
    title='Blood Pressure Trends Over Time',
    xaxis_title='Date',
    yaxis_title='Blood Pressure (mmHg)',
    hovermode='x unified',
    height=500,
    showlegend=True
)

# Chart 2: Heart Rate Over Time
fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=bp_df['datetime'],
    y=bp_df['heart_rate'],
    mode='lines+markers',
    name='Heart Rate',
    line=dict(color='#2ecc71', width=2),
    marker=dict(size=6),
    fill='tozeroy',
    fillcolor='rgba(46, 204, 113, 0.1)'
))

fig2.add_hline(y=60, line_dash="dash", line_color="gray",
               annotation_text="Normal Lower Limit (60)", annotation_position="right")
fig2.add_hline(y=100, line_dash="dash", line_color="orange",
               annotation_text="Normal Upper Limit (100)", annotation_position="right")

fig2.update_layout(
    title='Heart Rate Over Time',
    xaxis_title='Date',
    yaxis_title='Heart Rate (bpm)',
    hovermode='x unified',
    height=400
)

# Chart 3: Daily Averages with Box Plot
fig3 = make_subplots(rows=1, cols=3, subplot_titles=('Systolic BP', 'Diastolic BP', 'Heart Rate'))

fig3.add_trace(go.Box(y=bp_df['systolic_bp'], name='Systolic', marker_color='#e74c3c'), row=1, col=1)
fig3.add_trace(go.Box(y=bp_df['diastolic_bp'], name='Diastolic', marker_color='#3498db'), row=1, col=2)
fig3.add_trace(go.Box(y=bp_df['heart_rate'], name='Heart Rate', marker_color='#2ecc71'), row=1, col=3)

fig3.update_layout(
    title='Distribution of Blood Pressure and Heart Rate',
    height=400,
    showlegend=False
)

# Chart 4: Medication Timeline
fig4 = go.Figure()

colors = {'坎地沙坦 (Candesartan)': '#9b59b6',
          '乐卡地平 (Lercanidipine)': '#e67e22',
          '美托洛尔 (Metoprolol)': '#1abc9c'}

for med_name in med_df['medication_name'].unique():
    med_data = med_df[med_df['medication_name'] == med_name]
    fig4.add_trace(go.Scatter(
        x=med_data['datetime'],
        y=med_data['dosage'],
        mode='markers',
        name=med_name,
        marker=dict(size=12, color=colors.get(med_name, '#34495e')),
        text=med_data['dosage'],
        hovertemplate='%{x}<br>Dosage: %{y}<extra></extra>'
    ))

fig4.update_layout(
    title='Medication Timeline and Dosages',
    xaxis_title='Date',
    yaxis_title='Dosage',
    height=400,
    hovermode='closest'
)

# Chart 5: Time of Day Analysis
bp_df['hour'] = bp_df['datetime'].dt.hour
hourly_avg = bp_df.groupby('hour').agg({
    'systolic_bp': 'mean',
    'diastolic_bp': 'mean',
    'heart_rate': 'mean'
}).reset_index()

fig5 = go.Figure()

fig5.add_trace(go.Bar(
    x=hourly_avg['hour'],
    y=hourly_avg['systolic_bp'],
    name='Systolic BP',
    marker_color='#e74c3c'
))

fig5.add_trace(go.Bar(
    x=hourly_avg['hour'],
    y=hourly_avg['diastolic_bp'],
    name='Diastolic BP',
    marker_color='#3498db'
))

fig5.update_layout(
    title='Average Blood Pressure by Time of Day',
    xaxis_title='Hour of Day',
    yaxis_title='Blood Pressure (mmHg)',
    height=400,
    barmode='group'
)

# Chart 6: Correlation Analysis (BP around medication times)
med_impact = []
for idx, med_row in med_df.iterrows():
    med_time = med_row['datetime']
    nearby_readings = bp_df[
        (bp_df['datetime'] >= med_time) &
        (bp_df['datetime'] <= med_time + pd.Timedelta(hours=3))
    ]
    for _, bp_row in nearby_readings.iterrows():
        hours_after = (bp_row['datetime'] - med_time).total_seconds() / 3600
        med_impact.append({
            'medication': med_row['medication_name'],
            'hours_after': hours_after,
            'systolic': bp_row['systolic_bp'],
            'diastolic': bp_row['diastolic_bp']
        })

if med_impact:
    med_impact_df = pd.DataFrame(med_impact)

    fig6 = make_subplots(rows=1, cols=2, subplot_titles=('Systolic BP', 'Diastolic BP'))

    for med_name in med_impact_df['medication'].unique():
        med_data = med_impact_df[med_impact_df['medication'] == med_name]

        fig6.add_trace(go.Scatter(
            x=med_data['hours_after'],
            y=med_data['systolic'],
            mode='markers',
            name=med_name,
            marker=dict(size=8, color=colors.get(med_name, '#34495e')),
            legendgroup=med_name
        ), row=1, col=1)

        fig6.add_trace(go.Scatter(
            x=med_data['hours_after'],
            y=med_data['diastolic'],
            mode='markers',
            name=med_name,
            marker=dict(size=8, color=colors.get(med_name, '#34495e')),
            showlegend=False,
            legendgroup=med_name
        ), row=1, col=2)

    fig6.update_xaxes(title_text="Hours After Medication", row=1, col=1)
    fig6.update_xaxes(title_text="Hours After Medication", row=1, col=2)
    fig6.update_yaxes(title_text="mmHg", row=1, col=1)
    fig6.update_yaxes(title_text="mmHg", row=1, col=2)

    fig6.update_layout(
        title='Blood Pressure Response After Medication (0-3 hours)',
        height=400
    )
else:
    fig6 = go.Figure()
    fig6.add_annotation(text="Not enough data for medication impact analysis",
                       xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
    fig6.update_layout(title='Blood Pressure Response After Medication', height=400)

# Convert figures to HTML divs
fig1_html = fig1.to_html(full_html=False, include_plotlyjs=False, div_id='chart1')
fig2_html = fig2.to_html(full_html=False, include_plotlyjs=False, div_id='chart2')
fig3_html = fig3.to_html(full_html=False, include_plotlyjs=False, div_id='chart3')
fig4_html = fig4.to_html(full_html=False, include_plotlyjs=False, div_id='chart4')
fig5_html = fig5.to_html(full_html=False, include_plotlyjs=False, div_id='chart5')
fig6_html = fig6.to_html(full_html=False, include_plotlyjs=False, div_id='chart6')

# Create HTML report
html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Blood Pressure Analysis Report</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 40px;
            border-left: 4px solid #3498db;
            padding-left: 10px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin: 5px 0;
        }}
        .stat-card .unit {{
            font-size: 14px;
            opacity: 0.8;
        }}
        .chart {{
            margin: 30px 0;
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        .insight {{
            background-color: #e8f4f8;
            border-left: 4px solid #3498db;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .insight h3 {{
            margin-top: 0;
            color: #2980b9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Blood Pressure & Medication Analysis Report</h1>
        <p><strong>Analysis Period:</strong> {start_date} to {end_date}</p>

        <h2>📈 Summary Statistics</h2>
        <div class="summary">
            <div class="stat-card">
                <h3>Total Readings</h3>
                <div class="value">{total_readings}</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                <h3>Average Systolic BP</h3>
                <div class="value">{avg_systolic:.1f}</div>
                <div class="unit">mmHg</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <h3>Average Diastolic BP</h3>
                <div class="value">{avg_diastolic:.1f}</div>
                <div class="unit">mmHg</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <h3>Average Heart Rate</h3>
                <div class="value">{avg_hr:.1f}</div>
                <div class="unit">bpm</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <h3>Total Medications</h3>
                <div class="value">{total_meds}</div>
                <div class="unit">doses</div>
            </div>
        </div>

        <div class="insight">
            <h3>🎯 Blood Pressure Classification</h3>
            <p><strong>Normal readings:</strong> {normal_count} ({normal_pct:.1f}%)</p>
            <p><strong>Elevated readings:</strong> {elevated_count} ({elevated_pct:.1f}%)</p>
            <p><strong>High readings:</strong> {high_count} ({high_pct:.1f}%)</p>
        </div>

        <h2>📉 Blood Pressure Trends</h2>
        <div class="chart">
            {fig1_html}
        </div>

        <h2>💓 Heart Rate Monitoring</h2>
        <div class="chart">
            {fig2_html}
        </div>

        <h2>📊 Statistical Distribution</h2>
        <div class="chart">
            {fig3_html}
        </div>

        <h2>💊 Medication Schedule</h2>
        <div class="chart">
            {fig4_html}
        </div>

        <h2>🕐 Time of Day Patterns</h2>
        <div class="chart">
            {fig5_html}
        </div>

        <h2>🔬 Medication Impact Analysis</h2>
        <div class="chart">
            {fig6_html}
        </div>

        <div class="insight">
            <h3>📝 Key Observations</h3>
            <ul>
                <li>The patient has {total_readings} blood pressure readings over {days} days</li>
                <li>Three medications are being taken: Candesartan, Lercanidipine, and Metoprolol</li>
                <li>Average blood pressure: {avg_systolic:.1f}/{avg_diastolic:.1f} mmHg</li>
                <li>Average heart rate: {avg_hr:.1f} bpm</li>
            </ul>
        </div>
    </div>
</body>
</html>
"""

# Save HTML file
with open('bp_analysis_report.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✓ Analysis complete!")
print("✓ Report generated: bp_analysis_report.html")
print("\nYou can open the file in your web browser to view the interactive graphs.")
