import os
from pathlib import Path

from dotenv import load_dotenv


def configure_settings(default_module):
    load_dotenv(Path(__file__).resolve().parent.parent / ".env", interpolate=False)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", default_module)
