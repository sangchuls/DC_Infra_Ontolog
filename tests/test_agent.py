"""agent/ 레이어 스모크 테스트 — 실제 API 호출 없이 도구 등록/스키마 생성만 검증.
실행: python tests/test_agent.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.system_prompt import REVIEWER_PERSONA
from agent.tools import ALL_AGENT_TOOLS
from agent.tools_gemini import ALL_AGENT_TOOLS_GEMINI
from agent.knowledge_base import list_projects, load_project

if __name__ == "__main__":
    assert len(REVIEWER_PERSONA) > 100
    print(f"[OK] persona 길이: {len(REVIEWER_PERSONA)}자")

    print(f"[OK] Anthropic tool {len(ALL_AGENT_TOOLS)}개:")
    for t in ALL_AGENT_TOOLS:
        name = getattr(t, "name", getattr(t, "__name__", str(t)))
        print(f"  - {name}")

    print(f"\n[OK] Gemini tool {len(ALL_AGENT_TOOLS_GEMINI)}개:")
    for f in ALL_AGENT_TOOLS_GEMINI:
        print(f"  - {f.__name__}")
    assert len(ALL_AGENT_TOOLS) == len(ALL_AGENT_TOOLS_GEMINI), "두 프로바이더의 tool 개수가 일치해야 함"

    # provider 디스패처가 잘못된 provider 이름을 거부하는지 확인
    from agent.orchestrator import generate_review
    try:
        generate_review("test", provider="unknown-llm")
        raise AssertionError("알 수 없는 provider가 거부되지 않음")
    except ValueError:
        print("\n[OK] 알 수 없는 provider 거부 확인")

    projects = list_projects()
    print(f"\n[OK] 지식베이스 프로젝트 {len(projects)}개:")
    for p in projects:
        print(f"  - {p}")

    gapyeong = load_project("가평DC_수전용량검토")
    assert gapyeong["ontology"] is not None, "가평 DC 온톨로지 로드 실패"
    assert "entities" in gapyeong["ontology"]
    print("\n[OK] 가평DC_수전용량검토 온톨로지 로드 성공, scenarios:",
          [s["id"] for s in gapyeong["ontology"]["entities"]["scenarios"]])

    print("\nAll agent smoke tests passed (no live API call made).")
