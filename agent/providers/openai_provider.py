# agent/providers/openai_provider.py
# OpenAI(GPT) Responses API 기반 구현. OPENAI_API_KEY 환경변수 필요 (또는 api_key 인자 — BYOK).
# tool 스키마와 실행은 agent/tools.py 의 @beta_tool 객체(.to_dict()/.call())를 그대로 재사용한다 —
# 계산 함수 정의는 tools_common.py 한 곳에만 있다.

import json
import os

from openai import OpenAI

from agent.system_prompt import REVIEWER_PERSONA
from agent.tools import ALL_AGENT_TOOLS

# OpenAI 모델 문서(developers.openai.com/api/docs/models)에서 "잘 모르겠으면 이것부터"로 권장하는 모델.
# 더 저렴한 모델(gpt-6-luna 등)을 쓰려면 OPENAI_MODEL 환경변수로 재정의.
DEFAULT_MODEL = "gpt-6-astra"
MAX_TOOL_ROUNDS = 12

_TOOLS_BY_NAME = {t.name: t for t in ALL_AGENT_TOOLS}


def _tool_definitions() -> list:
    defs = []
    for t in ALL_AGENT_TOOLS:
        d = t.to_dict()
        defs.append({
            "type": "function",
            "name": d["name"],
            "description": d.get("description", ""),
            "parameters": d["input_schema"],
        })
    return defs


def _run_tool(name: str, args: dict) -> str:
    tool = _TOOLS_BY_NAME.get(name)
    if tool is None:
        return json.dumps({"error": f"알 수 없는 tool: {name}"}, ensure_ascii=False)
    try:
        return tool.call(args)
    except Exception as e:
        return json.dumps({"error": f"{name} 실행 실패: {e}"}, ensure_ascii=False)


def generate_review(user_query: str, model: str = None, api_key: str = None):
    """검토의견서 텍스트와, 실행된 tool 호출 내역([{tool, input}, ...])을 함께 반환한다.

    api_key: 지정하면 OPENAI_API_KEY 환경변수 대신 이 키를 쓴다 (브라우저에서 사용자가 입력한 키 — BYOK).
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY 환경변수가 설정되어 있지 않습니다. "
            "https://platform.openai.com/api-keys 에서 키를 발급받아 설정하세요."
        )
    client = OpenAI(api_key=key)
    model = model or os.environ.get("OPENAI_MODEL", DEFAULT_MODEL)
    tools = _tool_definitions()

    conversation = [{"role": "user", "content": user_query}]
    tool_calls = []

    for _ in range(MAX_TOOL_ROUNDS):
        response = client.responses.create(
            model=model,
            instructions=REVIEWER_PERSONA,
            tools=tools,
            input=conversation,
        )
        # reasoning 항목 포함 모델 출력 전체를 입력에 이어붙여야 다음 라운드에서 맥락이 유지된다
        conversation += response.output

        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return (response.output_text or "(응답 텍스트 없음)"), tool_calls

        for item in calls:
            try:
                args = json.loads(item.arguments) if item.arguments else {}
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"tool": item.name, "input": args})
            conversation.append({
                "type": "function_call_output",
                "call_id": item.call_id,
                "output": _run_tool(item.name, args),
            })

    return "(tool 호출이 너무 많아 중단했습니다 — 질문을 더 구체적으로 나눠서 다시 시도해 주세요)", tool_calls
