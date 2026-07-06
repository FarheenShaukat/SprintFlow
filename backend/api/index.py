import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django
from django.core.management import call_command
from django.core.wsgi import get_wsgi_application

django.setup()

if os.environ.get("VERCEL"):
    call_command("migrate", interactive=False, verbosity=0)

app = get_wsgi_application()
application = app
