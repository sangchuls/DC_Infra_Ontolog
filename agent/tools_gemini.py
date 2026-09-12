# agent/tools_gemini.py
# Gemini 자동 함수호출(Automatic Function Calling)용 — 일반 Python 함수를 그대로 tools=[...] 에 전달한다.
# (google-genai SDK가 타입힌트+docstring에서 스키마를 자동 추출한다. 별도 데코레이션 불필요)

from agent.tools_common import ALL_TOOL_FUNCS as ALL_AGENT_TOOLS_GEMINI

__all__ = ["ALL_AGENT_TOOLS_GEMINI"]
