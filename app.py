import streamlit as st
import asyncio
from datetime import datetime, timedelta, timezone
import httpx
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Earthquake Explorer", page_icon="🌍", layout="wide")
st.title("Recent earthquake explorer")
st.caption("Live data from USGS. The human-facing twin of an MCP server tool — see why in the sidebar.")

with st.sidebar:
    st.header("Filters")
    min_magnitude = st.slider(
        "Minimum magnitude",
        2.5, 7.5, 4.5, 0.1,
        help=(
            "Only earthquakes at or above this magnitude are shown. "
            "Magnitude is logarithmic — each whole step up is about 32x more energy released."
        ),
    )
    days = st.slider(
        "Time window (days back)",
        1, 30, 7,
        help="How far back to search, counting backward from right now (UTC). 7 = the last week.",
    )

    with st.expander("What does magnitude mean?"):
        st.markdown(
            "- **2.5–4.4** — Minor, rarely felt\n"
            "- **4.5–5.4** — Light, felt by people, minimal damage\n"
            "- **5.5–6.0** — Moderate, can damage poorly built structures\n"
            "- **6.1–6.9** — Strong, damage in populated areas\n"
            "- **7.0+** — Major, serious damage over large areas"
        )

    st.divider()
    with st.expander("Why does this exist alongside an MCP server?"):
        st.write(
            "This app is for humans — open it, drag sliders, look at a map. "
            "The same data-fetching logic also powers an MCP server tool, which lets AI agents "
            "(Claude Desktop, etc.) pull this same live data autonomously, as one step in reasoning "
            "about something else — no dashboard required. "
            "[See the MCP server on GitHub](https://github.com/KavyaAgarwal2001/geo-agent)."
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
    st.stop()

lats, lons, mags, texts = [], [], [], []
for eq in features:
    lon, lat, _ = eq["geometry"]["coordinates"]
    mag = eq["properties"]["mag"]
    eq_time = datetime.utcfromtimestamp(eq["properties"]["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
    lats.append(lat); lons.append(lon); mags.append(mag)
    texts.append(f"M{mag} — {eq['properties']['place']}<br>{eq_time}")

fig = go.Figure(go.Scattergeo(
    lat=lats, lon=lons, text=texts, hoverinfo="text",
    #marker=dict(size=[max(m,1)*4 for m in mags], color=mags, colorscale="OrRd", colorbar=dict(title="Magnitude"), line=dict(width=0.5, color="black")),
    marker=dict(
    size=[max(m, 1) * 4 for m in mags],
    color=mags,
    colorscale="OrRd",
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
