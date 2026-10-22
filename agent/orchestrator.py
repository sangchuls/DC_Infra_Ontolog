# agent/orchestrator.py
# "복제 인격" 에이전트 진입점 — Anthropic(Claude) / Gemini / OpenAI(GPT) 중 선택 가능.
#
# 실행 전제: 선택한 프로바이더의 API 키가 환경변수로 설정되어 있어야 한다.
#   Anthropic: ANTHROPIC_API_KEY (또는 `ant auth login` 프로필)
#   Gemini:    GEMINI_API_KEY 또는 GOOGLE_API_KEY
#   OpenAI:    OPENAI_API_KEY
# 이 모듈은 키를 직접 다루지 않으며, 각 provider 모듈이 환경변수에서 읽는다.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PROVIDERS = ("anthropic", "gemini", "openai")
DEFAULT_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic")


def generate_review(user_query: str, provider: str = None, **kwargs):
    """사용자 질의(설계 조건)를 받아 (검토의견서 텍스트, tool 호출 내역) 튜플을 반환한다.
    tool 호출 내역은 agent.evidence.build_evidence로 계산 앱 화면 링크로 변환할 수 있다.

    provider: 'anthropic' | 'gemini' | 'openai'. 미지정시 LLM_PROVIDER 환경변수, 그것도 없으면 'anthropic'.
    """
    provider = (provider or DEFAULT_PROVIDER).lower()
    if provider not in PROVIDERS:
        raise ValueError(f"알 수 없는 provider: {provider} (선택지: {PROVIDERS})")

    if provider == "anthropic":
        from agent.providers.anthropic_provider import generate_review as _run
    elif provider == "openai":
        from agent.providers.openai_provider import generate_review as _run
    else:
        from agent.providers.gemini_provider import generate_review as _run

    return _run(user_query, **kwargs)


def _choose_provider_interactively() -> str:
    print("사용할 LLM을 선택하세요:")
    for i, p in enumerate(PROVIDERS, 1):
        default_mark = " (기본값)" if p == DEFAULT_PROVIDER else ""
        print(f"  {i}. {p}{default_mark}")
    choice = input(f"번호 또는 이름 입력 [{DEFAULT_PROVIDER}]> ").strip()
    if not choice:
        return DEFAULT_PROVIDER
    if choice.isdigit() and 1 <= int(choice) <= len(PROVIDERS):
        return PROVIDERS[int(choice) - 1]
    if choice.lower() in PROVIDERS:
        return choice.lower()
    print(f"'{choice}'는 알 수 없는 선택입니다. 기본값({DEFAULT_PROVIDER})을 사용합니다.")
    return DEFAULT_PROVIDER


def run_cli():
    provider = _choose_provider_interactively()
    print(f"\n데이터센터 설계검토 에이전트 [{provider}] — 종료하려면 빈 줄 입력\n")
    while True:
        try:
            query = input("설계 조건 / 질의> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not query:
            break
        print("\n" + "=" * 70)
        try:
            text, tool_calls = generate_review(query, provider=provider)
            print(text)
            if tool_calls:
                from agent.evidence import build_evidence
                print("\n[계산 근거]")
                for ev in build_evidence(tool_calls):
                    print(f"  - {ev['label']}: http://127.0.0.1:8000{ev['url']}  (서버 켜져있을 때만 유효)")
        except Exception as e:
            print(f"[오류] {e}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    run_cli()
