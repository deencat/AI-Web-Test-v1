import asyncio
import httpx

async def main():
    r = httpx.post(
        "http://127.0.0.1:8000/api/v1/auth/login",
        data={"username": "admin", "password": "admin123"},
        timeout=30,
    )
    token = r.json()["access_token"]
    h = {"Authorization": f"Bearer {token}"}
    pid = "cmrcykllf0001s5015ynk8uhc"

    from app.services import reqiq_client as reqiq

    sources = await reqiq.list_sources(pid)
    print("sources type", type(sources))
    items = sources if isinstance(sources, list) else sources.get("items") or sources.get("sources") or []
    print("source count", len(items))
    for s in items[:5]:
        print(" -", s.get("originalFilename") or s.get("filename"), s.get("status"))

    print("reindex...")
    try:
        ri = await reqiq.reindex_embeddings(pid)
        print("reindex ok", str(ri)[:200])
    except Exception as exc:
        print("reindex failed", exc)

    cp = httpx.post(
        "http://127.0.0.1:8000/api/v1/products/5g-mobile-broadband/compile-wiki",
        headers=h,
        timeout=600,
    )
    print("compile", cp.status_code, cp.text[:500])

asyncio.run(main())
