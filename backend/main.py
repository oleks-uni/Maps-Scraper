import os
import json
import re
import tempfile
import asyncio

from io import BytesIO
from pydantic import BaseModel
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from starlette.concurrency import run_in_threadpool

from playwright_get_html import search_google_maps
from extract_from_html import parse_places
from excel_util import results_to_xlsx_bytes



app = FastAPI(title="Maps Scraper")

MAX_CONCURRENCY = 2
sem = asyncio.Semaphore(MAX_CONCURRENCY)


class ScrapeRequest(BaseModel):
    location: str


@app.post("/api/scrape/excel")
async def scrape_excel(location: str = Query(..., description="enter location")):
    async with sem:
        try:
            html = await run_in_threadpool(search_google_maps, location)
            results = parse_places(html)
            xlsx_bytes = results_to_xlsx_bytes(results)
            filename = f"places_{re.sub(r'[^a-zA-Z0-9_-]+', '_', location)[:60]}.xlsx"
            headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

            return StreamingResponse(
                BytesIO(xlsx_bytes),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers=headers,
            )

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/scrape/json")
async def scrape(location: str = Query(..., description="enter location")):
    async with sem:
        try:
            html = await run_in_threadpool(search_google_maps, location)

            results = parse_places(html)
            payload = {"query": location, "count": len(results), "results": results}

            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
            with open(tmp.name, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            filename = f"places_{re.sub(r'[^a-zA-Z0-9_-]+', '_', location)[:60]}.json"
            return FileResponse(tmp.name, media_type="application/json", filename=filename)

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        




BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/")
def serve_frontend():
    return FileResponse(
        os.path.join(FRONTEND_DIR, "index.html"),
        media_type="text/html"
    )