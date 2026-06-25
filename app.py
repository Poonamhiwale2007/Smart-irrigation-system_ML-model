import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- Page Setup ---
st.set_page_config(page_title="Smart Agros IoT Dashboard", page_icon="🌾", layout="wide")

st.title("🌾 Smart Agros: Advanced Irrigation Insights & Analytics Dashboard")
st.write("An enterprise-grade IoT decision support tool mapping real-time agronomic data to yield impacts.")
st.markdown("---")

# --- Initialize Persistent Session State for History & Trends ---
if "history" not in st.session_state:
    now = datetime.now()
    st.session_state.history = pd.DataFrame({
        "Timestamp": [(now - timedelta(hours=i)).strftime("%H:%M") for i in range(4, -1, -1)],
        "Soil Moisture (%)": [24.0, 28.5, 45.0, 62.0, 58.0],
        "Temperature (°C)": [31.2, 32.5, 29.0, 27.5, 28.3],
        "Humidity (%)": [35.0, 33.0, 48.0, 55.0, 52.0],
        "Action Taken": ["Irrigated Now", "Irrigated Now", "Monitoring", "No Action", "No Action"]
    })

# --- Sidebar Inputs (Features 6, 9, Soil, & Weather) ---
st.sidebar.header("🚜 Farm Configuration")
crop_type = st.sidebar.selectbox("🌾 Crop Type", ["Rice", "Wheat", "Tomato", "Cotton", "Sugarcane"])
soil_type = st.sidebar.selectbox("⏳ Soil Type", ["Sandy", "Loamy", "Clay", "Silty"])
farm_area = st.sidebar.number_input("📐 Farm Area (sq.m)", min_value=10, max_value=10000, value=500, step=50)

st.sidebar.header("🌦️ Environmental Sensors")
weather_condition = st.sidebar.selectbox("Current Forecast", ["Sunny", "Overcast", "Rainy", "Windy"])
soil_moisture = st.sidebar.slider("🌱 Soil Moisture (%)", 0.0, 100.0, 34.0, 0.1)
temperature = st.sidebar.slider("🌡️ Temperature (°C)", -5.0, 50.0, 28.3, 0.1)
humidity = st.sidebar.slider("💧 Humidity (%)", 0.0, 100.0, 42.0, 0.1)

# --- Business Logic & Calculation Helpers ---

# Base Water Factor based on crop types (Liters per sq.m under deficit)
crop_water_factors = {"Rice": 1.2, "Sugarcane": 1.0, "Tomato": 0.8, "Cotton": 0.7, "Wheat": 0.5}
base_factor = crop_water_factors[crop_type]

# Adjustments for soil type
soil_adjustments = {"Sandy": 1.2, "Loamy": 1.0, "Silty": 0.9, "Clay": 0.7}
soil_factor = soil_adjustments[soil_type]

# Calculate Water Requirement Meter (Feature 1 & 9)
moisture_deficit = max(0, 70 - soil_moisture)  # Target is optimal 70%
water_liters_per_sqm = (moisture_deficit / 100) * base_factor * soil_factor
if weather_condition == "Rainy":
    water_liters_per_sqm *= 0.1  # Reduce heavily if rain is expected
elif weather_condition == "Sunny" and temperature > 30:
    water_liters_per_sqm *= 1.2  # Increase due to evapotranspiration

total_water_needed = round(water_liters_per_sqm * farm_area, 1)
max_possible_water = (70 / 100) * 1.2 * 1.2 * farm_area
water_percentage = min(100, int((total_water_needed / max_possible_water) * 100)) if max_possible_water > 0 else 0

# Calculate Cost (Feature 7)
water_cost_per_liter = 0.125  # ₹0.125 per liter -> ~₹15 for 120L
estimated_cost = round(total_water_needed * water_cost_per_liter, 2)

# Calculate Crop Health Score (Feature 11)
m_score = 100 - abs(60 - soil_moisture) * 1.5
t_score = 100 - abs(22 - temperature) * 2.0
h_score = 100 - abs(55 - humidity) * 1.0
crop_health_score = max(0, min(100, int((m_score + t_score + h_score) / 3)))

