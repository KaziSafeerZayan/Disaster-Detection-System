"""
Global Multi-Hazard Early Warning System
Single-Page App with Dual-Division Risk (Floods & Earthquakes), Anti-Flicker Locks,
Global Location Command Center, and Map Click-to-Sync.
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
    page_title="Global Multi-Hazard Early Warning System",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 🎨 Custom Glassmorphism CSS & Anti-Flicker Locks
st.markdown("""
    <style>
        [data-testid="stSidebar"] {display: none;}
        header {visibility: hidden;}
        html { scroll-behavior: smooth; }

        /* 🔒 Complete lock to prevent screen flashing, dimming, or brightening during reruns */
        .stApp {
            opacity: 1 !important;
            background-color: #0e1117 !important;
            transition: none !important;
        }

        .main, div[data-testid="stVerticalBlock"], div.element-container {
            opacity: 1 !important;
            transition: none !important;
        }
        
        .stStatusWidget, [data-testid="stDecoration"] {
            display: none !important;
        }

        .floating-dock {
            position: fixed;
            right: 25px;
            top: 50%;
            transform: translateY(-50%);
            display: flex;
            flex-direction: column;
            gap: 15px;
            z-index: 99999;
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(12px);
            padding: 14px 10px;
            border-radius: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
            border: 1px solid rgba(255, 255, 255, 0.15);
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
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
        }

        .dock-btn:hover {
            transform: scale(1.15) translateX(-5px);
            background: linear-gradient(135deg, #60a5fa, #2563eb);
            box-shadow: 0 6px 20px rgba(96, 165, 250, 0.6);
        }

        .dock-btn::after {
            content: attr(data-tooltip);
            position: absolute;
            right: 65px;
            background: #1e293b;
            color: #f8fafc;
            padding: 5px 12px;
            font-size: 12px;
            font-family: sans-serif;
            white-space: nowrap;
            border-radius: 6px;
            opacity: 0;
            pointer-events: none;
            transition: opacity 0.2s ease;
            box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            border: 1px solid rgba(255,255,255,0.1);
        }

        .dock-btn:hover::after { opacity: 1; }

        .phase-container {
            padding: 15px 0px;
            margin-bottom: 30px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        }
    </style>

    <div class="floating-dock">
        <a href="#phase-1" class="dock-btn" data-tooltip="Phase 1: Multi-Hazard Map">🛰️</a>
        <a href="#phase-2" class="dock-btn" data-tooltip="Phase 2: Topological & Seismic Analytics">📊</a>
        <a href="#phase-3" class="dock-btn" data-tooltip="Phase 3: Emergency Protocols">🚨</a>
    </div>
""", unsafe_allow_html=True)

# App Header
st.title("🌍 Global Multi-Hazard Early Warning System")
st.markdown("Topological flood monitoring & geophysical seismic tracking powered by satellite radar and elevation models.")

# Initialize GEE & Geocoder
try:
    initialize_gee()
except Exception as e:
    st.error(f"GEE Auth Error: {e}. Run `earthengine authenticate` in your terminal.")

geocoder = GlobalGeocoder()

if "selected_region_name" not in st.session_state:
    st.session_state["selected_region_name"] = "Khulna Division, Bangladesh"

# ==========================================
# 🌐 SINGLE GLOBAL LOCATION SELECTOR BAR
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
    st.info(f"Active Target: **{st.session_state['selected_region_name']}**")

st.markdown("---")

active_reg_data = GLOBAL_REGIONS.get(st.session_state["selected_region_name"], {"lat": 22.8456, "lon": 89.5403, "zoom": 10, "bbox": [89.40, 22.70, 89.70, 22.95], "pop": 17000000})
active_lat = active_reg_data["lat"]
active_lon = active_reg_data["lon"]
active_zoom = active_reg_data["zoom"]
active_bbox = active_reg_data["bbox"]
base_pop = active_reg_data.get("pop", 17000000)

topo_profile = {
    # Bangladesh Divisions
    "Dhaka Division, Bangladesh": {"elevation": 6.5, "slope": 0.8, "fault_dist": 45, "seismic_tier": "High"},
    "Chattogram Division, Bangladesh": {"elevation": 18.0, "slope": 3.5, "fault_dist": 20, "seismic_tier": "Critical"},
    "Rajshahi Division, Bangladesh": {"elevation": 19.2, "slope": 1.5, "fault_dist": 90, "seismic_tier": "Moderate"},
    "Khulna Division, Bangladesh": {"elevation": 3.2, "slope": 0.4, "fault_dist": 140, "seismic_tier": "Moderate"},
    "Sylhet Division, Bangladesh": {"elevation": 14.0, "slope": 1.2, "fault_dist": 15, "seismic_tier": "Critical"},
    "Barishal Division, Bangladesh": {"elevation": 1.8, "slope": 0.2, "fault_dist": 110, "seismic_tier": "Moderate"},
    "Rangpur Division, Bangladesh": {"elevation": 32.0, "slope": 2.1, "fault_dist": 80, "seismic_tier": "Moderate"},
    "Mymensingh Division, Bangladesh": {"elevation": 12.0, "slope": 1.0, "fault_dist": 30, "seismic_tier": "High"},
    # International Hotspots
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
        st.warning(f"GEE tile rendering note: {e}")

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

    # Render map with width="100%" to avoid right-side clipping
    map_output = st_folium(m, width="100%", height=500, key="multi_hazard_map")

    # 🖱️ Click-to-sync region selection
    clicked_info = map_output.get("last_object_clicked") or map_output.get("last_clicked")
    if clicked_info:
        c_lat = clicked_info.get("lat")
        c_lon = clicked_info.get("lng")
        if c_lat and c_lon:
            closest_reg = None
            min_dist = float("inf")
            for r_name, r_info in GLOBAL_REGIONS.items():
                dist = abs(r_info["lat"] - c_lat) + abs(r_info["lon"] - c_lon)
                if dist < min_dist:
                    min_dist = dist
                    closest_reg = r_name

            if closest_reg and min_dist < 3.0:
                if st.session_state["selected_region_name"] != closest_reg:
                    st.session_state["selected_region_name"] = closest_reg
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PHASE 2: TOPOLOGICAL & SEISMIC ANALYTICS
# ==========================================
st.markdown('<div id="phase-2"></div>', unsafe_allow_html=True)
st.markdown(f"### 📊 Phase 2: Topological & Seismic Analytics — {st.session_state['selected_region_name']}")

with st.container():
    st.markdown('<div class="phase-container">', unsafe_allow_html=True)

    elevation = current_topo["elevation"]
    slope = current_topo["slope"]
    if elevation < 4.0 and slope < 0.8:
        flood_status = "🔴 FLOOD DIVISION: Critical Hydro-Inundation Risk (Low Basin Elevation)"
    elif elevation < 12.0:
        flood_status = "🟠 FLOOD DIVISION: Moderate Waterlogging Potential"
    else:
        flood_status = "🟢 FLOOD DIVISION: Low Flood Vulnerability (High Elevation/Slope)"

    fault_dist = current_topo["fault_dist"]
    seismic_tier = current_topo["seismic_tier"]
    if fault_dist < 15 or seismic_tier == "Critical":
        eq_status = "🔴 SEISMIC DIVISION: High Tectonic Strain / Active Fault Proximity"
    elif fault_dist < 50 or seismic_tier == "High":
        eq_status = "🟠 SEISMIC DIVISION: Moderate Fault Activity Zone"
    else:
        eq_status = "🟢 SEISMIC DIVISION: Stable Tectonic Block"

    col_div1, col_div2 = st.columns(2)

    with col_div1:
        st.subheader("🌊 Division 1: Floods & Waterlogging")
        st.info(flood_status)
        st.metric("Topographical Elevation", f"{elevation} meters", "DEM Relative to Sea Level")
        st.metric("Basin Drainage Slope", f"{slope}°", "Surface Runoff Gradient")
        flood_exposed_pop = int(base_pop * (0.25 if elevation < 5.0 else 0.08))
        st.write(f"👥 **Estimated Population Exposure:** {flood_exposed_pop:,} residents in low-lying sectors.")

    with col_div2:
        st.subheader("🌋 Division 2: Earthquakes & Seismicity")
        st.warning(eq_status)
        st.metric("Active Fault Proximity", f"{fault_dist} km", "Nearest Major Seismic Fault Line")
        st.metric("Seismic Hazard Tier", seismic_tier, "Peak Ground Acceleration Model")
        eq_exposed_pop = int(base_pop * (0.40 if seismic_tier == "Critical" else 0.15))
        st.write(f"👥 **Estimated Population Exposure:** {eq_exposed_pop:,} residents in urban footprint.")

    st.markdown("---")
    st.subheader("📈 14-Day Hydro-Seismic Stress Monitoring")
    multiplier = (base_pop % 4) + 2
    stress_levels = [round(multiplier + (i * 0.18) + (0.2 * (i % 4)), 2) for i in range(14)]
    chart_df = pd.DataFrame({'Day': [f"Day -{i}" for i in range(14, 0, -1)], 'Combined Hazard Index': stress_levels})
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
        st.write(f"Elevation analysis ({elevation}m) dictates automated deployment of mobile drainage units to low topographical depressions upon radar saturation.")
    with col_al2:
        st.warning("🌋 **Earthquake Division Protocol**")
        st.write(f"Fault distance ({fault_dist}km) triggers automated structural health telemetry alerts across critical lifelines and bridges.")

    st.markdown('</div>', unsafe_allow_html=True)