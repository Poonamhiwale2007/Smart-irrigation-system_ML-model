import streamlit as st
import pandas as pd
import numpy as np
import joblib
import plotly.express as px
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(page_title="Smart Irrigation Analytics Dashboard", layout="wide")

st.title("🌱 Smart Irrigation Prediction & Analytics Dashboard")
st.write("Modify real-time sensor variables below to compute irrigation water volumes and visualize analytics charts.")

# Load saved model and metadata
@st.cache_resource
def load_model_artifacts():
    model = joblib.load('irrigation_rf_model.pkl')
    metadata = joblib.load('model_metadata.pkl')
    return model, metadata

# Optional: Load the crop summary data to display benchmark statistics in charts
# Updated safe version for app.py
@st.cache_data
def load_benchmark_data():
    try:
        # Tries to pull global crop benchmarks from your summary file if available
        summary_df = pd.read_csv("irrigation_dataset.xlsx - Crop Summary.csv")
        return summary_df
    except FileNotFoundError:
        # Fallback dataset automatically structured if the file isn't in the folder
        return pd.DataFrame({
            'Crop Type': ['Wheat', 'Tomato', 'Corn', 'Potato', 'Soybean', 'Vegetables', 'Rice', 'Cotton'],
            'Avg Water Req (mm)': [10.8, 16.32, 11.58, 15.13, 13.85, 16.11, 16.32, 10.58]
        })
        

try:
    model, metadata = load_model_artifacts()
    summary_df = load_benchmark_data()
    
    # Create two main structural sections: Left column for Inputs, Right column for Charts
    form_column, report_column = st.columns([1, 2], gap="large")
    
    input_data = {}
    
    with form_column:
        st.subheader("⚙️ Field & Sensor Inputs")
        
        # Section A: Crop & Soil Profile
        st.markdown("#### 🌾 Crop & Soil Profile")
        if 'crop_type' in metadata['unique_categories']:
            input_data['crop_type'] = st.selectbox("Crop Variety", metadata['unique_categories']['crop_type'])
        if 'soil_type' in metadata['unique_categories']:
            input_data['soil_type'] = st.selectbox("Soil Composition Type", metadata['unique_categories']['soil_type'])
        
        input_data['area_sqm'] = st.number_input("Field Area (sqm)", min_value=0.0, value=10000.0, step=500.0)
        input_data['target_moisture_pct'] = st.slider("Target Optimal Moisture (%)", 0.0, 100.0, 55.0)
        input_data['current_moisture_pct'] = st.slider("Current Soil Moisture (%)", 0.0, 100.0, 32.0)

        # Section B: Environmental Conditions
        st.markdown("#### 🌡️ Weather Parameters")
        if 'weather_condition' in metadata['unique_categories']:
            input_data['weather_condition'] = st.selectbox("Atmospheric State", metadata['unique_categories']['weather_condition'])
            
        input_data['temperature_c'] = st.slider("Ambient Temperature (°C)", -5.0, 50.0, 24.0)
        input_data['humidity_pct'] = st.slider("Relative Air Humidity (%)", 0.0, 100.0, 60.0)
        input_data['wind_speed_kmh'] = st.number_input("Measured Wind Speed (km/h)", min_value=0.0, value=12.5)
        input_data['rainfall_mm'] = st.number_input("Precipitation last 24h (mm)", min_value=0.0, value=0.0)

        # Section C: Advanced Growth Metrics
        st.markdown("#### 💧 Moisture Indices")
        input_data['days_since_last_irrigation'] = st.number_input("Interval Since Last Run (Days)", min_value=0.0, value=3.0)
        input_data['evapotranspiration_mm_day'] = st.number_input("Evapotranspiration (mm/day)", min_value=0.0, value=4.2)
        input_data['crop_coefficient_kc'] = st.number_input("Crop Coefficient (Kc)", min_value=0.0, max_value=2.0, value=0.85)
        
        st.markdown("---")
        submit_btn = st.button("🔮 Calculate & Update Visualizations", type="primary", use_container_width=True)

    with report_column:
        st.subheader("📊 Operational Analytics & Performance Charts")
        
        # Enforce correct pipeline alignment order
        feature_order = metadata['numerical_cols'] + metadata['categorical_cols']
        input_df = pd.DataFrame([input_data])[feature_order]
        
        # Calculate initial or updated prediction
        prediction_mm = model.predict(input_df)[0]
        prediction_mm = max(0.0, prediction_mm) # Bound lower value to 0
        total_liters = prediction_mm * input_data['area_sqm']
        
        # Display key summary KPI metric cards
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric(label="Predicted Water Depth", value=f"{prediction_mm:.2f} mm")
        with metric_col2:
            st.metric(label="Total Volumetric Delivery", value=f"{total_liters:,.2f} Liters")
        with metric_col3:
            deficit = max(0.0, input_data['target_moisture_pct'] - input_data['current_moisture_pct'])
            st.metric(label="Moisture Deficit to Target", value=f"{deficit:.1f} %")
            
        st.markdown("---")
        
        # --- GRAPH 1: Moisture Level Status (Gauge Chart) ---
        st.write("##### 📉 Current vs. Target Soil Moisture Balance")
        
        fig_gauge = go.Figure(go.Indicator(
            mode = "gauge+number+delta",
            value = input_data['current_moisture_pct'],
            domain = {'x': [0, 1], 'y': [0, 1]},
            delta = {'reference': input_data['target_moisture_pct'], 'position': "top", 'relative': False, 'valueformat': '.1f'},
            title = {'text': "Current Moisture level relative to Optimal Crop Threshold (%)", 'font': {'size': 14}},
            gauge = {
                'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#1f77b4"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, input_data['target_moisture_pct']], 'color': '#ffcccc'},
                    {'range': [input_data['target_moisture_pct'], 100], 'color': '#e0f2f1'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': input_data['target_moisture_pct']
                }
            }
        ))
        fig_gauge.update_layout(height=280, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # --- GRAPH 2: Benchmark Comparison Chart ---
        st.write("##### 🌾 Context Comparison: Scenario Prediction vs Historical Crop Requirements")
        
        # Dynamically append user data into comparative copy of baseline frame
        temp_summary = summary_df.copy()
        
        # Rename column mapping variations from CSV if present
        if 'Crop Type' in temp_summary.columns:
            crop_col, water_col = 'Crop Type', 'Avg Water Req (mm)'
        else:
            crop_col, water_col = temp_summary.columns[0], temp_summary.columns[2]
            
        # Add a custom row representing the current real-time user session
        user_row = pd.DataFrame({
            crop_col: [f"CURRENT INPUT ({input_data['crop_type']})"],
            water_col: [prediction_mm]
        })
        
        plot_df = pd.concat([temp_summary[[crop_col, water_col]], user_row], ignore_index=True)
        
        # Color coding configuration: Highlight user's custom run distinctly from benchmark crops
        colors = ['#aec7e8'] * (len(plot_df) - 1) + ['#1f77b4']
        
        fig_bar = px.bar(
            plot_df, 
            x=crop_col, 
            y=water_col,
            labels={water_col: 'Water Required (mm)', crop_col: 'Crop Category'},
            title="How your current recommendation compares against average crop distributions"
        )
        fig_bar.update_traces(marker_color=colors)
        fig_bar.update_layout(height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

except FileNotFoundError:
    st.error("⚠️ System Core Error: ML models missing from environment folder. Ensure your Jupyter execution pipeline has written the necessary `.pkl` files successfully.")
    
