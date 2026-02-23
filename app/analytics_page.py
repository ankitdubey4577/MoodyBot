"""
Analytics Page with Advanced Visualizations
Displays productivity metrics, patterns, predictions, and anomalies
"""
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import pandas as pd


def render_health_score_gauge(health_score: float, status: str):
    """Render health score gauge chart"""
    # Color based on status
    color_map = {
        'excellent': '#10b981',
        'good': '#3b82f6',
        'concerning': '#f59e0b',
        'critical': '#ef4444'
    }
    color = color_map.get(status, '#6b7280')

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=health_score,
        title={'text': "Health Score", 'font': {'size': 24}},
        delta={'reference': 70, 'increasing': {'color': "#10b981"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 40], 'color': '#fee2e2'},
                {'range': [40, 60], 'color': '#fef3c7'},
                {'range': [60, 80], 'color': '#dbeafe'},
                {'range': [80, 100], 'color': '#d1fae5'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 90
            }
        }
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#374151", 'family': "Arial"}
    )

    return fig


def render_productivity_trend_chart(daily_metrics: list):
    """Render productivity trend line chart"""
    if not daily_metrics:
        return None

    dates = [m['date'] for m in daily_metrics]
    scores = [m['productivity_score'] for m in daily_metrics]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=dates,
        y=scores,
        mode='lines+markers',
        name='Productivity Score',
        line=dict(color='#3b82f6', width=3),
        marker=dict(size=8, color='#3b82f6'),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)'
    ))

    fig.update_layout(
        title="Weekly Productivity Trend",
        xaxis_title="Date",
        yaxis_title="Score (0-100)",
        hovermode='x unified',
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#374151"},
        yaxis=dict(range=[0, 100])
    )

    return fig


def render_productive_hours_chart(hourly_breakdown: dict):
    """Render productive hours bar chart"""
    if not hourly_breakdown:
        return None

    hours = sorted(hourly_breakdown.keys())
    scores = [hourly_breakdown[h]['productivity_score'] for h in hours]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=hours,
        y=scores,
        marker_color='#10b981',
        text=scores,
        textposition='auto',
        hovertemplate='Hour: %{x}<br>Score: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Productivity by Hour of Day",
        xaxis_title="Hour",
        yaxis_title="Productivity Score",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#374151"}
    )

    return fig


def render_weekly_pattern_chart(daily_breakdown: dict):
    """Render weekly pattern radar chart"""
    if not daily_breakdown:
        return None

    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    completion_rates = [
        daily_breakdown.get(day, {}).get('completion_rate', 0) * 100
        for day in days
    ]

    fig = go.Figure()

    fig.add_trace(go.Scatterpolar(
        r=completion_rates,
        theta=days,
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)',
        line=dict(color='#3b82f6', width=2),
        marker=dict(size=8, color='#3b82f6'),
        name='Completion Rate'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        title="Weekly Completion Pattern",
        height=400,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#374151"}
    )

    return fig


def render_burnout_risk_chart(burnout_trend: dict):
    """Render burnout risk gauge"""
    current_risk = burnout_trend.get('current_risk', 0) * 100
    predicted_risk = burnout_trend.get('predicted_risk_7_days', 0) * 100

    # Determine color
    if predicted_risk >= 70:
        color = '#ef4444'  # Red
    elif predicted_risk >= 50:
        color = '#f59e0b'  # Orange
    elif predicted_risk >= 30:
        color = '#fbbf24'  # Yellow
    else:
        color = '#10b981'  # Green

    fig = go.Figure()

    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=predicted_risk,
        title={'text': "Burnout Risk (7-day forecast)", 'font': {'size': 20}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1},
            'bar': {'color': color},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 30], 'color': '#d1fae5'},
                {'range': [30, 50], 'color': '#fef3c7'},
                {'range': [50, 70], 'color': '#fed7aa'},
                {'range': [70, 100], 'color': '#fecaca'}
            ],
            'threshold': {
                'line': {'color': "darkred", 'width': 4},
                'thickness': 0.75,
                'value': 70
            }
        },
        number={'suffix': "%"}
    ))

    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=50, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        font={'color': "#374151"}
    )

    return fig


