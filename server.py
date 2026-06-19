from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
import httpx

mcp = FastMCP("climate-data")

@mcp.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)

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

if __name__ == "__main__":
    mcp.run()
