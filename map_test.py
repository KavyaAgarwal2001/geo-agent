import asyncio
from datetime import datetime, timedelta, timezone
import httpx
import plotly.graph_objects as go

async def fetch_earthquakes(min_magnitude=4.5, days=7):
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    start = datetime.now(timezone.utc) - timedelta(days=days)
    params = {
        "format": "geojson",
        "minmagnitude": min_magnitude,
        "starttime": start.strftime("%Y-%m-%d"),
        "orderby": "magnitude",
        "limit": 100,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        return resp.json(), start

def plot_earthquakes(data, start_date, min_magnitude, days):
    lats, lons, mags, texts = [], [], [], []
    for eq in data["features"]:
        lon, lat, _ = eq["geometry"]["coordinates"]
        mag = eq["properties"]["mag"]
        place = eq["properties"]["place"]
        eq_time = datetime.utcfromtimestamp(eq["properties"]["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
        lats.append(lat)
        lons.append(lon)
        mags.append(mag)
        texts.append(f"M{mag} — {place}<br>{eq_time}")

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    subtitle = (
        f"M{min_magnitude}+ · last {days} days (since {start_date.strftime('%b %d, %Y')}) · "
        f"{len(data['features'])} events · Source: USGS Earthquake Catalog · Generated {generated}"
    )

    fig = go.Figure(go.Scattergeo(
        lat=lats, lon=lons, text=texts, hoverinfo="text",
        marker=dict(
            size=[max(m, 1) * 4 for m in mags],
            color=mags, colorscale="OrRd",
            colorbar=dict(title="Magnitude"),
            line=dict(width=0.5, color="black"),
        ),
        mode="markers",
    ))
    fig.update_geos(showcountries=True, showcoastlines=True, showland=True, landcolor="rgb(243,243,243)")
    fig.update_layout(title=dict(text=f"Recent earthquakes worldwide<br><sub>{subtitle}</sub>"), height=650, margin=dict(t=90))
    fig.write_html("earthquake_map.html")
    print(f"Saved {len(data['features'])} earthquakes to earthquake_map.html")

async def main(min_magnitude=4.5, days=7):
    data, start_date = await fetch_earthquakes(min_magnitude, days)
    plot_earthquakes(data, start_date, min_magnitude, days)

if __name__ == "__main__":
    asyncio.run(main())
