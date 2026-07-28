# ⚡ Texas Grid Resilience & Power Generation Pipeline

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-app-name.streamlit.app)

An end-to-end data engineering, feature engineering, and predictive modeling system designed to forecast monthly power plant utilization and evaluate grid resilience across the Greater Houston area (Harris, Fort Bend, Montgomery, Brazoria, and Galveston counties).

By combining localized weather extremes, fuel type characteristics, and historical generation trends, this project delivers a predictive risk framework to identify vulnerable assets before grid stress escalates.

Data source: [Catalyst Cooperative PUDL Dataset on Kaggle](https://www.kaggle.com/datasets/catalystcooperative/pudl-project)
---

## 🌐 Live Interactive Dashboard

👉 **[Click here to launch the Live Streamlit Dashboard]([https://texasgridpipeline-mflusckyq9bzgjkxjmnxfu.streamlit.app](https://texasgridpipeline-mflusckyq9bzgjkxjmnxfu.streamlit.app)**

*Simulate weather anomalies, view critical plant leaderboards, and inspect model feature importance in real-time.*

---

## 📌 Project Architecture & Objective

The primary objective is to forecast monthly plant-level utilization (`utilization_pct`) and categorize grid risk during severe weather conditions. 

```text
[MySQL: pudl_analysis] ➔ [Pandas ETL & Feature Eng.] ➔ [Grouped Time-Series Split] ➔ [XGBoost + CatBoost Delta Blend] ➔ [Streamlit Dashboard & Risk Matrix]

🛠️ Data Pipeline & Ingestion
Database Connection: Connects to a local MySQL database (pudl_analysis) using SQLAlchemy.
Extraction: Ingests relational view v_houston_grid_resilience into Pandas DataFrames.
Pipeline Integration: Combines raw monthly generation data (EIA-923 / EIA-860 via PUDL) with localized meteorological features.
🔬 Feature Engineering & Data Quality Controls
Feature Engineering
Temperature Metrics: Computes mean monthly temperature:
TMEAN= 
2
TMAX+TMIN
​	
 
Degree Days: Derives Heating Degree Days (HDD) and Cooling Degree Days (CDD) relative to a 65°F baseline:
HDD=max(0,65−TMEAN)
CDD=max(0,TMEAN−65)
Temporal Lags: Creates 1-period (1-month) historical lag features for TMEAN (TMEAN_lag1) and utilization_pct (utilization_pct_lag1) grouped strictly by plant_id_eia.
Categorical & Seasonal Encoding: Applies one-hot encoding to fuel_type_code_pudl and extracts seasonal month indicators.
Data Quality & EDA
Range Validation: Scans utilization_pct for anomalies outside 0–100% and clips extreme values.
Chronological Sorting: Enforces strict sorting by report_date and plant_id_eia.
Non-Operational Filtering: Analyzes the proportion of plants at 0% utilization to flag non-operational or offline assets.
Correlation Analysis: Evaluates linear and rank dependencies between plant utilization, lagged metrics, and degree days.
📐 Validation Strategy
Crucial Engineering Fix: Panel Data Leakage Prevention
Standard row-based TimeSeriesSplit creates severe data leakage in panel datasets because multiple power plants share the exact same report_date. Standard splits allow the model to train on Plant A's data in June 2023 while predicting Plant B's data in the same month.
Solution: Implemented Date-Grouped Time-Series Splitting based on unique report_date values. This ensures entire monthly blocks across all plants remain intact, eliminating contemporaneous data leakage across folds.
🤖 Baseline & Modeling Breakthroughs
Baseline Performance
Naive Persistence Benchmark: Using utilization_pct_lag1 directly as the prediction yields:
RMSE: ≈17.84
R 
2
 : ≈0.496
Target Transformation & Model Exploration
Ridge Regression: Outperformed the baseline when predicting raw utilization directly.
CatBoost: Initially underperformed on raw utilization due to lag dominance.
Target Delta Breakthrough: Refactored models to predict the change in utilization from last month (Δutilization=utilization 
t
​	
 −utilization 
t−1
​	
 ) rather than raw utilization.
XGBoost: Delivered strong performance on utilization deltas, specifically across recent time-series folds.
Model Ensemble
Blended Predictions: Combining XGBoost and CatBoost delta predictions yielded the highest overall stability and accuracy:
Final Ensemble R 
2
 : ≈0.6855
Final Ensemble MAE: ≈8.63%
💡 Key Engineering Insights
Predicting Deltas Neutralizes Lag Dominance: Predicting month-over-month changes (Δutilization) forces the model to learn structural relationships instead of overly relying on past state persistence.
Fuel Type Importance Surges: Removing lag dominance revealed that fuel_type_code_pudl (e.g., natural gas, coal, solar) is one of the strongest predictive signals for ramp capability.
Weather Response Curves: Models successfully learned expected nonlinear physical dynamics:
U-Shaped Demand Curve: Observed for TMEAN across thermal extremes.
Ramp Behavior: Clear linear ramp response for HDD (winter heating demand) and CDD (summer cooling demand).
⚠️ Resilience Risk Matrix Framework
The risk framework evaluates plant vulnerability by blending predictive output, weather severity, and model variance across three operational tiers:
Plaintext
  [Predictive Model Outputs] ──┐
  [Extreme Weather Signals]  ──┼──> [Risk Matrix Engine] ──>  🟢 STABLE
  [Utilization Ramp Magnitude]─┤                             🟡 ELEVATED
  [Model Disagreement Variance]┘                             🔴 CRITICAL
Risk Tiers
🟢 STABLE: Low plant utilization stress, moderate weather conditions, and low model variance.
🟡 ELEVATED: Moderate plant ramp rates, elevated HDD/CDD load forecasts, or moderate prediction variance between CatBoost and XGBoost.
🔴 CRITICAL: High predicted utilization nearing capacity limits, severe weather events, large utilization swings, or high model disagreement.
📊 Streamlit Dashboard (app.py)
The repository includes an interactive Streamlit application designed for grid monitoring:
Interactive Weather Simulation: Adjust simulated monthly temperature, HDD, and CDD to evaluate grid stress under synthetic heatwaves or arctic blasts.
Risk Tier Summary: Real-time classification of plants into STABLE, ELEVATED, and CRITICAL buckets.
Critical Plant Leaderboard: Ranked list of high-risk power generation assets requiring dispatch oversight.
Weather Response Curves: Interactive visualizations of temperature vs. utilization ramps by fuel type.
Feature Importance Panel: Inspection of SHAP values and tree split counts for XGBoost and CatBoost models.
🚀 Quickstart Guide
1. Requirements & Environment
Bash
git clone [https://github.com/AxelPalapa/texas_grid_pipeline.git](https://github.com/AxelPalapa/texas_grid_pipeline.git)
cd texas_grid_pipeline
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Configure Database Credentials
Create a .env file in the root folder:
Ini, TOML
DB_URL=mysql+mysqlconnector://root:YOUR_PASSWORD@localhost:3306/pudl_analysis
3. Run Notebooks & Web App
Bash
# 1. Run ETL Pipeline and Feature Engineering inside notebooks/
# 2. Launch the Streamlit Dashboard locally:
streamlit run app.py
