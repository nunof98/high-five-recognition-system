import base64

import requests
import streamlit as st


def _headers() -> dict:
    token = st.secrets["github"]["token"]
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _api_url(path: str) -> str:
    repo = st.secrets["github"]["repo"]
    return f"https://api.github.com/repos/{repo}/contents/{path}"


def get_file(path: str) -> tuple[bytes, str]:
    """Fetch a file from GitHub. Returns (raw_bytes, sha).

    Raises FileNotFoundError if the path doesn't exist yet.
    """
    resp = requests.get(_api_url(path), headers=_headers(), timeout=15)
    if resp.status_code == 404:
        raise FileNotFoundError(f"{path} not found in GitHub repo")
    resp.raise_for_status()
    data = resp.json()
    raw = base64.b64decode(data["content"])
    return raw, data["sha"]


def put_file(
    path: str,
    content_bytes: bytes,
    sha: str | None,
    commit_message: str,
) -> str:
    """Create or update a file in GitHub. Returns the new SHA."""
    payload: dict = {
        "message": commit_message,
        "content": base64.b64encode(content_bytes).decode(),
    }
    if sha:
        payload["sha"] = sha

    resp = requests.put(
        _api_url(path), headers=_headers(), json=payload, timeout=15
    )
    resp.raise_for_status()
    return resp.json()["content"]["sha"]
