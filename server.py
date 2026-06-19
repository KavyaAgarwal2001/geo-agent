from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("geo-agent")

READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

@mcp.tool(annotations=READ_ONLY)
async def get_recent_earthquakes(min_magnitude: float = 4.5, days: int = 7) -> str:
    """Get recent significant earthquakes worldwide from USGS.

    Args:
        min_magnitude: minimum magnitude to include (default 4.5)
        days: how many days back to search (default 7)
    """
    url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    params = {
        "format": "geojson",
        "minmagnitude": min_magnitude,
        "starttime": (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d"),
        "orderby": "magnitude",
        "limit": 10,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10.0)
        resp.raise_for_status()
        data = resp.json()

    if not data["features"]:
        return f"No earthquakes above magnitude {min_magnitude} in the last {days} days."

    lines = [f"Earthquakes above M{min_magnitude} in the last {days} days:"]
    for eq in data["features"]:
        props = eq["properties"]
        time_str = datetime.utcfromtimestamp(props["time"] / 1000).strftime("%Y-%m-%d %H:%M UTC")
        lines.append(f"- M{props['mag']} — {props['place']} — {time_str}")
    return "\n".join(lines)


@mcp.tool(annotations=READ_ONLY)
async def get_climate_point_data(latitude: float, longitude: float, days: int = 7) -> str:
    """Get recent daily climate data (temperature, precipitation, solar radiation) for a location, from NASA POWER.

    Args:
        latitude: latitude of the location, -90 to 90
        longitude: longitude of the location, -180 to 180
        days: how many days of data to fetch (default 7). NASA POWER has a few days of processing lag, so this ends a few days before today, not today.
    """
    end = datetime.utcnow() - timedelta(days=3)
    start = end - timedelta(days=days)
    url = "https://power.larc.nasa.gov/api/temporal/daily/point"
    params = {
        "parameters": "T2M,PRECTOTCORR,ALLSKY_SFC_SW_DWN",
        "community": "AG",
        "longitude": longitude,
        "latitude": latitude,
        "start": start.strftime("%Y%m%d"),
        "end": end.strftime("%Y%m%d"),
        "format": "JSON",
    }
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=15.0)
        resp.raise_for_status()
        data = resp.json()

    param_data = data["properties"]["parameter"]
    dates = sorted(param_data["T2M"].keys())

    lines = [f"Climate data for ({latitude}, {longitude}), {dates[0]} to {dates[-1]} (Source: NASA POWER):"]
    for d in dates:
        temp = param_data["T2M"][d]
        precip = param_data["PRECTOTCORR"][d]
        solar = param_data["ALLSKY_SFC_SW_DWN"][d]
        solar_str = "not yet available" if solar == -999.0 else f"{solar} kWh/m²/day"
        lines.append(f"- {d}: {temp}°C avg temp, {precip} mm/day precip, {solar_str} solar radiation")
        #lines.append(f"- {d}: {temp}°C avg temp, {precip} mm/day precip, {solar} kWh/m²/day solar radiation")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
