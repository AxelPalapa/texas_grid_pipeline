import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
# ---------------------------------------------------------
st.set_page_config(
    page_title="Power Grid Operations Risk Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Power Grid Operations Risk Dashboard")
st.caption("Predictive Machine Learning Pipeline for Grid Capacity Utilization & Extreme Weather Response")

# ---------------------------------------------------------
# 2. LOAD RESOURCES
# ---------------------------------------------------------
@st.cache_resource
def load_resources():
    df = pd.read_pickle("models/df_sorted.pkl")
    xgb = joblib.load("models/joblib/model_xgb.joblib")
    cat = joblib.load("models/joblib/model_catboost.joblib")
    features = joblib.load("models/joblib/feature_cols.joblib")
    return df, xgb, cat, features

df_sorted, model_xgb, model_catboost, feature_cols = load_resources()

# ---------------------------------------------------------
# 3. SIDEBAR CONTROLS
# ---------------------------------------------------------
st.sidebar.header("🕹️ Weather Simulation Controls")
temp_offset = st.sidebar.slider(
    "Simulated Temperature Spike (+/- degrees)",
    min_value=-10.0,
    max_value=15.0,
    value=0.0,
    step=1.0
)

# ---------------------------------------------------------
# 4. PREDICTION ENGINE
# ---------------------------------------------------------
def calculate_grid_risk(df, model_xgb, model_catboost, feature_cols, temp_shift):
    data = df.copy()

    # Applying simulated temperature shift to CDD
    if temp_shift != 0 and 'CDD' in data.columns:
        data['CDD'] = (data['CDD'] + temp_shift).clip(lower=0)

    # Feature predictions
    X = data[feature_cols]
    data['xgb_pred_delta'] = model_xgb.predict(X)
    data['catboost_pred_delta'] = model_catboost.predict(X)

    # Blending and utilization calculation
    data['blended_pred_delta'] = (data['xgb_pred_delta'] + data['catboost_pred_delta']) / 2
    data['pred_utilization_pct'] = (data['utilization_pct_lag1'] + data['blended_pred_delta']).clip(0, 100)

    # Stress indicators
    data['model_disagreement'] = (data['xgb_pred_delta'] - data['catboost_pred_delta']).abs()
    data['ramp_magnitude'] = data['blended_pred_delta'].abs()

    # Risk rules
    cdd_val = data['CDD'] if 'CDD' in data.columns else 0
    hdd_val = data['HDD'] if 'HDD' in data.columns else 0

    conditions = [
        (data['pred_utilization_pct'] > 85) & ((cdd_val > 15) | (hdd_val > 6)),
        (data['ramp_magnitude'] > 20) | (data['model_disagreement'] > 5)
    ]
    choices = ['CRITICAL', 'ELEVATED']
    data['risk_tier'] = np.select(conditions, choices, default='STABLE')

    return data

df_results = calculate_grid_risk(df_sorted, model_xgb, model_catboost, feature_cols, temp_offset)

# ---------------------------------------------------------
# 5. KEY METRIC SUMMARY
# ---------------------------------------------------------
critical_count = (df_results['risk_tier'] == 'CRITICAL').sum()
elevated_count = (df_results['risk_tier'] == 'ELEVATED').sum()
stable_count = (df_results['risk_tier'] == 'STABLE').sum()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Simulated Shift", f"{temp_offset:+.1f} °F")
col2.metric("Critical Risk Facilities", critical_count, delta_color="inverse")
col3.metric("Elevated Risk Facilities", elevated_count)
col4.metric("Stable Facilities", stable_count)

st.markdown("---")

# ---------------------------------------------------------
# 6. TAB NAVIGATION LAYOUT
# ---------------------------------------------------------
tab_overview, tab_weather, tab_explain = st.tabs([
    "📊 Risk Overview & Leaderboard", 
    "🌡️ Weather Response Curves", 
    "🧠 Model Feature Importance"
])

