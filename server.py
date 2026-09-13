# server.py
# agent/orchestrator.py 를 브라우저 채팅 UI로 감싸는 FastAPI 서버.
# 실행: uvicorn server:app --reload --port 8000  (ANTHROPIC_API_KEY / GEMINI_API_KEY 는
#       이 명령을 실행하는 터미널 세션에 미리 설정되어 있어야 한다 — 서버가 그 환경을 그대로 물려받는다)
#
# 로컬 개발 편의를 위해 /apps/generator, /apps/chiller 로 원본 계산 앱(generator-calc, 냉동기수량계산x)을
# 이 컴퓨터의 로컬 경로에서 정적 서빙한다 — 배포 서버(Render 등)에는 그 경로가 없으므로 자동으로 건너뛴다.
# 배포 후에는 각 앱을 Vercel에 별도 배포하고, GENERATOR_APP_URL / CHILLER_APP_URL 환경변수로
# 그 URL을 가리키게 하면 evidence[].url이 로컬 대신 그쪽을 쓴다 (agent/evidence.py 참고).
# 각 앱은 URL 쿼리 파라미터로 tool 호출과 동일한 입력값을 받아 자동으로 채워진 화면을 보여준다.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent.orchestrator import generate_review, PROVIDERS, DEFAULT_PROVIDER
from agent.evidence import build_evidence

app = FastAPI(title="데이터센터 설계검토 에이전트")

# Vercel에 별도 배포된 프론트엔드(static/index.html)가 이 도메인으로 /api/* 를 호출할 수 있게 허용.
# FRONTEND_ORIGIN을 실제 Vercel 도메인으로 지정하면 그 출처만 허용, 미지정시 전체 허용(*)한다.
_frontend_origin = os.environ.get("FRONTEND_ORIGIN")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_origin] if _frontend_origin else ["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# 로컬 전용 fallback 경로. 배포 서버엔 없는 경로라 존재하지 않으면 조용히 건너뛴다.
GENERATOR_APP_DIR = os.environ.get("GENERATOR_APP_LOCAL_DIR", r"D:\DATA\앱개발\generator-calc")
CHILLER_APP_DIR = os.environ.get("CHILLER_APP_LOCAL_DIR", r"D:\DATA\앱개발\냉동기수량계산x")
if os.path.isdir(GENERATOR_APP_DIR):
    app.mount("/apps/generator", StaticFiles(directory=GENERATOR_APP_DIR, html=True), name="generator-app")
if os.path.isdir(CHILLER_APP_DIR):
    app.mount("/apps/chiller", StaticFiles(directory=CHILLER_APP_DIR, html=True), name="chiller-app")


class ChatRequest(BaseModel):
    message: str
    provider: str = None
    api_key: str = None  # BYOK: 지정하면 서버 환경변수 대신 이 키를 사용 (브라우저 localStorage에서만 옴, 서버엔 저장 안 함)


class EvidenceItem(BaseModel):
    tool: str
    label: str
    url: str


class ChatResponse(BaseModel):
    reply: str
    provider: str
    error: bool = False
    evidence: List[EvidenceItem] = []


@app.get("/")
def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/config")
def get_config():
    return {"providers": list(PROVIDERS), "default_provider": DEFAULT_PROVIDER}


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    provider = (req.provider or DEFAULT_PROVIDER).lower()
    try:
        kwargs = {"api_key": req.api_key} if req.api_key else {}
        reply, tool_calls = generate_review(req.message, provider=provider, **kwargs)
        evidence = build_evidence(tool_calls)
        return ChatResponse(reply=reply, provider=provider, error=False, evidence=evidence)
    except Exception as e:
        return ChatResponse(reply=f"[오류] {e}", provider=provider, error=True, evidence=[])
