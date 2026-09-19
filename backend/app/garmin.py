import os

from dotenv import load_dotenv


load_dotenv()


DEFAULT_REDIRECT_URI = "http://127.0.0.1:8000/api/integrations/garmin/callback"
GARMIN_DEVELOPER_URL = "https://developer.garmin.com/gc-developer-program/"


def garmin_settings() -> dict:
    return {
        "consumer_key": os.getenv("GARMIN_CONSUMER_KEY", "").strip(),
        "consumer_secret": os.getenv("GARMIN_CONSUMER_SECRET", "").strip(),
        "redirect_uri": os.getenv("GARMIN_REDIRECT_URI", DEFAULT_REDIRECT_URI).strip(),
    }


def garmin_is_configured() -> bool:
    settings = garmin_settings()
    return bool(settings["consumer_key"] and settings["consumer_secret"])
