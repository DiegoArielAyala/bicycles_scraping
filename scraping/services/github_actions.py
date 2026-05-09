import requests

from django.conf import settings

def trigger_github_action(data):
    url = "https://api.github.com/repos/USER/REPO/actions/workflow/scraping.yml/dispatches"

    headers = {
        "Authorization": f"Bearer {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }

    payload = {
        "ref": "main",
        "inputs": {
            "start_page": str(data["start_page"]),
            "last_page" : str(data["last_page"]),
            "web": str(data["web"]),
            "delete": bool(data["delete"]),
        }
    }

    requests.post(url=url, json=payload, headers=headers)