"""Temporary evaluator API check for Feature 3 — delete after eval."""
import json
import os
import urllib.parse
import urllib.request

BASE = "http://127.0.0.1:8000/api/v1"


def req(method: str, path: str, token: str | None = None, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    request = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(request) as resp:
        return json.loads(resp.read())


def main():
    login_data = urllib.parse.urlencode(
        {"username": "admin", "password": "admin123"}
    ).encode()
    login_req = urllib.request.Request(
        f"{BASE}/auth/login", data=login_data, method="POST"
    )
    login_req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(login_req) as resp:
        token = json.loads(resp.read())["access_token"]
    print("token_ok", bool(token))

    put = req("PUT", "/tests/1399", token, {"requires_runtime_credentials": True})
    print(
        "PUT",
        put["requires_runtime_credentials"],
        "password_in",
        "password" in put,
        "login_credentials_in",
        "login_credentials" in put,
    )

    get = req("GET", "/tests/1399", token)
    print("GET", get["requires_runtime_credentials"])

    lst = req("GET", "/tests?page=1&size=50", token)
    match = next(i for i in lst["items"] if i["id"] == 1399)
    print("LIST", match["requires_runtime_credentials"])

    clone = req("POST", "/tests/1399/clone", token, {})
    print("CLONE", clone["id"], clone["requires_runtime_credentials"])

    put_f = req("PUT", "/tests/1399", token, {"requires_runtime_credentials": False})
    get_f = req("GET", "/tests/1399", token)
    print("FALSE_PUT", put_f["requires_runtime_credentials"], "FALSE_GET", get_f["requires_runtime_credentials"])

    put_t = req("PUT", "/tests/1399", token, {"requires_runtime_credentials": True})
    print("RESET_TRUE", put_t["requires_runtime_credentials"])

    tmp = os.environ.get("TEMP", ".")
    with open(os.path.join(tmp, "awt_eval_clone_id.txt"), "w", encoding="utf-8") as f:
        f.write(str(clone["id"]))
    with open(os.path.join(tmp, "awt_eval_test_id.txt"), "w", encoding="utf-8") as f:
        f.write("1399")
    with open(os.path.join(tmp, "awt_eval_token.txt"), "w", encoding="utf-8") as f:
        f.write(token)
    print("done")


if __name__ == "__main__":
    main()