def render_mood_correlation_chart(mood_productivity: dict):
    """Render mood-productivity correlation chart"""
    if not mood_productivity:
        return None

    moods = list(mood_productivity.keys())
    task_counts = [mood_productivity[m]['completed'] for m in moods]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=moods,
        y=task_counts,
        marker_color='#8b5cf6',
        text=task_counts,
        textposition='auto',
        hovertemplate='Mood: %{x}<br>Tasks: %{y}<extra></extra>'
    ))

    fig.update_layout(
        title="Tasks Completed by Mood",
        xaxis_title="Mood",
        yaxis_title="Tasks Completed",
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font={'color': "#374151"}
    )

    return fig


def render_task_completion_predictions(task_predictions: list):
    """Render task completion predictions"""
    if not task_predictions:
        st.info("No pending tasks to predict")
        return

    for pred in task_predictions[:5]:  # Top 5
        task_title = pred.get('title', 'Unknown Task')
        probability = pred.get('completion_probability', 0) * 100
        confidence = pred.get('confidence', 'medium')

        # Color based on probability
        if probability >= 70:
            color = "green"
            icon = "✅"
        elif probability >= 50:
            color = "blue"
            icon = "🔵"
        else:
            color = "orange"
            icon = "⚠️"

        col1, col2, col3 = st.columns([5, 2, 1])
        with col1:
            st.markdown(f"**{task_title}**")
        with col2:
            st.markdown(f"<span style='color: {color}'>{probability:.0f}%</span>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"{icon}")


def render_anomaly_alerts(anomaly_report: dict):
    """Render anomaly detection alerts"""
    all_alerts = anomaly_report.get('all_alerts', [])
    priority_recs = anomaly_report.get('priority_recommendations', [])

    if not all_alerts and not priority_recs:
        st.success("✅ No anomalies detected. Everything looks healthy!")
        return

    # Show priority recommendations first
    if priority_recs:
        st.markdown("### 🚨 Priority Actions")
        for rec in priority_recs:
            if "URGENT" in rec:
                st.error(rec)
            elif "HIGH" in rec:
                st.warning(rec)
            else:
                st.info(rec)

    # Show all alerts
    if all_alerts:
        st.markdown("### ⚠️ Detected Issues")
        for alert in all_alerts:
            st.warning(alert)


def render_insights_cards(insights: list):
    """Render insight cards"""
    if not insights:
        return

    for insight in insights[:5]:  # Top 5 insights
        # Extract emoji and text
        if insight.startswith('✅') or insight.startswith('📈') or insight.startswith('🌟'):
            st.success(insight)
        elif insight.startswith('⚠️') or insight.startswith('📉'):
            st.warning(insight)
        elif insight.startswith('💡') or insight.startswith('📅'):
            st.info(insight)
        else:
            st.info(insight)


def render_analytics_page(dashboard_data: dict):
    """Main analytics page renderer"""

    if 'error' in dashboard_data:
        st.error(f"Analytics Error: {dashboard_data['error']}")
        st.info("Analytics system requires completed tasks and mood data to generate insights.")
        return

    # Executive Summary Section
    st.markdown("## 📊 Executive Summary")

    exec_summary = dashboard_data.get('executive_summary', {})
    health_score = exec_summary.get('health_score', 0)
    status = exec_summary.get('status', 'unknown')
    status_message = exec_summary.get('status_message', '')

    col1, col2 = st.columns([1, 2])

    with col1:
        # Health score gauge
        gauge_fig = render_health_score_gauge(health_score, status)
        if gauge_fig:
            st.plotly_chart(gauge_fig, use_container_width=True)

    with col2:
        # Key metrics
        st.markdown("### Key Metrics")
        key_metrics = exec_summary.get('key_metrics', {})

        met_col1, met_col2, met_col3 = st.columns(3)

        with met_col1:
            st.metric(
                "Today's Productivity",
                f"{key_metrics.get('today_productivity', 0):.0f}/100",
                delta=None
            )
            st.metric(
                "Completion Rate",
                f"{key_metrics.get('completion_rate', 0):.1f}%",
                delta=None
            )

        with met_col2:
            st.metric(
                "Best Time",
                key_metrics.get('best_time_of_day', 'Unknown'),
                delta=None
            )
            st.metric(
                "Weekly Outlook",
                key_metrics.get('weekly_outlook', 'Unknown').title(),
                delta=None
            )

        with met_col3:
            burnout_risk = key_metrics.get('burnout_risk', 0)
            st.metric(
                "Burnout Risk",
                f"{burnout_risk:.0f}%",
                delta=None,
                delta_color="inverse"
            )
            st.metric(
                "Anomalies",
                key_metrics.get('anomalies_detected', 0),
                delta=None,
                delta_color="inverse"
            )

    # Status message
    if status_message:
        if status == 'excellent':
            st.success(status_message)
        elif status == 'good':
            st.info(status_message)
        elif status == 'concerning':
            st.warning(status_message)
        else:
            st.error(status_message)

    # Top Insights
    top_insights = exec_summary.get('top_insights', [])
    if top_insights:
        st.markdown("### 💡 Top Insights")
        render_insights_cards(top_insights)

    st.markdown("---")

    # Tabs for detailed views
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Productivity", "🔍 Patterns", "🔮 Predictions", "⚠️ Anomalies"
    ])

    with tab1:
        # Productivity Section
        st.markdown("### Productivity Metrics")

        productivity = dashboard_data.get('productivity', {})
        today_metrics = productivity.get('today', {})
        weekly_metrics = productivity.get('this_week', {})

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Today")
            st.metric("Tasks Completed", today_metrics.get('completed_tasks', 0))
            st.metric("Total Time (min)", today_metrics.get('total_time_spent_minutes', 0))
            st.metric("Productivity Score", f"{today_metrics.get('productivity_score', 0):.1f}/100")

        with col2:
            st.markdown("#### This Week")
            st.metric("Total Completed", weekly_metrics.get('total_completed', 0))
            st.metric("Avg Completion Rate", f"{weekly_metrics.get('avg_completion_rate', 0)*100:.1f}%")
            st.metric("Avg Productivity", f"{weekly_metrics.get('avg_productivity_score', 0):.1f}/100")

        # Productivity trend chart
        daily_breakdown = weekly_metrics.get('daily_breakdown', [])
        if daily_breakdown:
            trend_fig = render_productivity_trend_chart(daily_breakdown)
            if trend_fig:
                st.plotly_chart(trend_fig, use_container_width=True)

        # Focus metrics
        focus_metrics = productivity.get('focus', {})
        if focus_metrics:
            st.markdown("#### Focus & Deep Work")
            focus_col1, focus_col2, focus_col3 = st.columns(3)
            with focus_col1:
                st.metric("Deep Work Hours", f"{focus_metrics.get('deep_work_hours', 0):.1f}")
            with focus_col2:
                st.metric("Deep Work Tasks", focus_metrics.get('deep_work_tasks', 0))
            with focus_col3:
                st.metric("Focus Score", f"{focus_metrics.get('focus_score', 0)}/100")

    with tab2:
        # Patterns Section
        st.markdown("### Behavioral Patterns")

        patterns = dashboard_data.get('patterns', {})
        productive_hours = patterns.get('productive_hours', {})
        mood_correlations = patterns.get('mood_correlations', {})
        weekly_patterns = patterns.get('weekly_patterns', {})

        col1, col2 = st.columns(2)

        with col1:
            # Productive hours
            hourly_breakdown = productive_hours.get('hourly_breakdown', {})
            if hourly_breakdown:
                hours_fig = render_productive_hours_chart(hourly_breakdown)
                if hours_fig:
                    st.plotly_chart(hours_fig, use_container_width=True)

            # Best time info
            best_time = productive_hours.get('best_time_of_day', 'Unknown')
            st.info(f"🌟 Your most productive time is **{best_time}**")

        with col2:
            # Weekly pattern
            daily_breakdown_patterns = weekly_patterns.get('daily_breakdown', {})
            if daily_breakdown_patterns:
                weekly_fig = render_weekly_pattern_chart(daily_breakdown_patterns)
                if weekly_fig:
                    st.plotly_chart(weekly_fig, use_container_width=True)

            # Best day info
            best_day = weekly_patterns.get('best_day', 'Unknown')
            st.info(f"📅 Your best day is **{best_day}**")

        # Mood correlation
        st.markdown("#### Mood-Productivity Correlation")
        mood_productivity = mood_correlations.get('mood_productivity', {})
        if mood_productivity:
            mood_fig = render_mood_correlation_chart(mood_productivity)
            if mood_fig:
                st.plotly_chart(mood_fig, use_container_width=True)

    with tab3:
        # Predictions Section
        st.markdown("### Predictive Insights")

        predictions = dashboard_data.get('predictions', {})

        # Weekly forecast
        weekly_forecast = predictions.get('weekly_productivity_forecast', {})
        if weekly_forecast:
            st.markdown("#### 📈 Weekly Productivity Forecast")
            forecast_col1, forecast_col2, forecast_col3 = st.columns(3)

            with forecast_col1:
                st.metric(
                    "Forecasted Score",
                    f"{weekly_forecast.get('forecasted_productivity_score', 0):.0f}/100"
                )
            with forecast_col2:
                trend = weekly_forecast.get('trend', 'stable')
                trend_emoji = "📈" if trend == 'increasing' else "📉" if trend == 'decreasing' else "➡️"
                st.metric("Trend", f"{trend_emoji} {trend.title()}")
            with forecast_col3:
                outlook = weekly_forecast.get('outlook', 'unknown')
                st.metric("Outlook", outlook.title())

            forecast_message = weekly_forecast.get('message', '')
            if forecast_message:
                if 'excellent' in forecast_message.lower():
                    st.success(forecast_message)
                elif 'good' in forecast_message.lower():
                    st.info(forecast_message)
                else:
                    st.warning(forecast_message)

        # Burnout risk
        burnout_trend = predictions.get('burnout_risk_trend', {})
        if burnout_trend:
            st.markdown("#### 🔥 Burnout Risk Trend")

            burnout_fig = render_burnout_risk_chart(burnout_trend)
            if burnout_fig:
                st.plotly_chart(burnout_fig, use_container_width=True)

            warning = burnout_trend.get('warning')
            if warning:
                st.error(warning)

            recommendation = burnout_trend.get('recommendation', '')
            if recommendation:
                st.info(f"**Recommendation:** {recommendation}")

        # Task completion predictions
        st.markdown("#### ✅ Task Completion Predictions")
        task_predictions = predictions.get('task_completion_predictions', [])
        render_task_completion_predictions(task_predictions)

        # Optimal schedule
        optimal_schedule = predictions.get('optimal_schedule', {})
        if optimal_schedule.get('suggestions'):
            st.markdown("#### 🗓️ Optimal Schedule Suggestions")
            for suggestion in optimal_schedule['suggestions'][:3]:
                st.info(f"**{suggestion['title']}**: {suggestion['suggested_time']} - {suggestion['reason']}")

    with tab4:
        # Anomalies Section
        st.markdown("### Anomaly Detection")

        anomalies = dashboard_data.get('anomalies', {})

        # Overall status
        overall_status = anomalies.get('overall_status', 'unknown')
        anomaly_count = anomalies.get('anomaly_count', 0)

        status_col1, status_col2 = st.columns(2)
        with status_col1:
            if overall_status == 'healthy':
                st.success(f"✅ Status: **{overall_status.title()}**")
            elif overall_status == 'warning':
                st.warning(f"⚠️ Status: **{overall_status.title()}**")
            else:
                st.error(f"🚨 Status: **{overall_status.title()}**")

        with status_col2:
            st.metric("Anomalies Detected", anomaly_count, delta_color="inverse")

        # Anomaly alerts
        render_anomaly_alerts(anomalies)

        # Detailed detections
        detections = anomalies.get('detections', {})

        st.markdown("### Detailed Analysis")

        det_col1, det_col2 = st.columns(2)

        with det_col1:
            # Unusual hours
            unusual_hours = detections.get('unusual_work_hours', {})
            if unusual_hours:
                st.markdown("#### 🌙 Work Hours")
                st.metric("Late Night Work", unusual_hours.get('late_night_count', 0))
                st.metric("Weekend Work", unusual_hours.get('weekend_count', 0))

            # Productivity drops
            productivity_drops = detections.get('productivity_drops', {})
            if productivity_drops:
                st.markdown("#### 📉 Productivity")
                drops = len(productivity_drops.get('drops_detected', []))
                st.metric("Drops Detected", drops)
                consecutive = productivity_drops.get('consecutive_low_days', 0)
                if consecutive > 0:
                    st.warning(f"{consecutive} consecutive low-productivity days")

        with det_col2:
            # Mood deterioration
            mood_deterioration = detections.get('mood_deterioration', {})
            if mood_deterioration:
                st.markdown("#### 😟 Mood Trend")
                trend = mood_deterioration.get('trend', 'unknown')
                mood_change = mood_deterioration.get('mood_change', 0)

                if trend == 'declining':
                    st.error(f"Trend: **Declining** ({mood_change:.2f})")
                elif trend == 'improving':
                    st.success(f"Trend: **Improving** (+{abs(mood_change):.2f})")
                else:
                    st.info(f"Trend: **Stable**")

            # Workload spikes
            workload_spikes = detections.get('workload_spikes', {})
            if workload_spikes:
                st.markdown("#### 📊 Workload")
                spikes = len(workload_spikes.get('spikes_detected', []))
                st.metric("Spikes Detected", spikes)
