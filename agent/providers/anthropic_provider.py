# agent/providers/anthropic_provider.py
# Anthropic Tool Runner 기반 구현. ANTHROPIC_API_KEY 환경변수(또는 ant auth login 프로필) 필요.

import anthropic

from agent.system_prompt import REVIEWER_PERSONA
from agent.tools import ALL_AGENT_TOOLS

DEFAULT_MODEL = "claude-opus-5"


def generate_review(user_query: str, model: str = DEFAULT_MODEL, max_tokens: int = 16000, api_key: str = None):
    """검토의견서 텍스트와, 실행된 tool 호출 내역([{tool, input}, ...])을 함께 반환한다.

    api_key: 지정하면 ANTHROPIC_API_KEY 환경변수 대신 이 키로 클라이언트를 만든다
             (브라우저에서 사용자가 직접 입력한 키를 쓸 때 — BYOK).
    """
    client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()

    runner = client.beta.messages.tool_runner(
        model=model,
        max_tokens=max_tokens,
        system=REVIEWER_PERSONA,
        tools=ALL_AGENT_TOOLS,
        messages=[{"role": "user", "content": user_query}],
    )

    last_message = None
    tool_calls = []
    for message in runner:
        last_message = message
        for block in message.content:
            if block.type == "tool_use":
                tool_calls.append({"tool": block.name, "input": dict(block.input) if block.input else {}})

    if last_message is None:
        return "(응답 없음)", tool_calls

    texts = [b.text for b in last_message.content if b.type == "text"]
    reply = "\n".join(texts) if texts else "(text 블록 없음 — 마지막 메시지를 직접 확인 필요)"
    return reply, tool_calls