if crop_health_score >= 90:
    health_status, health_color = "Excellent", "green"
elif crop_health_score >= 70:
    health_status, health_color = "Good", "blue"
elif crop_health_score >= 50:
    health_status, health_color = "Fair", "orange"
else:
    health_status, health_color = "Poor", "red"

# Predicted Yield Impact (Feature 12)
current_yield = max(40, int(crop_health_score * 1.0))
if soil_moisture < 30:
    delayed_yield = max(30, current_yield - 22)
elif soil_moisture > 90:
    delayed_yield = max(30, current_yield - 15)
else:
    delayed_yield = current_yield

# Helper function to create gauges (Feature 8)
def create_gauge(value, title, unit, max_val, color):
    return go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': color},
            'steps': [{'range': [0, max_val], 'color': "#f4f4f4"}]
        }
    )).update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))


# --- DASHBOARD LAYOUT ---

# ROW 1: Gauge Charts & Status Indicators (Features 5 & 8)
st.subheader("📊 Real-Time IoT Telemetry & Core Status")
g1, g2, g3 = st.columns(3)
with g1:
    st.plotly_chart(create_gauge(soil_moisture, "🌱 Soil Moisture", "%", 100, "teal"), use_container_width=True)
    if soil_moisture < 30:
        st.error("🔴 Critical - Irrigate Now")
    elif soil_moisture < 50:
        st.warning("🟠 Moderate Warning")
    elif soil_moisture <= 70:
        st.success("🟢 Optimal Range")
    elif soil_moisture <= 90:
        st.info("🔵 Wet Conditions")
    else:
        st.error("❌ Waterlogged - Drainage Needed")

with g2:
    st.plotly_chart(create_gauge(temperature, "temperature", "°C", 50, "darkorange"), use_container_width=True)
    if temperature > 35: st.error("🔴 High Heat Stress")
    elif temperature > 30: st.warning("🟠 Warm Conditions")
    elif temperature >= 15: st.success("🟢 Optimal Growth Conditions")
    else: st.info("🔵 Cool Conditions")

with g3:
    st.plotly_chart(create_gauge(humidity, "💧 Relative Humidity", "%", 100, "royalblue"), use_container_width=True)
    if humidity < 40: st.warning("🟠 Dry Air (High Evaporation)")
    elif humidity <= 70: st.success("🟢 Normal Humidity Range")
    else: st.info("🔵 Humid Conditions")

st.markdown("---")

# ROW 2: AI Recommendations & Water Analytics
col_left, col_right = st.columns([1, 1])

with col_left:
    # AI Recommendation Card (Feature 3)
    st.subheader("🤖  Smart Recommendation Engine")
    with st.container(border=True):
        st.markdown(f"### **Action Analysis Matrix**")
        
        # Micro insights mapping
        m_msg = f"❌ Soil moisture is critically low ({soil_moisture}%)" if soil_moisture < 30 else f"✅ Moisture status is functional ({soil_moisture}%)"
        t_msg = f"🌡️ Thermal load stress active ({temperature}°C)" if temperature > 35 else f"🌱 Thermal envelope is optimal ({temperature}°C)"
        h_msg = f"💧 Ambient humidity is dry ({humidity}%)" if humidity < 40 else f"🌤️ Humidity vapor density is balanced ({humidity}%)"
        
        st.write(m_msg)
        st.write(t_msg)
        st.write(h_msg)
        
        # Execution timing recommendation
        if soil_moisture < 30:
            rec_action = "Execute system ignition immediately (Within 1 Hour)."
            rec_urgency = "High"
        elif soil_moisture < 50:
            rec_action = "Schedule irrigation loop during next standard deployment cycle."
            rec_urgency = "Medium"
        else:
            rec_action = "Hold cycles. Maintain normal passive logging protocols."
            rec_urgency = "None"
            
        st.markdown(f"""
        **Recommended Action:** `{rec_action}`  
        
        **Estimated System Urgency:** **{rec_urgency}**
        """)

