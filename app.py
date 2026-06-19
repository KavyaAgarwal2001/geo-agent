import streamlit as st
import asyncio
from datetime import datetime, timedelta, timezone
import httpx
import plotly.graph_objects as go

st.set_page_config(page_title="Earthquake Explorer", layout="wide")
st.title("Recent earthquake explorer")

min_magnitude = st.slider("Minimum magnitude", 2.5, 7.5, 4.5, 0.1)
days = st.slider("Days back", 1, 30, 7)

async def fetch_earthquakes(min_magnitude, days):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    start = datetime.now(timezone.utc) - timedelta(days=days)
    params = {"format": "geojson", "minmagnitude": min_magnitude, "starttime": start.strftime("%Y-%m-%d"), "orderby": "magnitude", "limit": 200}
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json(), start

data, start_date = asyncio.run(fetch_earthquakes(min_magnitude, days))
features = data["features"]
st.caption(f"{len(features)} events · M{min_magnitude}+ · since {start_date.strftime('%b %d, %Y')} · Source: USGS · Live data")

lats, lons, mags, texts = [], [], [], []
for eq in features:
    lon, lat, _ = eq["geometry"]["coordinates"]
    mag = eq["properties"]["mag"]
    eq_time = datetime.utcfromtimestamp(eq["properties"]["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
    lats.append(lat); lons.append(lon); mags.append(mag)
    texts.append(f"M{mag} — {eq['properties']['place']}<br>{eq_time}")

fig = go.Figure(go.Scattergeo(
    lat=lats, lon=lons, text=texts, hoverinfo="text",
    marker=dict(size=[max(m,1)*4 for m in mags], color=mags, colorscale="OrRd", colorbar=dict(title="Magnitude"), line=dict(width=0.5, color="black")),
    mode="markers",
))
fig.update_geos(showcountries=True, showcoastlines=True, showland=True, landcolor="rgb(243,243,243)")
fig.update_layout(height=650, margin=dict(t=30))
st.plotly_chart(fig, use_container_width=True)
