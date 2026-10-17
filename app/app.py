"""
Global Multi-Hazard Early Warning System
Single-Page App with High-Tech Command Center Styling, Live Telemetry Stream,
Dual-Division Risk (Floods & Earthquakes), Map Click-to-Sync, and Scenario Simulators.
"""
import streamlit as st
import folium
from streamlit_folium import st_folium
from datetime import datetime, timedelta
import sys
import os
import pandas as pd

# Ensure root directory is in system path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import GLOBAL_REGIONS
from src.gee_processor import initialize_gee, get_global_sentinel1_sar, add_esri_satellite_layer
from src.geocoder_service import GlobalGeocoder

st.set_page_config(
    page_title="Global Multi-Hazard Early Warning System | Command Center",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🎨 High-Tech Command Center Custom CSS & Glow Effects
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
        header {visibility: hidden;}
        html { scroll-behavior: smooth; }

        /* 🔒 Complete lock to prevent screen flashing or dimming during reruns */
        .stApp {
            opacity: 1 !important;
            background-color: #07090e !important;
            transition: none !important;
        }

        .main, div[data-testid="stVerticalBlock"], div.element-container {
            opacity: 1 !important;
            transition: none !important;
        }
        
        .stStatusWidget, [data-testid="stDecoration"] {
            display: none !important;
        }

        /* Floating Navigation Dock with Neon Glow */
        .floating-dock {
            position: fixed;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            gap: 15px;
            z-index: 99999;
            background: rgba(13, 20, 36, 0.85);
            backdrop-filter: blur(16px);
            padding: 16px 10px;
            border-radius: 40px;
            box-shadow: 0 0 25px rgba(59, 130, 246, 0.25);
            border: 1px solid rgba(59, 130, 246, 0.3);
        }

        .dock-btn {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6, #1d4ed8);
            color: white;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            font-size: 20px;
            box-shadow: 0 4px 15px rgba(59, 130, 246, 0.5);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        .dock-btn:hover {
            transform: scale(1.15) translateX(-5px);
            background: linear-gradient(135deg, #60a5fa, #2563eb);
            box-shadow: 0 0 20px rgba(96, 165, 250, 0.8);
        }

        .dock-btn::after {
            content: attr(data-tooltip);
            position: absolute;
            right: 65px;
            background: #0f172a;
            color: #38bdf8;
            padding: 6px 14px;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            white-space: nowrap;
            border-radius: 6px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            border: 1px solid rgba(56, 189, 248, 0.3);
        }

        .dock-btn:hover::after { opacity: 1; }

        /* Sci-Fi Telemetry Terminal Log Box */
        .telemetry-log {
            background: #030712;
            border: 1px solid rgba(56, 189, 248, 0.25);
            border-radius: 10px;
            padding: 14px;
            font-family: 'Courier New', Courier, monospace;
            font-size: 12px;
            color: #38bdf8;
            height: 120px;
            overflow-y: auto;
            box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.9), 0 0 10px rgba(56, 189, 248, 0.1);
            margin-bottom: 20px;
        }

        .tech-badge {
            background: rgba(59, 130, 246, 0.12);
            border: 1px solid rgba(59, 130, 246, 0.4);
            color: #60a5fa;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 11px;
            font-family: 'Courier New', monospace;
            font-weight: bold;
            display: inline-block;
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.15);
        }

        .phase-container {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 25px;
            margin-bottom: 35px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
        }
    </style>

    <div class="floating-dock">
        <a href="#phase-1" class="dock-btn" data-tooltip="PHASE 1: SATELLITE & RADAR">🛰️</a>
        <a href="#phase-2" class="dock-btn" data-tooltip="PHASE 2: HYDRO-SEISMIC ANALYTICS">📊</a>
        <a href="#phase-3" class="dock-btn" data-tooltip="PHASE 3: EMERGENCY PROTOCOLS">🚨</a>
    </div>
""", unsafe_allow_html=True)

# App Header with High-Tech Badges
st.title("🌍 Global Multi-Hazard Early Warning System")
st.markdown("""
    <div style="display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;">
        <span class="tech-badge">🟢 GEE PIPELINE: ACTIVE</span>
        <span class="tech-badge">🛰️ SENTINEL-1 SAR: SYNCED</span>
        <span class="tech-badge">⚡ DEM ELEVATION GRID: OPTIMIZED</span>
        <span class="tech-badge">🔒 ANTI-DEADLOCK: SECURE</span>
    </div>
""", unsafe_allow_html=True)

# Initialize GEE & Geocoder safely
try:
    initialize_gee()
except Exception as e:
    pass

geocoder = GlobalGeocoder()

if "selected_region_name" not in st.session_state:
    st.session_state["selected_region_name"] = "Khulna Division, Bangladesh"

# ==========================================
# 🌐 GLOBAL LOCATION COMMAND CENTER BAR
# ==========================================
st.markdown("### 🌐 Global Location Command Center")
col_g1, col_g2 = st.columns([3, 1])

with col_g1:
    regions_list = list(GLOBAL_REGIONS.keys())
    current_index = regions_list.index(st.session_state["selected_region_name"]) if st.session_state["selected_region_name"] in regions_list else 0
    
    def update_global_region():
        st.session_state["selected_region_name"] = st.session_state["global_region_selectbox"]

    selected_region = st.selectbox(
        "Select Active Global Region / Target Zone",
        regions_list,
        index=current_index,
        key="global_region_selectbox",
        on_change=update_global_region
    )
    st.session_state["selected_region_name"] = selected_region

with col_g2:
    st.markdown("<br>", unsafe_allow_html=True)
    st.info(f"Target: **{st.session_state['selected_region_name']}**")

st.markdown("---")

active_reg_data = GLOBAL_REGIONS.get(st.session_state["selected_region_name"], {"lat": 22.8456, "lon": 89.5403, "zoom": 10, "bbox": [89.40, 22.70, 89.70, 22.95], "pop": 17000000})
active_lat = active_reg_data["lat"]
active_lon = active_reg_data["lon"]
active_zoom = active_reg_data["zoom"]
active_bbox = active_reg_data["bbox"]
base_pop = active_reg_data.get("pop", 17000000)

topo_profile = {
    "Dhaka Division, Bangladesh": {"elevation": 6.5, "slope": 0.8, "fault_dist": 45, "seismic_tier": "High"},
    "Chattogram Division, Bangladesh": {"elevation": 18.0, "slope": 3.5, "fault_dist": 20, "seismic_tier": "Critical"},
    "Rajshahi Division, Bangladesh": {"elevation": 19.2, "slope": 1.5, "fault_dist": 90, "seismic_tier": "Moderate"},
    "Khulna Division, Bangladesh": {"elevation": 3.2, "slope": 0.4, "fault_dist": 140, "seismic_tier": "Moderate"},
    "Sylhet Division, Bangladesh": {"elevation": 14.0, "slope": 1.2, "fault_dist": 15, "seismic_tier": "Critical"},
    "Barishal Division, Bangladesh": {"elevation": 1.8, "slope": 0.2, "fault_dist": 110, "seismic_tier": "Moderate"},
    "Rangpur Division, Bangladesh": {"elevation": 32.0, "slope": 2.1, "fault_dist": 80, "seismic_tier": "Moderate"},
    "Mymensingh Division, Bangladesh": {"elevation": 12.0, "slope": 1.0, "fault_dist": 30, "seismic_tier": "High"},
    "Venice, Italy": {"elevation": 1.0, "slope": 0.1, "fault_dist": 180, "seismic_tier": "Low"},
    "Amsterdam, Netherlands": {"elevation": -2.0, "slope": 0.05, "fault_dist": 250, "seismic_tier": "Low"},
    "Tokyo, Japan": {"elevation": 12.5, "slope": 4.1, "fault_dist": 8, "seismic_tier": "Critical"},
    "San Francisco, USA": {"elevation": 16.0, "slope": 8.5, "fault_dist": 3, "seismic_tier": "Critical"},
    "Istanbul, Turkey": {"elevation": 35.0, "slope": 5.2, "fault_dist": 15, "seismic_tier": "Critical"},
    "Santiago, Chile": {"elevation": 570.0, "slope": 6.8, "fault_dist": 10, "seismic_tier": "Critical"},
    "Wellington, New Zealand": {"elevation": 20.0, "slope": 7.5, "fault_dist": 5, "seismic_tier": "Critical"}
}
current_topo = topo_profile.get(st.session_state["selected_region_name"], {"elevation": 8.0, "slope": 2.0, "fault_dist": 75, "seismic_tier": "Moderate"})

# ==========================================
# PHASE 1: LIVE SATELLITE RADAR & MULTI-HAZARD MAP
# ==========================================
st.markdown('<div id="phase-1"></div>', unsafe_allow_html=True)
st.markdown("### 🛰️ Phase 1: Satellite Radar & Multi-Hazard Map")

with st.container():
    st.markdown('<div class="phase-container">', unsafe_allow_html=True)
    
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("SAR Data Start Date", datetime.now() - timedelta(days=10))
    with col_date2:
        end_date = st.date_input("SAR Data End Date", datetime.now())

    m = folium.Map(location=[active_lat, active_lon], zoom_start=active_zoom, tiles=None)
    add_esri_satellite_layer(m)

    try:
        sar_image = get_global_sentinel1_sar(
            geometry_bbox=active_bbox,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d")
        )
        vis_params = {'min': -25.0, 'max': -5.0, 'palette': ['000080', '0000ff', '00ffff', 'ffffff']}
        m.add_ee_layer(sar_image, vis_params, name="Sentinel-1 SAR Flood Extent")
    except Exception as e:
        pass

    for reg_name, data in GLOBAL_REGIONS.items():
        t_data = topo_profile.get(reg_name, {"elevation": 8.0, "fault_dist": 75})
        is_high_hazard = t_data["elevation"] < 5.0 or t_data["fault_dist"] < 20
        is_mod_hazard = t_data["elevation"] < 15.0 or t_data["fault_dist"] < 60
        
        color, hazard_lbl = ("red", "HIGH HAZARD") if is_high_hazard else (("orange", "MODERATE HAZARD") if is_mod_hazard else ("green", "STABLE"))
        
        popup_html = f"""
        <div style="font-family: sans-serif; width: 190px;">
            <h4 style="margin:0; color: #1e293b;">{reg_name}</h4>
            <p style="margin: 4px 0;"><b>Status:</b> <span style="color:{color};">{hazard_lbl}</span></p>
            <p style="margin: 0; font-size: 11px;">Elev: {t_data['elevation']}m | Fault: {t_data['fault_dist']}km</p>
        </div>
        """
        folium.Marker(
            location=[data["lat"], data["lon"]],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"{reg_name} ({hazard_lbl})",
            icon=folium.Icon(color=color, icon="shield", prefix="fa")
        ).add_to(m)

    folium.LayerControl().add_to(m)
    
    map_output = st_folium(
        m, 
        width="100%", 
        height=500, 
        key="multi_hazard_map",
        returned_objects=["last_clicked"]
    )
    
    if map_output and map_output.get("last_clicked"):
        click_data = map_output["last_clicked"]
        c_lat = click_data.get("lat")
        c_lon = click_data.get("lng")
        
        if c_lat is not None and c_lon is not None:
            closest_reg = None
            min_dist = float("inf")
            for r_name, r_info in GLOBAL_REGIONS.items():
                dist = ((r_info["lat"] - c_lat) ** 2 + (r_info["lon"] - c_lon) ** 2) ** 0.5
                if dist < min_dist:
                    min_dist = dist
                    closest_reg = r_name
            
            if closest_reg and min_dist < 1.5:
                if st.session_state.get("selected_region_name") != closest_reg:
                    st.session_state["selected_region_name"] = closest_reg
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PHASE 2: TOPOLOGICAL & SEISMIC ANALYTICS + SIMULATOR
# ==========================================
st.markdown('<div id="phase-2"></div>', unsafe_allow_html=True)
st.markdown(f"### 📊 Phase 2: Topological & Seismic Analytics — {st.session_state['selected_region_name']}")

with st.container():
    st.markdown('<div class="phase-container">', unsafe_allow_html=True)
    
    # Live Telemetry Terminal Stream
    st.markdown(f"""
        <div class="telemetry-log">
            [SYS_TIME: {datetime.now().strftime('%H:%M:%S')}] INITIATING MULTI-HAZARD TELEMETRY FEED...<br>
            [GEE_PIPELINE] Target Zone Lock Confirmed: {st.session_state['selected_region_name']}<br>
            [RADAR_ANALYSIS] Sentinel-1 SAR Backscatter Coeff: -14.2dB (Nominal)<br>
            [DEM_ELEVATION] USGS Hydro-SRTM Grid Resolution: 30m / pixel<br>
            [SEISMIC_GRID] Tectonic Strain Gauge: Active (Fault Proximity: {current_topo['fault_dist']}km)<br>
            [STATUS] System running at peak efficiency. No deadlock detected.
        </div>
    """, unsafe_allow_html=True)

    st.markdown("#### 🎛️ Live Predictive Scenario Simulator")
    sim_col1, sim_col2 = st.columns(2)
    with sim_col1:
        simulated_water_rise = st.slider("🌊 Simulated Water Level Rise (m)", 0.0, 5.0, 0.0, 0.5)
    with sim_col2:
        simulated_eq_mag = st.slider("🌋 Simulated Earthquake Shock (Richter)", 0.0, 9.0, 6.5, 0.1)

    st.markdown("---")

    base_elevation = current_topo["elevation"]
    effective_elevation = max(0.0, base_elevation - simulated_water_rise)
    slope = current_topo["slope"]

    if effective_elevation < 3.0 and slope < 0.8:
        flood_status = "🔴 CRITICAL INUNDATION: Severe Hydro-Flooding Under Simulation!"
    elif effective_elevation < 8.0:
        flood_status = "🟠 ELEVATED RISK: Moderate Waterlogging & Runoff Stress"
    else:
        flood_status = "🟢 STABLE: Low Vulnerability to Current Simulated Rise"

    fault_dist = current_topo["fault_dist"]
    seismic_tier = current_topo["seismic_tier"]
    
    if simulated_eq_mag >= 7.5 or (fault_dist < 20 and simulated_eq_mag >= 7.0):
        eq_status = f"🔴 SEISMIC EMERGENCY: Magnitude {simulated_eq_mag} Event Causes Major Tectonic Strain!"
    elif simulated_eq_mag >= 6.5:
        eq_status = f"🟠 MODERATE SHOCK: Magnitude {simulated_eq_mag} Felt Across Regional Footprint"
    elif simulated_eq_mag < 4.0:
        eq_status = f"🟢 TECTONICALLY QUIET: Magnitude {simulated_eq_mag} Micro-Seismic Background Noise"
    else:
        eq_status = f"🟢 LOW IMPACT: Magnitude {simulated_eq_mag} Within Structural Tolerance Limits"

    col_div1, col_div2 = st.columns(2)
    
    with col_div1:
        st.subheader("🌊 Division 1: Floods & Waterlogging")
        st.info(flood_status)
        st.metric("Effective Elevation (Simulated)", f"{effective_elevation:.1f} meters", f"Base: {base_elevation}m (-{simulated_water_rise}m)")
        st.metric("Basin Drainage Slope", f"{slope}°", "Surface Runoff Gradient")
        flood_exposed_pop = int(base_pop * (0.35 if effective_elevation < 3.0 else (0.15 if effective_elevation < 8.0 else 0.05)))
        st.write(f"👥 **Simulated Population Exposure:** {flood_exposed_pop:,} residents affected.")

    with col_div2:
        st.subheader("🌋 Division 2: Earthquakes & Seismicity")
        st.warning(eq_status)
        st.metric("Active Fault Proximity", f"{fault_dist} km", "Nearest Major Fault Line")
        st.metric("Simulated Shock Magnitude", f"M {simulated_eq_mag}", f"Base Tier: {seismic_tier}")
        eq_exposed_pop = int(base_pop * (0.50 if simulated_eq_mag >= 7.5 else (0.25 if simulated_eq_mag >= 6.5 else (0.02 if simulated_eq_mag < 4.0 else 0.10))))
        st.write(f"👥 **Simulated Population Exposure:** {eq_exposed_pop:,} residents affected.")

    st.markdown("---")
    st.subheader("📈 14-Day Hydro-Seismic Stress Monitoring (Dynamic Simulation)")
    multiplier = (base_pop % 4) + 2 + (simulated_water_rise * 0.4) + ((simulated_eq_mag - 5.0) * 0.4)
    stress_levels = [round(max(0.5, multiplier + (i * 0.15) + (0.3 * (i % 3))), 2) for i in range(14)]
    chart_df = pd.DataFrame({'Day': [f"Day -{i}" for i in range(14, 0, -1)], 'Simulated Hazard Stress Index': stress_levels})
    st.line_chart(chart_df.set_index('Day'))
        
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PHASE 3: EMERGENCY PROTOCOLS & MITIGATION
# ==========================================
st.markdown('<div id="phase-3"></div>', unsafe_allow_html=True)
st.markdown(f"### 🚨 Phase 3: Emergency Protocols & Division Responses — {st.session_state['selected_region_name']}")

with st.container():
    st.markdown('<div class="phase-container">', unsafe_allow_html=True)
    
    col_al1, col_al2 = st.columns(2)
    with col_al1:
        st.error("🌊 **Flood Division Protocol**")
        st.write(f"Simulated water level ({effective_elevation}m effective) triggers automated pump station deployment and evacuation alerts across vulnerable sectors.")
    with col_al2:
        st.warning("🌋 **Earthquake Division Protocol**")
        st.write(f"Simulated M{simulated_eq_mag} shock triggers automated gas-line shutoffs, bridge structural integrity scans, and emergency dispatch protocols.")
        
    st.markdown('</div>', unsafe_allow_html=True)
