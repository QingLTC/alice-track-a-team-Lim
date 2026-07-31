"""Thin HTTP client for the FastAPI backend.

The dashboard runs NO model logic itself: every prediction, metric and
optimization comes from the backend through these functions. Each returns a
tuple (ok: bool, data_or_error) so pages can show a clean message on failure.

"""

import requests

DEFAULT_BASE = "http://127.0.0.1:8000"


def _detail(resp) -> str:
  """Pull a human message out of an error response (GIVEN)."""
  try:
    detail = resp.json().get("detail", resp.text)
    if isinstance(detail, list):
      return "; ".join(
          f"{'.'.join(map(str, item.get('loc', [])))}: {item.get('msg', item)}"
          for item in detail
      )
    return str(detail)
  except Exception:
    return resp.text or f"HTTP {resp.status_code}"


def health(base: str = DEFAULT_BASE):
  """GET /health -> (ok, data). GIVEN as the pattern to copy."""
  try:
    r = requests.get(f"{base}/health", timeout=10)
    r.raise_for_status()
    return True, r.json()
  except requests.HTTPError:
    return False, _detail(r)
  except Exception as exc:
    return False, str(exc)


def model_info(base: str = DEFAULT_BASE):
  """GET /model-info -> (ok, data_or_error)."""
  try:
    r = requests.get(f"{base}/model-info", timeout=10)
    r.raise_for_status()
    return True, r.json()
  except requests.HTTPError:
    return False, _detail(r)
  except Exception as exc:
    return False, str(exc)


def forecast(
    base: str = DEFAULT_BASE,
    file_bytes: bytes = b"",
    filename: str = "",
    last_hours=None,
):
  """POST /forecast as multipart/form-data."""
  try:
    params = {"last_hours": last_hours} if last_hours else {}
    files = {"file": (filename, file_bytes, "text/csv")}
    r = requests.post(
        f"{base}/forecast", files=files, params=params, timeout=120
    )
    r.raise_for_status()
    return True, r.json()
  except requests.HTTPError:
    return False, _detail(r)
  except Exception as exc:
    return False, str(exc)


def optimize(base: str = DEFAULT_BASE, payload: dict = None):
  """POST /optimize with json payload."""
  try:
    r = requests.post(
        f"{base}/optimize", json=payload or {}, timeout=60
    )
    r.raise_for_status()
    return True, r.json()
  except requests.HTTPError:
    return False, _detail(r)
  except Exception as exc:
    return False, str(exc)