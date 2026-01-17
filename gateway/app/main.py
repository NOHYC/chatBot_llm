import os
import httpx
from fastapi import FastAPI

app = FastAPI()

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://vllm:8002")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/ready")
def ready():
    # vLLM이 떠서 /v1/models 응답하는지로 readiness 판단
    try:
        with httpx.Client(timeout=2.0) as client:
            r = client.get(f"{VLLM_BASE_URL}/v1/models")
            r.raise_for_status()
        return {"ready": True}
    except Exception as e:
        return {"ready": False, "error": str(e)}

@app.post("/v1/chat/completions")
async def proxy_chat_completions(payload: dict):
    # 게이트웨이에서 vLLM OpenAI 호환 엔드포인트로 프록시
    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(f"{VLLM_BASE_URL}/v1/chat/completions", json=payload)
        r.raise_for_status()
        return r.json()
