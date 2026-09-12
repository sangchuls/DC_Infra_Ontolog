# data/kds_loads.py
# KDS(국가건설기준) 기반 하중 데이터베이스

# 용도별 기본 활하중 (단위: kN/m²)
LIVE_LOADS = {
    "residential":   {"label": "주거시설",       "value": 2.0},
    "office":        {"label": "일반 업무시설",   "value": 2.5},
    "commercial":    {"label": "상업/판매시설",   "value": 5.0},
    "hospital":      {"label": "병원",           "value": 3.0},
    "school":        {"label": "학교",           "value": 3.0},
    "parking":       {"label": "주차장",         "value": 4.0},
    "warehouse":     {"label": "창고/물류",      "value": 7.5},
    "data_center":   {"label": "데이터센터",     "value": 12.0},
    "plant_room":    {"label": "기계실/플랜트룸", "value": 7.5},
    "rooftop_mep":   {"label": "옥상 기계설비층","value": 10.0},
}

# 공법별 기본 고정하중 (단위: kN/m², 마감재 포함 개략치)
DEAD_LOADS = {
    "RC":    {"label": "철근콘크리트 (RC)",          "value": 6.0},
    "Steel": {"label": "철골 (Steel)",              "value": 4.0},
    "SRC":   {"label": "철골철근콘크리트 (SRC)",     "value": 7.0},
    "PT":    {"label": "포스트텐션 (PT)",            "value": 5.5},
}

# 건물 중요도계수 (KDS 41 17 00(2022) 표 2.2-1 기준)
# 특=1.5, 1=1.2, 2·3=1.0
# ※ 구버전(특=1.2, 1=1.0, 2=0.9)과 혼동 주의 — 현행 기준은 아래와 같이 상향됨
IMPORTANCE_FACTORS = {
    "특": {"label": "특등급 (병원·소방서·발전소 등 필수시설)",         "value": 1.5},
    "1":  {"label": "1등급 (일반 오피스·학교·숙박시설 등)",            "value": 1.2},
    "2":  {"label": "2등급 (소규모 주거·창고 등)",                    "value": 1.0},
    "3":  {"label": "3등급 (농업용 창고·가설구조물 등 임시시설)",       "value": 1.0},
}

# 지반 종류별 허용 지내력 (단위: kN/m²)
BEARING_CAPACITY = {
    "암반":    {"label": "암반 (Hard Rock)",        "value": 2000.0},
    "조밀모래": {"label": "조밀한 모래·자갈",        "value": 400.0},
    "중간모래": {"label": "중간 밀도 모래",          "value": 200.0},
    "연약점토": {"label": "연약 점토",              "value": 100.0},
    "느슨모래": {"label": "느슨한 모래",            "value": 80.0},
}

# 흙의 단위중량 및 내부마찰각 (옹벽 토압 계산용)
SOIL_PROPERTIES = {
    "일반사질토": {"label": "일반 사질토",     "gamma": 18.0, "phi": 30},
    "조밀자갈":   {"label": "조밀한 자갈",    "gamma": 20.0, "phi": 35},
    "연약점토":   {"label": "연약 점토",      "gamma": 16.0, "phi": 15},
    "매립토":     {"label": "매립토 (혼합)",  "gamma": 17.0, "phi": 25},
}
