from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from .analytics import adjusted_training_plan, activity_detail, activity_to_dict, dashboard_summary
from .data import ACTIVITIES
from .garmin import GARMIN_DEVELOPER_URL, garmin_is_configured, garmin_settings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"

app = FastAPI(title="AI Personal Running Coach", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/activities")
def get_activities() -> list[dict]:
    return [activity_to_dict(activity) for activity in ACTIVITIES]


@app.get("/api/activities/{activity_id}")
def get_activity(activity_id: int) -> dict:
    activity = next((item for item in ACTIVITIES if item["id"] == activity_id), None)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity_detail(activity)


@app.get("/api/dashboard")
def get_dashboard() -> dict:
    return dashboard_summary()


@app.get("/api/training-plan")
def get_training_plan() -> list[dict]:
    return adjusted_training_plan()


@app.get("/api/athlete")
def get_athlete() -> dict:
    return {
        "name": "Runner",
        "goal": "Build consistent aerobic fitness",
        "target_race": "10K personal best",
        "target_date": "2026-11-15",
        "current_phase": "Base building",
    }


@app.get("/api/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/api/integrations/garmin/status")
def get_garmin_status() -> dict:
    return {
        "configured": garmin_is_configured(),
        "redirect_uri": garmin_settings()["redirect_uri"],
        "developer_program_url": GARMIN_DEVELOPER_URL,
    }


@app.get("/api/integrations/garmin/connect")
def connect_garmin() -> dict:
    if not garmin_is_configured():
        raise HTTPException(
            status_code=503,
            detail="Garmin access is not configured. Apply for Garmin Connect Developer Program access first.",
        )
    raise HTTPException(
        status_code=501,
        detail="Garmin credentials are present, but the approved Garmin authorization flow still needs to be enabled.",
    )


@app.get("/api/integrations/garmin/callback", response_class=HTMLResponse)
def garmin_callback() -> str:
    return "<h1>Garmin callback is ready for the next integration step.</h1><p>Data sync will be enabled after Garmin Developer Program access and secure token storage are configured.</p>"


app.mount("/assets", StaticFiles(directory=FRONTEND_DIR), name="assets")


@app.get("/{path:path}")
def serve_frontend(path: str = ""):
    requested = FRONTEND_DIR / path
    if path and requested.is_file():
        return FileResponse(requested)
    return FileResponse(FRONTEND_DIR / "index.html")
