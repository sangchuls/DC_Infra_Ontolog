# 데이터센터 통합검토 시스템 — 백엔드

기존 계산 앱들의 검증 로직을 Python 순수 함수(`engine/`)로 이식하고, LangChain `@tool`로 래핑(`tools/`)한 것.
`data/knowledge_base/가평DC_수전용량검토/ontology.json`의 `tool_bindings`가 온톨로지 엔티티와 이 tool들을 연결한다.
이 리포는 자기완결적이다 — 다른 프로젝트 폴더의 절대경로를 참조하지 않으므로 그대로 배포 가능하다.

## 구조

```
engine/               순수 계산 함수 (프레임워크 비의존, 그대로 단위 테스트 가능)
  kds_loads.py         KDS 하중 데이터베이스        ← structural_estimator/api/data/kds_loads.py 복사
  beam_calc.py          보/슬래브 산정               ← structural_estimator/api/engine/beam_calc.py 복사
  column_calc.py         기둥 산정                    ← structural_estimator/api/engine/column_calc.py 복사
  foundation_calc.py      기초/토압벽체 산정            ← structural_estimator/api/engine/foundation_calc.py 복사
  generator_calc.py        발전기실 급배기 개구면적 산정   ← generator-calc/app.jsx 의 compute() 를 Python으로 포팅
  chiller_calc.py           냉동기 대수·저수조 산정        ← 냉동기수량계산x/script.js 의 computeWater/Air 를 Python으로 포팅

tools/                LangChain @tool 래퍼 (engine/ 함수를 그대로 호출) — 다른 오케스트레이터와 통합할 때 사용
  structural_tools.py    STRUCTURAL_TOOLS (8개)
  generator_tools.py      GENERATOR_TOOLS (1개)
  chiller_tools.py         CHILLER_TOOLS (3개)
  __init__.py               ALL_TOOLS = 위 3개 합친 리스트

agent/                "복제 인격" — Claude/Gemini 중 선택 가능한 검토의견서 생성 에이전트 (Step 4)
  system_prompt.py       페르소나. 검토의견서.pdf(김상범 소장 작성본)의 4단 구조·문체를 그대로 인코딩
  knowledge_base.py        프로젝트 온톨로지 파일기반 지식베이스. data/knowledge_base/<프로젝트명>/ 폴더를
                              스캔한다 (ontology.json 필수, description.md 선택) — 새 프로젝트는 폴더만 추가하면 됨
  evidence.py               tool 호출 내역을 계산 앱 화면 링크로 변환 (GENERATOR_APP_URL/CHILLER_APP_URL로 배포 URL 지정)
  tools_common.py           프로바이더 비의존 tool 함수 (engine/ + knowledge_base 호출, 8개) — 실제 로직은 여기 한 곳
  tools.py                  Anthropic 전용: tools_common을 @beta_tool로 래핑
  tools_gemini.py            Gemini 전용: tools_common 함수를 그대로 노출 (자동 함수호출)
  providers/
    anthropic_provider.py     client.beta.messages.tool_runner 기반 구현
    gemini_provider.py         client.models.generate_content + 자동 함수호출 기반 구현
  orchestrator.py            진입점(디스패처). generate_review(query, provider="anthropic"|"gemini")
                              CLI: python -m agent.orchestrator (실행 시 provider 선택 프롬프트)

tests/
  test_engine.py         engine/ 함수 스모크 테스트 — langchain/anthropic/google-genai 없이도 실행 가능
  test_tools.py           tools/ @tool 래퍼 스모크 테스트 — langchain-core 필요
  test_agent.py            agent/ 도구 등록(양쪽 프로바이더 모두)·지식베이스 스모크 테스트 — 실제 API 호출 없음
```

## 실행

```bash
pip install -r requirements.txt
python tests/test_engine.py
python tests/test_tools.py
python tests/test_agent.py        # 실제 API 호출 없이 두 프로바이더의 도구 등록만 검증

# 실제 검토의견서 생성 (선택한 프로바이더의 API 키 필요 — 과금 발생)
python -m agent.orchestrator
```

`agent/orchestrator.py`는 `provider` 인자(또는 `LLM_PROVIDER` 환경변수, CLI 실행 시 대화형 선택)로
Anthropic/Gemini 중 고른다. 각 provider 모듈이 자체적으로 키를 환경변수에서 읽으며, 이 저장소는 키를
하드코딩하지 않는다.

- Anthropic: `ANTHROPIC_API_KEY` (또는 `ant auth login` 프로필) — 발급 https://console.anthropic.com/settings/keys
- Gemini: `GEMINI_API_KEY` 또는 `GOOGLE_API_KEY` — 발급 https://aistudio.google.com/apikey
  (모델 ID는 `GEMINI_MODEL`로 재정의 가능, 기본값 `gemini-3.1-pro-preview`)

키/프로바이더 선택 예시는 `.env.example` 참고 (플레이스홀더만 있음, 실제 값은 `.env`에). **주의**: `generate_review()`
호출은 실제 과금이 발생한다.

## 브라우저 채팅 UI

```bash
python -m uvicorn server:app --reload --port 8000
```
후 http://127.0.0.1:8000 접속. `/apps/generator`, `/apps/chiller`는 로컬 개발용 정적 서빙(원본 계산 앱을
이 컴퓨터의 경로에서 직접 서빙) — 배포 후에는 GENERATOR_APP_URL/CHILLER_APP_URL로 대체된다.

## 배포 (GitHub → Render / Vercel)

이 백엔드(`데이터센터통합검토시스템`)는 **Render**(장시간 실행 웹서비스)에 배포한다. LLM tool-calling 루프는
응답에 수십 초 걸릴 수 있어 Vercel 서버리스(실행시간 제한)에는 맞지 않는다.

1. 이 폴더를 새 GitHub 레포로 push (`.env`는 `.gitignore`에 있어 자동 제외됨)
2. Render 대시보드 → New → Blueprint → 이 레포 연결 (`render.yaml`이 서비스를 정의함)
3. Render 대시보드에서 `sync: false`로 표시된 값 직접 입력: `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`,
   `GENERATOR_APP_URL`, `CHILLER_APP_URL` (아래 4번에서 배포된 Vercel URL)
4. 계산 앱 3종(`generator-calc`, `냉동기수량계산x`, `structural_estimator`)은 이미 각자 별도 GitHub 레포이므로
   Vercel에 개별 연결해서 배포 — `structural_estimator`는 `vercel.json`이 이미 있어 그대로 가능

`agent/knowledge_base.py`는 `data/knowledge_base/`에 번들된 파일을 쓰므로 별도 설정 없이 그대로 배포된다.
다른 위치를 쓰려면 `KNOWLEDGE_BASE_DIR` 환경변수로 재정의.

## 다음 단계 (미착수)

- `structural_estimator`의 `api/engine/check_calc.py`(하중조합·구조검토)는 아직 이식하지 않음
- 두 provider 모두 아직 실제 배포 환경에서 검증 전
- 카탈로그/계수 데이터를 Supabase로 옮겨 원본 계산 앱과 실시간 동기화하는 것(현재는 engine/*.py에
  포팅된 스냅샷) — 논의는 됐으나 아직 미착수
- 근거 요청 시 화면 스크린샷을 직접 캡처해 LLM에 첨부하는 기능(Playwright) — 아직 미착수, 링크 제공까지만 구현됨
- `구조_이력_검증`: engine/를 원본과 별도 복사본으로 유지 중 — 원본(`structural_estimator`) 수정 시 수동 동기화 필요
