# agent/providers/gemini_provider.py
# Google Gemini API(google-genai SDK) 기반 구현.
# 자동 함수호출(Automatic Function Calling)로 일반 Python 함수를 tools=[...]에 그대로 전달한다 — 별도 루프 불필요.
# GEMINI_API_KEY 또는 GOOGLE_API_KEY 환경변수 필요.

import os

from google import genai
from google.genai import types

from agent.system_prompt import REVIEWER_PERSONA
from agent.tools_gemini import ALL_AGENT_TOOLS_GEMINI

# 2026-09 기준 확인된 모델 ID. 오류 발생 시 https://ai.google.dev/gemini-api/docs/models 에서 최신 ID 확인 후
# GEMINI_MODEL 환경변수로 재정의할 것.
DEFAULT_MODEL = "gemini-3.1-pro-preview"


def _resolve_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "GEMINI_API_KEY(또는 GOOGLE_API_KEY) 환경변수가 설정되어 있지 않습니다. "
            "https://aistudio.google.com/apikey 에서 키를 발급받아 설정하세요."
        )
    return key


def generate_review(user_query: str, model: str = None):
    """검토의견서 텍스트와, 실행된 tool 호출 내역([{tool, input}, ...])을 함께 반환한다."""
    client = genai.Client(api_key=_resolve_api_key())
    model = model or os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)

    response = client.models.generate_content(
        model=model,
        contents=user_query,
        config=types.GenerateContentConfig(
            system_instruction=REVIEWER_PERSONA,
            tools=ALL_AGENT_TOOLS_GEMINI,
        ),
    )

    tool_calls = []
    for content in (response.automatic_function_calling_history or []):
        for part in (content.parts or []):
            fc = getattr(part, "function_call", None)
            if fc is not None:
                tool_calls.append({"tool": fc.name, "input": dict(fc.args) if fc.args else {}})

    reply = response.text if response.text else "(응답 텍스트 없음 — response 객체를 직접 확인 필요)"
    return reply, tool_calls
