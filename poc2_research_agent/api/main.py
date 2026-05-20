"""FastAPI backend for the Research & Report Agent."""
import asyncio
import json
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

from poc2_research_agent.main import run_agent
from poc2_research_agent.api.history import init_db, save_run, get_history, get_brief_text

app = FastAPI(title="Research & Report Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# All API routes live under /api so the React proxy (/api → :8000/api) works correctly
api = APIRouter(prefix="/api")

# In-memory job store: job_id -> {"status", "events": [], "result": None}
jobs: dict = {}


@app.on_event("startup")
def startup():
    init_db()


# ─── POST /api/run ────────────────────────────────────────────────────────────
@api.post("/run")
async def start_run(body: dict):
    """Start an agent run in a background thread. Returns {job_id}."""
    company = body.get("company", "").strip()
    scenario = body.get("scenario", "S-A").strip()
    if not company:
        raise HTTPException(status_code=400, detail="company is required")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "events": [], "result": None}

    def run():
        events = jobs[job_id]["events"]

        def on_event(event_type: str, data: dict):
            events.append({"type": event_type, "data": data})

        try:
            result = run_agent(company, scenario, on_event=on_event)
            # Read the generated brief
            brief_text = ""
            try:
                brief_text = get_brief_text(result["brief_path"])
            except Exception:
                pass

            # Persist to SQLite
            try:
                save_run(result, brief_text=brief_text)
            except Exception:
                pass

            jobs[job_id]["result"] = result
            jobs[job_id]["status"] = "complete"
            events.append({"type": "complete", "data": result})
        except Exception as e:
            jobs[job_id]["status"] = "error"
            events.append({"type": "error", "data": {"message": str(e)}})

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return {"job_id": job_id}


# ─── GET /api/stream/{job_id} ─────────────────────────────────────────────────
@api.get("/stream/{job_id}")
async def stream(job_id: str):
    """SSE stream of agent events. Closes when job status is complete or error."""

    async def generator():
        if job_id not in jobs:
            yield {"data": json.dumps({"type": "error", "data": {"message": "job not found"}})}
            return

        sent = 0
        while True:
            job = jobs.get(job_id)
            if not job:
                break

            events = job["events"]
            while sent < len(events):
                yield {"data": json.dumps(events[sent])}
                sent += 1

            if job["status"] in ("complete", "error"):
                break

            await asyncio.sleep(0.3)

    return EventSourceResponse(generator())


# ─── GET /api/history ─────────────────────────────────────────────────────────
@api.get("/history")
async def list_history(limit: int = 20):
    """Return the most recent runs."""
    return get_history(limit=limit)


@api.get("/history/{company}")
async def company_history(company: str, limit: int = 20):
    """Return recent runs for a specific company."""
    return get_history(company=company, limit=limit)


# ─── GET /api/brief/{job_id} ──────────────────────────────────────────────────
@api.get("/brief/{job_id}")
async def get_brief(job_id: str):
    """Return the brief markdown for a completed job."""
    job = jobs.get(job_id)
    if not job or job["status"] != "complete":
        raise HTTPException(status_code=404, detail="Job not found or not complete")
    result = job.get("result", {})
    brief_path = result.get("brief_path", "")
    text = get_brief_text(brief_path)
    return {"brief_path": brief_path, "brief_text": text}


# ─── GET /api/brief (by path query param) ────────────────────────────────────
@api.get("/brief")
async def get_brief_by_path(path: str):
    """Return brief markdown as plain text given a file path."""
    from pathlib import Path as _Path
    try:
        text = _Path(path).read_text(encoding="utf-8")
        return PlainTextResponse(content=text, media_type="text/plain; charset=utf-8")
    except Exception:
        raise HTTPException(status_code=404, detail="Brief not found")


# Register the /api router
app.include_router(api)

# ─── Serve static frontend build (MUST be last — catches all remaining routes) ─
_frontend_build = Path(__file__).parent.parent.parent / "frontend" / "build"
if _frontend_build.exists():
    app.mount("/", StaticFiles(directory=str(_frontend_build), html=True), name="static")
