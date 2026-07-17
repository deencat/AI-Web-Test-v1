import httpx
from pathlib import Path

path = Path(
    r"C:/Users/andrechw/OneDrive - hutchison3hk/Documents/AI-Web-Test-v1-2/docs/5G 流動寬頻/Sample of DT Offer Table_20250729_updated.xlsx"
)
if not path.is_file():
    raise SystemExit(f"Missing: {path}")

data = path.read_bytes()
login = httpx.post(
    "http://127.0.0.1:8000/api/v1/auth/login",
    data={"username": "admin", "password": "admin123"},
    timeout=30,
)
login.raise_for_status()
token = login.json()["access_token"]
headers = {"Authorization": f"Bearer {token}"}
files = [
    (
        "files",
        (
            path.name,
            data,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
    )
]
resp = httpx.post(
    "http://127.0.0.1:8000/api/v1/products/5g-mobile-broadband/upload",
    headers=headers,
    files=files,
    timeout=300,
)
print("status", resp.status_code)
print(resp.text[:1500])
