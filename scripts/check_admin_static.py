import os
import sys
from pathlib import Path

import django
from django.test import Client


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))


def fail(message: str) -> None:
    print(f"❌ {message}")
    sys.exit(1)


def main() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "school_system.settings")
    django.setup()

    client = Client()

    admin_login = client.get("/admin/login/")
    if admin_login.status_code != 200:
        fail(f"/admin/login/ returned {admin_login.status_code}")

    html = admin_login.content.decode("utf-8", errors="ignore")
    if "admin/css/base.css" not in html:
        fail("Admin login page does not reference admin/css/base.css")

    css_response = client.get("/static/admin/css/base.css")
    content_type = css_response.get("Content-Type", "")

    if css_response.status_code != 200:
        fail(f"/static/admin/css/base.css returned {css_response.status_code}")

    if "text/css" not in content_type:
        fail(f"Unexpected content type for admin css: {content_type}")

    print("✅ Admin static check passed: /admin/login/ references CSS and /static/admin/css/base.css is reachable")


if __name__ == "__main__":
    main()
