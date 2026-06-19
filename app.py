import streamlit as st
import asyncio
from datetime import datetime, timedelta, timezone
import httpx
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Geo Agent Explorer", page_icon="🌍", layout="wide")
st.title("Geo agent explorer")
st.caption("Live earth-science data. The human-facing twin of an MCP server tool, see why in the sidebar.")

with st.sidebar:
    st.header("About")
    with st.expander("Why does this exist alongside an MCP server?"):
        st.write(
            "This app is for humans: open it, click around, look at charts. "
            "The same data-fetching logic also powers an MCP server tool, which lets AI agents "
            "(Claude Desktop, etc.) pull this same live data autonomously, as one step in reasoning "
            "about something else, no dashboard required. "
            "[See the MCP server on GitHub](https://github.com/KavyaAgarwal2001/geo-agent)."
        )

tab1, tab2 = st.tabs(["🌍 Earthquakes", "🌡️ Climate"])

# ---------------- Earthquakes tab ----------------
with tab1:
    col1, col2 = st.columns(2)
    with col1:
        min_magnitude = st.slider(
            "Minimum magnitude", 2.5, 7.5, 4.5, 0.1,
            help="Only earthquakes at or above this magnitude are shown. Magnitude is logarithmic: each whole step up is about 32x more energy released.",
            key="eq_mag",
        )
    with col2:
        days = st.slider(
            "Time window (days back)", 1, 30, 7,
            help="How far back to search, counting backward from right now (UTC). 7 = the last week.",
            key="eq_days",
        )

    with st.expander("What does magnitude mean?"):
        st.markdown(
            "- **2.5–4.4** — Minor, rarely felt\n"
            "- **4.5–5.4** — Light, felt by people, minimal damage\n"
            "- **5.5–6.0** — Moderate, can damage poorly built structures\n"
            "- **6.1–6.9** — Strong, damage in populated areas\n"
            "- **7.0+** — Major, serious damage over large areas"
        )

    @st.cache_data(ttl=300)
    def fetch_earthquakes(min_magnitude, days):
        async def _fetch():
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            start = datetime.now(timezone.utc) - timedelta(days=days)
            params = {"format": "geojson", "minmagnitude": min_magnitude, "starttime": start.strftime("%Y-%m-%d"), "orderby": "magnitude", "limit": 200}
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                return resp.json(), start
        return asyncio.run(_fetch())

    with st.spinner("Fetching live earthquake data from USGS..."):
        try:
            data, start_date = fetch_earthquakes(min_magnitude, days)
        except httpx.HTTPError as e:
            st.error(f"Couldn't reach USGS right now: {e}")
            st.stop()

    features = data["features"]
    st.caption(
        f"**{len(features)} events** · M{min_magnitude}+ · since {start_date.strftime('%b %d, %Y')} · "
        f"Source: [USGS](https://earthquake.usgs.gov) (U.S. Geological Survey) · Live data"
    )

    if not features:
        st.info("No earthquakes matched these filters. Try lowering the minimum magnitude or extending the day range.")
    else:
        lats, lons, mags, texts = [], [], [], []
        for eq in features:
            lon, lat, _ = eq["geometry"]["coordinates"]
            mag = eq["properties"]["mag"]
            eq_time = datetime.utcfromtimestamp(eq["properties"]["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
            lats.append(lat); lons.append(lon); mags.append(mag)
            texts.append(f"M{mag} — {eq['properties']['place']}<br>{eq_time}")

        fig = go.Figure(go.Scattergeo(
            lat=lats, lon=lons, text=texts, hoverinfo="text",
            marker=dict(
                size=[max(m, 1) * 4 for m in mags],
                color=mags, colorscale="OrRd",
                colorbar=dict(title="Magnitude", thickness=15, len=0.7, y=0.5, yanchor="middle"),
                line=dict(width=0.5, color="black"),
            ),
            mode="markers",
        ))
        fig.update_geos(showcountries=True, showcoastlines=True, showland=True, landcolor="rgb(243,243,243)")
        fig.update_layout(height=600, margin=dict(t=10))
        st.plotly_chart(fig, use_container_width=True)

        with st.expander("View raw data"):
            df = pd.DataFrame({
                "Magnitude": mags,
                "Place": [eq["properties"]["place"] for eq in features],
                "Time (UTC)": [datetime.utcfromtimestamp(eq["properties"]["time"]/1000).strftime("%Y-%m-%d %H:%M") for eq in features],
                "Latitude": lats,
                "Longitude": lons,
            }).sort_values("Magnitude", ascending=False)
            st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------- Climate tab ----------------
with tab2:
    PRESETS = {
        "New Haven, CT": (41.31, -72.92),
        "Agra, India": (27.18, 78.02),
        "Tokyo, Japan": (35.68, 139.65),
        "Jakarta, Indonesia": (-6.21, 106.85),
        "Custom": None,
    }
    location_name = st.selectbox("Location", list(PRESETS.keys()), key="climate_loc")

    if location_name == "Custom":
        c1, c2 = st.columns(2)
        with c1:
            latitude = st.number_input("Latitude", -90.0, 90.0, 41.31, 0.01, key="climate_lat")
        with c2:
            longitude = st.number_input("Longitude", -180.0, 180.0, -72.92, 0.01, key="climate_lon")
    else:
        latitude, longitude = PRESETS[location_name]
        st.caption(f"{latitude}°, {longitude}°")

    climate_days = st.slider(
        "Days of history", 3, 21, 10, key="climate_days",
        help="NASA POWER has a short processing lag, so the most recent day or two may not have solar data yet.",
    )

    @st.cache_data(ttl=3600)
    def fetch_climate(lat, lon, days):
        end = datetime.utcnow() - timedelta(days=3)
        start = end - timedelta(days=days)
        url = "https://power.larc.nasa.gov/api/temporal/daily/point"
        params = {
            "parameters": "T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
            "community": "AG",
            "longitude": lon,
            "latitude": lat,
            "start": start.strftime("%Y%m%d"),
            "end": end.strftime("%Y%m%d"),
            "format": "JSON",
        }
        with httpx.Client() as client:
            resp = client.get(url, params=params, timeout=15.0)
            resp.raise_for_status()
            return resp.json()

    with st.spinner("Fetching live climate data from NASA POWER..."):
        try:
            climate_data = fetch_climate(latitude, longitude, climate_days)
        except httpx.HTTPError as e:
            st.error(f"Couldn't reach NASA POWER right now: {e}")
            st.stop()

    param_data = climate_data["properties"]["parameter"]
    dates = sorted(param_data["T2M"].keys())
    date_labels = [datetime.strptime(d, "%Y%m%d").strftime("%b %d") for d in dates]
    temps = [param_data["T2M"][d] for d in dates]
    precip = [param_data["PRECTOTCORR"][d] for d in dates]
    solar = [None if param_data["ALLSKY_SFC_SW_DWN"][d] == -999.0 else param_data["ALLSKY_SFC_SW_DWN"][d] for d in dates]

    loc_label = location_name if location_name != "Custom" else f"{latitude}°, {longitude}°"
    st.caption(f"**{loc_label}** · {date_labels[0]}–{date_labels[-1]} · Source: [NASA POWER](https://power.larc.nasa.gov) · Live data")

    climate_fig = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
        subplot_titles=("Avg temperature (°C)", "Precipitation (mm/day)", "Solar radiation (kWh/m²/day)"),
    )
    climate_fig.add_trace(go.Scatter(x=date_labels, y=temps, mode="lines+markers", line=dict(color="#d9534f")), row=1, col=1)
    climate_fig.add_trace(go.Bar(x=date_labels, y=precip, marker_color="#5b8fd9"), row=2, col=1)
    climate_fig.add_trace(go.Bar(x=date_labels, y=solar, marker_color="#e8a23d"), row=3, col=1)
    climate_fig.update_layout(height=650, showlegend=False, margin=dict(t=40))
    st.plotly_chart(climate_fig, use_container_width=True)

    if any(s is None for s in solar):
        st.caption("Note: the most recent day(s) show no solar bar, NASA POWER hasn't finished processing that satellite data yet.")

    map_fig = go.Figure(go.Scattergeo(
        lat=[latitude], lon=[longitude], mode="markers",
        marker=dict(size=14, color="#e8a23d", line=dict(width=1, color="black")),
        text=[loc_label], hoverinfo="text",
    ))
    map_fig.update_geos(
        showcountries=True, showcoastlines=True, showland=True, landcolor="rgb(243,243,243)",
        projection_scale=4, center=dict(lat=latitude, lon=longitude),
    )
    map_fig.update_layout(height=300, margin=dict(t=10, b=0))
    st.plotly_chart(map_fig, use_container_width=True)

    with st.expander("View raw data"):
        df = pd.DataFrame({
            "Date": date_labels,
            "Temp (°C)": temps,
            "Precip (mm/day)": precip,
            "Solar (kWh/m²/day)": solar,
        })
        st.dataframe(df, use_container_width=True, hide_index=True)
