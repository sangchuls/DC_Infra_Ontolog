# agent/evidence.py
# 에이전트가 실행한 tool 호출을, 그 계산의 원본 앱 화면 링크로 변환한다.
# (검토의견서 텍스트만이 아니라 실제 계산 앱에서 같은 입력값으로 근거를 보여주기 위함)
#
# 로컬 개발: server.py 가 /apps/generator, /apps/chiller 로 원본 앱을 정적 서빙 (기본값).
# 배포 후: GENERATOR_APP_URL / CHILLER_APP_URL 환경변수에 실제 Vercel 배포 URL을 넣으면
#          그쪽을 가리키도록 바뀐다 (예: https://generator-calc.vercel.app).
# 각 앱은 URL 쿼리 파라미터로 초기값을 받도록 수정되어 있다
# (generator-calc/app.jsx, 냉동기수량계산x/script.js 의 loadFromQuery 참고).

import os
from urllib.parse import urlencode

GENERATOR_APP_URL = os.environ.get("GENERATOR_APP_URL", "/apps/generator").rstrip("/")
CHILLER_APP_URL = os.environ.get("CHILLER_APP_URL", "/apps/chiller").rstrip("/")


def build_evidence(tool_calls: list) -> list:
    """tool_calls: [{"tool": str, "input": dict}, ...] -> [{"tool","label","url"}, ...]"""
    evidence = []
    for call in tool_calls:
        name = call.get("tool")
        inp = call.get("input") or {}

        if name == "calc_generator_room_openings":
            q = {}
            if inp.get("manufacturer"):
                q["model"] = inp["manufacturer"]
            for k in ("kw", "n_i", "n_e", "sf"):
                if inp.get(k) is not None:
                    q[k] = inp[k]
            mfg = inp.get("manufacturer", "cummins")
            kw_label = f" ({mfg} {inp['kw']}kW)" if inp.get("kw") is not None else f" ({mfg})"
            evidence.append({
                "tool": name,
                "label": f"발전기 급배기 계산 앱에서 보기{kw_label}",
                "url": f"{GENERATOR_APP_URL}/?" + urlencode(q),
            })

        elif name == "calc_chiller_sizing":
            mode = inp.get("cooling_method", "water")
            q = {"mode": mode}
            if inp.get("it_load_kw") is not None:
                q["it"] = inp["it_load_kw"]
            if inp.get("domestic_water_count") is not None:
                q["count"] = inp["domestic_water_count"]
            if inp.get("domestic_water_usage_l_per_day") is not None:
                q["usage"] = inp["domestic_water_usage_l_per_day"]
            if inp.get("domestic_water_days") is not None:
                q["days"] = inp["domestic_water_days"]
            if inp.get("fire_water_ton") is not None:
                q["fire"] = inp["fire_water_ton"]
            it_label = inp.get("it_load_kw", "?")
            evidence.append({
                "tool": name,
                "label": f"냉동기 계산 앱에서 보기 (IT부하 {it_label}kW, {'수냉식' if mode == 'water' else '공냉식'})",
                "url": f"{CHILLER_APP_URL}/?" + urlencode(q),
            })

    return evidence