with col_right:
    # Water Requirement & Financial Cost Estimation (Features 1, 7, & 9)
    st.subheader("💧 Volumetric Water Meter & Cost Metrics")
    with st.container(border=True):
        st.markdown(f"#### Target Volume for **{farm_area} sq.m** of **{crop_type}** ({soil_type} Soil)")
        st.metric(label="Calculated Hydration Needed", value=f"{total_water_needed} Litres")
        
        # Text Progress Bar Visualization
        filled_blocks = int(water_percentage / 10)
        bar_str = "█" * filled_blocks + "░" * (10 - filled_blocks)
        st.markdown(f"`{bar_str}` **{water_percentage}% Requirement Capacity**")
        
        st.markdown("---")
        st.metric(label="Estimated Resource Overhead Cost", value=f"₹{estimated_cost}", delta="Based on ₹0.125/L rate")

st.markdown("---")

# ROW 3: Predictive Analytics & Advanced Decision Metrics
col_an1, col_an2, col_an3 = st.columns(3)

with col_an1:
    # Crop Health Score (Feature 11)
    st.subheader("🏆 Crop Vitality Index")
    with st.container(border=True):
        st.metric(label="Health Score Rating", value=f"{crop_health_score} / 100", delta=health_status, delta_color="normal" if health_color != "red" else "inverse")
        st.caption("Aggregated metric analyzing immediate soil moisture boundary bounds cross-referenced with air temperature indexes.")

with col_an2:
    # Predicted Yield Impact (Feature 12)
    st.subheader("🎯 Agronomic Yield Forecasting")
    with st.container(border=True):
        st.markdown(f"**Current Context Yield Potential:** `{current_yield}%`")
        st.markdown(f"**Potential If Irrigation Delayed:** `{delayed_yield}%`")
        
        loss = current_yield - delayed_yield
        if loss > 0:
            st.error(f"⚠️ Delays hazard a prospective {loss}% reduction in crop output potential.")
        else:
            st.success("✅ Current balance path preserves maximal target harvest index.")

with col_an3:
    # Weather Impact Section (Feature 4)
    st.subheader("🌦️ Environmental Vector Rules")
    with st.container(border=True):
        st.markdown(f"**Active Condition Context:** `{weather_condition}`")
        
        # Weather rules layout table
        weather_rules_df = pd.DataFrame({
            "Condition": ["Hot & Dry", "Cool & Humid", "Rain Expected", "Windy & Sunny"],
            "System Action Adjustment": ["Accelerated Volumetric Irrigation", "Throttle / Decrease Delivery", "Suppression & Schedule Postponement", "Increase Rate to offset Evaporation"]
        })
        st.dataframe(weather_rules_df, hide_index=True, use_container_width=True)

st.markdown("---")

# ROW 4: Real-Time Time-Series Graphs & History logs (Features 2 & 10)
st.subheader("📈 Historical Data Sequences & Telemetry Trends")
col_graph, col_table = st.columns([1, 1])

# Append the current dynamic slider adjustments into a local visualization frame
historical_df = st.session_state.history.copy()

with col_graph:
    st.markdown("#### Real-Time Sensor Trends vs Time Logs")
    # Multi-tab view for cleaner real-time trend organization
    tab1, tab2, tab3 = st.tabs(["Moisture Track", "Thermal Track", "Humidity Track"])
    with tab1:
        st.line_chart(historical_df.set_index("Timestamp")["Soil Moisture (%)"])
    with tab2:
        st.line_chart(historical_df.set_index("Timestamp")["Temperature (°C)"])
    with tab3:
        st.line_chart(historical_df.set_index("Timestamp")["Humidity (%)"])

with col_table:
    st.markdown("#### Logging Event Ledger (Recent Audit Logs)")
    st.dataframe(historical_df, use_container_width=True, hide_index=True)
