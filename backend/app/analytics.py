from datetime import timedelta

import pandas as pd

from .data import ACTIVITIES, TRAINING_PLAN


def format_pace(minutes_per_km: float) -> str:
    minutes = int(minutes_per_km)
    seconds = round((minutes_per_km - minutes) * 60)
    if seconds == 60:
        minutes += 1
        seconds = 0
    return f"{minutes}:{seconds:02d}"


def activity_to_dict(activity: dict) -> dict:
    result = activity.copy()
    result["date"] = result["date"].isoformat()
    result["pace"] = format_pace(result["avg_pace_min_km"])
    return result


def build_splits(activity: dict) -> list[dict]:
    if activity["sport"] != "Run":
        return []

    full_kilometers = int(activity["distance_km"])
    remainder = round(activity["distance_km"] - full_kilometers, 1)
    pace_offsets = (-0.08, 0.03, 0.06, -0.04)
    splits = []

    for index in range(full_kilometers):
        pace = activity["avg_pace_min_km"] + pace_offsets[index % len(pace_offsets)]
        splits.append({"km": index + 1, "distance_km": 1.0, "pace": format_pace(pace)})

    if remainder:
        splits.append({"km": full_kilometers + 1, "distance_km": remainder, "pace": format_pace(activity["avg_pace_min_km"])})

    return splits


def activity_detail(activity: dict) -> dict:
    result = activity_to_dict(activity)
    result["splits"] = build_splits(activity)
    return result


def current_week_activities() -> list[dict]:
    latest = max(activity["date"] for activity in ACTIVITIES)
    week_start = latest - timedelta(days=6)
    return [activity for activity in ACTIVITIES if activity["date"] >= week_start]


def dashboard_summary() -> dict:
    week = current_week_activities()
    frame = pd.DataFrame(week)
    runs = frame[frame["sport"] == "Run"]
    distance = float(runs["distance_km"].sum()) if not runs.empty else 0
    load = int(frame["training_load"].sum()) if not frame.empty else 0
    avg_pace = float(runs["avg_pace_min_km"].mean()) if not runs.empty else 0
    avg_hr = int(round(runs["avg_heart_rate"].mean())) if not runs.empty else 0
    avg_cadence = int(round(runs["cadence"].mean())) if not runs.empty else 0
    recovery_score = max(0, 100 - min(80, round(load / 4)))

    if load >= 220:
        recommendation = "Recovery priority: keep the next run easy and skip hard intervals."
        recovery = "Needs attention"
    elif load >= 170:
        recommendation = "Keep Wednesday easy and reassess your legs before the weekend quality session."
        recovery = "Moderate"
    else:
        recommendation = "Recovery looks stable. Progress gently and keep one full rest day."
        recovery = "Good"

    return {
        "week_start": min(activity["date"] for activity in week).isoformat(),
        "week_end": max(activity["date"] for activity in week).isoformat(),
        "weekly_distance_km": round(distance, 1),
        "training_load": load,
        "run_count": len(runs),
        "avg_pace": format_pace(avg_pace) if avg_pace else "-",
        "avg_heart_rate": avg_hr,
        "avg_cadence": avg_cadence,
        "recovery": recovery,
        "recovery_score": recovery_score,
        "recommendation": recommendation,
        "recent_activities": [activity_to_dict(item) for item in ACTIVITIES[:4]],
    }


def adjusted_training_plan() -> list[dict]:
    plan = [item.copy() for item in TRAINING_PLAN]
    load = dashboard_summary()["training_load"]

    if load >= 220:
        plan[0].update({
            "type": "Recovery",
            "title": "Recovery run",
            "detail": "25-30 min very easy, stop if legs feel heavy",
            "status": "next",
        })
        plan[1].update({
            "type": "Rest",
            "title": "Rest and mobility",
            "detail": "Skip intervals; gentle mobility only",
            "status": "adjusted",
        })
        plan[2]["status"] = "planned"
        plan[5].update({
            "type": "Easy",
            "title": "Easy aerobic run",
            "detail": "Keep it conversational after recovery check",
            "status": "adjusted",
        })

    return plan
