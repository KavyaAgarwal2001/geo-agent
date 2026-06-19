# geo-agent

Live earth-science data, in two shapes: a tool for AI agents, and an app for humans.

- 🔗 **Live demo:** https://kavyaagarwal-geo-agent.streamlit.app
- 🔧 **MCP server:** exposes the same data as tools for any [MCP](https://modelcontextprotocol.io) compatible AI client (Claude Desktop, Cursor, etc.)
- 📝 **Writeup:** https://kavya855084.substack.com/p/building-geo-agent-an-mcp-server

## What this is

This project exposes earth-science data through two interfaces, because they solve different problems.

- **The Streamlit app** is for humans. Open it, click around, look at charts, maps, and search results.
- **The MCP server** is for agents. It lets an AI assistant decide, on its own, to pull live data or search reference material as one step while reasoning about something else entirely.

Three data sources, both interfaces: live earthquakes (USGS), live climate data (NASA POWER), and semantic search over real climate science reports (IPCC AR6, SR15).

## Components

### 1. MCP server (`server.py`)
Exposes earth-science data as tools any MCP client can call.

**Tools:**
- `get_recent_earthquakes(min_magnitude, days)`: recent significant earthquakes worldwide, via [USGS](https://earthquake.usgs.gov). Read-only, annotated.
- `get_climate_point_data(latitude, longitude, days)`: recent daily temperature, precipitation, and solar radiation for any location, via [NASA POWER](https://power.larc.nasa.gov). Read-only, annotated. Handles NASA's processing-lag fill values gracefully instead of printing raw placeholder data.
- `search_climate_papers(query, n_results)`: semantic search over real climate science reports, see Component 3 below.

```bash
uv sync
uv run mcp dev server.py
```
Opens the MCP Inspector in your browser for testing tools directly.

### 2. Live web app (`app.py`)
Three tabs, same underlying data sources, built for human exploration:
- **Earthquakes**: live filtering by magnitude and time window, a magnitude reference guide, an interactive map, and a raw data table.
- **Climate**: pick a location (presets or custom coordinates), see temperature, precipitation, and solar radiation as time series, plus a location map.
- **Paper Search**: ask a question, get back cited passages from real climate science reports, the same retrieval pipeline as the MCP tool.

```bash
uv run streamlit run app.py
```

### 3. Climate paper search
A local retrieval-augmented search system over real climate science reports (IPCC AR6 Synthesis Report, SR15), available both as an MCP tool and as a tab in the web app, so the same retrieval logic is usable by an agent or a person.

**Pipeline:**
1. **Ingestion** (`ingest.py`, run once): PDFs in `papers/` are read page by page with `pypdf`, split into ~800-character chunks with 100-character overlap so meaning isn't lost at chunk boundaries, and embedded with `sentence-transformers` (`all-MiniLM-L6-v2`, runs locally, no API key or cost).
2. **Storage**: chunks, their embeddings, and metadata (source filename, page number) are persisted to a local [Chroma](https://www.trychroma.com) vector database, just a folder on disk, no server process to run.
3. **Retrieval**: a query is embedded with the same model, and Chroma returns the chunks whose embeddings are nearest to it by semantic similarity, not keyword overlap. Every result carries its source and page, so answers are traceable to a real document instead of generated from training data alone.

**Two interfaces, same pipeline:**
- `search_climate_papers(query, n_results)`, an MCP tool, callable autonomously by an agent
- The **Paper Search** tab in the web app, the same retrieval logic, for direct human use, with a visible note confirming results come from local search, not the internet

```bash
uv run python ingest.py
uv run pytest tests/test_retrieval.py -v
```

**Validation:** `tests/test_retrieval.py` checks that 5 real climate questions each return a relevant passage in their top 3 results. This is a lightweight check (keyword presence in top-k), not a full IR evaluation; a more rigorous version would use precision@k, MRR, or a framework like [Ragas](https://github.com/explodinggradients/ragas).

**Known limitations, documented honestly rather than hidden:**
- The corpus is small and curated (2 reports), not comprehensive literature coverage.
- Overlapping chunks can produce near-duplicate results from the same page; results are not currently deduplicated by source/page.
- PDF text extraction is occasionally noisy (e.g. figure captions interleaved with body text), a known limitation of plain-text PDF extraction, not something this project works around.

## Tech stack
Python, MCP SDK, Streamlit, Plotly, httpx, Chroma, sentence-transformers, pytest, uv

## Status
See commit history for progress. Connected to Claude Desktop and confirmed it correctly chooses between live-data tools and paper search depending on the question, and correctly recognizes when a question needs more than these three tools can offer. Next: a router agent that makes that same tool-selection decision explicitly, in code, instead of relying on the client's built-in reasoning.

## Author
Kavya Agarwal. [Website](https://kavyaagarwal2001.github.io) · [LinkedIn](https://in.linkedin.com/in/kavya-agarwal-5a77611a4)