# =========================================================
# TAB 1: EXECUTIVE OVERVIEW & LEADERBOARD
# =========================================================
with tab_overview:
    col_chart, col_empty = st.columns([2, 1])

    with col_chart:
        st.subheader("Operational Risk Tier Distribution")
        tier_counts = df_results['risk_tier'].value_counts().reset_index()
        tier_counts.columns = ['risk_tier', 'count']
        color_map = {'STABLE': '#2ecc71', 'ELEVATED': '#f39c12', 'CRITICAL': '#e74c3c'}

        fig_tier = px.bar(
            tier_counts,
            x='risk_tier',
            y='count',
            color='risk_tier',
            color_discrete_map=color_map,
            labels={'risk_tier': 'Risk Tier', 'count': 'Number of Plant Months'},
            template='plotly_white'
        )
        st.plotly_chart(fig_tier, use_container_width=True)

    st.subheader("🚨 Critical Risk Plant Leaderboard")
    critical_df = df_results[df_results['risk_tier'] == 'CRITICAL'][
        [col for col in ['plant_name_eia', 'county', 'report_date', 'pred_utilization_pct', 'CDD', 'HDD'] if col in df_results.columns]
    ].sort_values(by='pred_utilization_pct', ascending=False)

    if len(critical_df) > 0:
        st.dataframe(critical_df, use_container_width=True)
    else:
        st.info("No plants currently at CRITICAL risk under selected weather conditions.")

# =========================================================
# TAB 2: WEATHER RESPONSE CURVES (CDD, HDD, TMEAN)
# =========================================================
with tab_weather:
    st.subheader("Plant Utilization Response to Weather Variables")
    st.markdown("These curves show how average plant capacity utilization responds across binned weather ranges, comparing baseline values against model predictions.")

    def build_weather_response_plot(df, weather_col):
        if weather_col not in df.columns:
            return None

        actual_col = 'utilization_pct' if 'utilization_pct' in df.columns else 'utilization_pct_lag1'
        plot_df = df[[weather_col, 'pred_utilization_pct', actual_col]].copy()

        # Round weather values into clean bins
        plot_df['weather_bin'] = plot_df[weather_col].round()
        grouped = plot_df.groupby('weather_bin')[[actual_col, 'pred_utilization_pct']].mean().reset_index().sort_values('weather_bin')

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=grouped['weather_bin'], 
            y=grouped[actual_col],
            mode='lines+markers', 
            name='Baseline / Actual Utilization',
            line=dict(color='#2980b9', width=3)
        ))
        fig.add_trace(go.Scatter(
            x=grouped['weather_bin'], 
            y=grouped['pred_utilization_pct'],
            mode='lines+markers', 
            name='Model Prediction',
            line=dict(color='#e74c3c', width=3, dash='dot')
        ))
        fig.update_layout(
            title=f'Plant Utilization Response ({weather_col})',
            xaxis_title=weather_col,
            yaxis_title='Average Utilization (%)',
            template='plotly_white',
            hovermode='x unified',
            height=400
        )
        return fig

    # Display plots in clean sub-tabs or columns
    sub_tab_cdd, sub_tab_hdd, sub_tab_tmean = st.tabs(["Cooling Demand (CDD)", "Heating Demand (HDD)", "Mean Temp (TMEAN)"])

    with sub_tab_cdd:
        fig_cdd = build_weather_response_plot(df_results, 'CDD')
        if fig_cdd:
            st.plotly_chart(fig_cdd, use_container_width=True)
        else:
            st.warning("`CDD` column not found in dataset.")

    with sub_tab_hdd:
        fig_hdd = build_weather_response_plot(df_results, 'HDD')
        if fig_hdd:
            st.plotly_chart(fig_hdd, use_container_width=True)
        else:
            st.warning("`HDD` column not found in dataset.")

    with sub_tab_tmean:
        fig_tmean = build_weather_response_plot(df_results, 'TMEAN')
        if fig_tmean:
            st.plotly_chart(fig_tmean, use_container_width=True)
        else:
            st.warning("`TMEAN` column not found in dataset.")

# =========================================================
# TAB 3: MODEL FEATURE IMPORTANCE
# =========================================================
with tab_explain:
    st.subheader("What Factors Matter Most? (XGBoost Feature Importance)")
    st.markdown("Relative feature weights generated directly from the trained XGBoost model.")

    importance_df = pd.DataFrame({
        'Feature': feature_cols,
        'Importance': model_xgb.feature_importances_
    }).sort_values(by='Importance', ascending=True)

    fig_importance = px.bar(
        importance_df, 
        x='Importance', 
        y='Feature', 
        orientation='h',
        color='Importance',
        color_continuous_scale='Blues'
    )
    fig_importance.update_layout(
        template='plotly_white',
        showlegend=False,
        height=500
    )

    st.plotly_chart(fig_importance, use_container_width=True)
