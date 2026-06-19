from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
import httpx
import chromadb
from chromadb.utils import embedding_functions

mcp = FastMCP("geo-agent")

READ_ONLY = {
    "readOnlyHint": True,
    "destructiveHint": False,
    "idempotentHint": True,
    "openWorldHint": True,
}

# Loaded once at server startup, not per-call, since loading the embedding
# model takes a few seconds and the server stays running between tool calls.
CHROMA_PATH = "./chroma_db"
_embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)
_chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)


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
    return "\n".join(lines)


@mcp.tool(annotations=READ_ONLY)
def search_climate_papers(query: str, n_results: int = 3) -> str:
    """Search real climate science reports (IPCC AR6, SR15) for passages relevant to a question.
    Returns the most relevant passages with their source document and page number,
    so answers can be grounded in real citations instead of relying on training data alone.

    Args:
        query: the question or topic to search for
        n_results: how many passages to return (default 3, max 10)
    """
    try:
        collection = _chroma_client.get_collection(
            name="climate_papers", embedding_function=_embedding_fn
        )
    except Exception:
        return (
            "No climate paper index found. Add PDFs to papers/ and run "
            "`uv run python ingest.py` first."
        )

    n_results = max(1, min(n_results, 10))
    results = collection.query(query_texts=[query], n_results=n_results)

    docs = results["documents"][0]
    metas = results["metadatas"][0]

    if not docs:
        return f"No relevant passages found for: {query}"

    lines = [f"Top {len(docs)} passages for: {query}\n"]
    for doc, meta in zip(docs, metas):
        snippet = doc.strip().replace("\n", " ")
        lines.append(f"[{meta['source']}, page {meta['page']}]\n{snippet}\n")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
