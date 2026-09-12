# engine/generator_calc.py
# 발전기실 흡배기(그릴·소음기·댐퍼) 개구 면적 산정 모듈
# 원본: D:\DATA\앱개발\generator-calc\app.jsx 의 MANUFACTURERS 카탈로그 + compute() 로직을 Python으로 포팅
# 출처: GnCenergy 카탈로그(Cummins p.13, Caterpillar p.14, MTU p.18) + GnC에너지 공문(2026-05) 확정값

MANUFACTURERS = {
    "cummins": {
        "name": "Cummins", "vref_i": 7.0, "vref_e": 8.0,
        "models": [
            {"kw": 800,  "model": "C800D6 / QSK23-G3",     "qcool": 888,  "qcomb": 67.9,  "cat_oa": 2.3, "cat_ea": 1.9},
            {"kw": 1000, "model": "C1000D6B / KTA38-G14",  "qcool": 981,  "qcomb": 86.1,  "cat_oa": 2.5, "cat_ea": 2.0},
            {"kw": 1250, "model": "C1250D6 / KTA50-G3",    "qcool": 1518, "qcomb": 110.4, "cat_oa": 3.9, "cat_ea": 3.2},
            {"kw": 1500, "model": "C1500D6 / KTA50-G9",    "qcool": 1362, "qcomb": 125,   "cat_oa": 3.5, "cat_ea": 2.8},
            {"kw": 2000, "model": "C2000D6 / QSK60-G6",    "qcool": 1998, "qcomb": 174,   "cat_oa": 5.2, "cat_ea": 4.2},
            {"kw": 2250, "model": "C2250D6A / QSK60-G9",   "qcool": 2040, "qcomb": 183,   "cat_oa": 5.3, "cat_ea": 4.3},
            {"kw": 2500, "model": "DQKAN / QSK60-G19",     "qcool": 2649, "qcomb": 193,   "cat_oa": 6.8, "cat_ea": 5.5},
            {"kw": 2750, "model": "DQLD / QSK78-G8",       "qcool": 3060, "qcomb": 236,   "cat_oa": 6.9, "cat_ea": 6.4},
            {"kw": 3000, "model": "C3000D6EB / QSK78-G37", "qcool": 2751, "qcomb": 262,   "cat_oa": 7.2, "cat_ea": 5.7, "is_default": True},
            {"kw": 3250, "model": "C3250D6 / QSK95-G2",    "qcool": 3135, "qcomb": 279,   "cat_oa": 8.1, "cat_ea": 6.5},
            {"kw": 3500, "model": "C3500D6 / QSK95-G2",    "qcool": 3135, "qcomb": 284,   "cat_oa": 8.1, "cat_ea": 6.5},
        ],
    },
    "cat": {
        "name": "Caterpillar", "vref_i": 8.0, "vref_e": 8.0,
        "models": [
            {"kw": 800,  "model": "3412C",   "qcool": 923,  "qcomb": 70,  "cat_oa": 2.1, "cat_ea": 1.9},
            {"kw": 1000, "model": "C32",     "qcool": 1175, "qcomb": 83,  "cat_oa": 2.6, "cat_ea": 2.4},
            {"kw": 1250, "model": "3512",    "qcool": 1397, "qcomb": 106, "cat_oa": 3.1, "cat_ea": 2.9},
            {"kw": 1500, "model": "3512B",   "qcool": 1611, "qcomb": 126, "cat_oa": 3.6, "cat_ea": 3.4},
            {"kw": 1750, "model": "3516",    "qcool": 1611, "qcomb": 159, "cat_oa": 3.7, "cat_ea": 2.8},
            {"kw": 2000, "model": "3516B",   "qcool": 1674, "qcomb": 164, "cat_oa": 3.8, "cat_ea": 3.5},
            {"kw": 2500, "model": "3516C",   "qcool": 2356, "qcomb": 202, "cat_oa": 5.3, "cat_ea": 4.9},
            {"kw": 2750, "model": "3516E",   "qcool": 2688, "qcomb": 229, "cat_oa": 6.1, "cat_ea": 5.6},
            {"kw": 3000, "model": "C175-16", "qcool": 2933, "qcomb": 264, "cat_oa": 6.7, "cat_ea": 6.1, "is_default": True},
            {"kw": 3250, "model": "C175-16", "qcool": 3296, "qcomb": 271, "cat_oa": 7.4, "cat_ea": 6.9},
            {"kw": 3500, "model": "C175-20", "qcool": 3426, "qcomb": 312, "cat_oa": 7.8, "cat_ea": 7.1},
            {"kw": 3900, "model": "C175-20", "qcool": 3426, "qcomb": 339, "cat_oa": 7.8, "cat_ea": 7.1},
        ],
    },
    "mtu": {
        "name": "MTU", "vref_i": 7.0, "vref_e": 8.0,
        "models": [
            {"kw": 800,  "model": "12V2000G45",  "qcool": 1080, "qcomb": 66,  "cat_oa": 2.7,  "cat_ea": 2.3},
            {"kw": 900,  "model": "16V2000G45",  "qcool": 1476, "qcomb": 84,  "cat_oa": 3.7,  "cat_ea": 3.1},
            {"kw": 1000, "model": "16V2000G85",  "qcool": 1476, "qcomb": 87,  "cat_oa": 3.7,  "cat_ea": 3.1},
            {"kw": 1250, "model": "16V2000G86S", "qcool": 1709, "qcomb": 108, "cat_oa": 3.8,  "cat_ea": 3.1},
            {"kw": 1600, "model": "12V4000G74S", "qcool": 1598, "qcomb": 138, "cat_oa": 4.1,  "cat_ea": 3.3},
            {"kw": 1750, "model": "12V4000G84S", "qcool": 1850, "qcomb": 144, "cat_oa": 4.7,  "cat_ea": 3.9},
            {"kw": 2100, "model": "16V4000G74S", "qcool": 2141, "qcomb": 186, "cat_oa": 5.5,  "cat_ea": 4.5},
            {"kw": 2300, "model": "16V4000G84S", "qcool": 2522, "qcomb": 192, "cat_oa": 6.5,  "cat_ea": 5.3},
            {"kw": 2500, "model": "20V4000G64S", "qcool": 2591, "qcomb": 228, "cat_oa": 6.7,  "cat_ea": 5.4},
            {"kw": 2750, "model": "20V4000G74S", "qcool": 3643, "qcomb": 246, "cat_oa": 9.3,  "cat_ea": 7.6, "is_default": True},
            {"kw": 3250, "model": "20V4000G94S", "qcool": 4079, "qcomb": 270, "cat_oa": 10.4, "cat_ea": 8.5},
        ],
    },
    "rehlko": {
        "name": "Rehlko (Kohler)", "vref_i": 7.0, "vref_e": 8.0,
        "models": [
            {"kw": 3000, "model": "KD3000UE", "qcool": 3570, "qcomb": 266, "cat_oa": 9.13, "cat_ea": 7.44, "is_default": True},
        ],
    },
}

# 확정 기준값 (GnC에너지 공문 2026-05 + Cummins C3000D6EB 사양서)
DEFAULT_PARAMS = {
    "i_da_eta": 100, "i_sil_eta": 50, "i_dmp_eta": 85,   # 급기 개구율(%): DA/소음기/댐퍼
    "e_sil_eta": 39, "e_dmp_eta": 85, "e_grl_eta": 50, "e_da_eta": 100,  # 배기 개구율(%)
    "v_i_da": 7.0, "v_i_sil": 6.0, "v_i_dmp": 5.0,   # 급기 설계풍속(m/s)
    "v_e_sil": 8.0, "v_e_dmp": 6.0, "v_e_grl": 5.5, "v_e_da": 8.0,  # 배기 설계풍속(m/s)
    "sf": 1.2, "n_i": 8, "n_e": 8,
}

# 절대 풍속 한계 (물리적 제약 — 초과 시 경고)
ABS_VELOCITY_LIMITS = {
    "i_da": 8.0, "i_sil": 8.0, "i_dmp": 8.0,
    "e_sil": 8.0, "e_dmp": 8.0, "e_grl": 6.0, "e_da": 8.0,
}


def find_model(manufacturer: str, kw: float = None) -> dict:
    """제조사+kW로 카탈로그 모델을 찾는다. kW 미지정/미일치 시 기본(is_default) 모델을 반환."""
    mfg = MANUFACTURERS.get(manufacturer)
    if not mfg or not mfg["models"]:
        return None
    if kw is not None:
        match = next((m for m in mfg["models"] if m["kw"] == kw), None)
        if match:
            return match
    return next((m for m in mfg["models"] if m.get("is_default")), mfg["models"][0])


def _safe(v):
    return v if v > 0 else 0.01


def compute_generator_room(
    manufacturer: str = "cummins",
    kw: float = None,
    n_i: int = None,
    n_e: int = None,
    sf: float = None,
    overrides: dict = None,
) -> dict:
    """
    발전기실 흡배기(그릴·소음기·댐퍼) 소요 개구 면적을 산정한다.

    manufacturer: 'cummins' | 'cat' | 'mtu' | 'rehlko'
    kw: Stand-by Power(kW). 미지정 시 제조사 기본 모델(is_default) 사용
    n_i / n_e: 급기/배기 대수. 미지정 시 기본 8대
    sf: 여유율 배수. 미지정 시 기본 1.2
    overrides: 개구율(η, %)·설계풍속(m/s) 등 세부 파라미터 재정의
               키: i_da_eta, i_sil_eta, i_dmp_eta, e_sil_eta, e_dmp_eta, e_grl_eta, e_da_eta,
                   v_i_da, v_i_sil, v_i_dmp, v_e_sil, v_e_dmp, v_e_grl, v_e_da

    핵심 공식: 1대 gross 면적 = Q_unit(㎥/s) × sf ÷ (설계풍속 × 개구율)
    """
    mfg = MANUFACTURERS.get(manufacturer)
    if not mfg:
        raise ValueError(f"알 수 없는 제조사: {manufacturer}")
    model = find_model(manufacturer, kw)
    if not model:
        raise ValueError(f"{manufacturer} 카탈로그에 등록된 모델이 없습니다")

    d = dict(DEFAULT_PARAMS)
    d.update({
        "vref_i": mfg["vref_i"], "vref_e": mfg["vref_e"],
        "oa": model["cat_oa"], "ea": model["cat_ea"],
        "qcomb": model["qcomb"], "qcool": model["qcool"],
    })
    if n_i is not None:
        d["n_i"] = n_i
    if n_e is not None:
        d["n_e"] = n_e
    if sf is not None:
        d["sf"] = sf
    if overrides:
        d.update(overrides)

    Vref_i, Vref_e = d["vref_i"], d["vref_e"]
    oa, ea = d["oa"], d["ea"]
    # Q역산값 (카탈로그 OA/EA 검산용)
    oa_q = round((d["qcomb"] + d["qcool"]) / 60 / Vref_i, 2)
    ea_q = round(d["qcool"] / 60 / Vref_e, 2)
    # 단위 유량 [㎥/s per 대]
    qi, qe = oa * Vref_i, ea * Vref_e
    OA_total = round(oa * d["n_i"] * d["sf"], 2)
    EA_total = round(ea * d["n_e"] * d["sf"], 2)

    gi = {
        "da":  round(qi * d["sf"] / (_safe(d["v_i_da"])  * (d["i_da_eta"]  / 100)), 2),
        "sil": round(qi * d["sf"] / (_safe(d["v_i_sil"]) * (d["i_sil_eta"] / 100)), 2),
        "dmp": round(qi * d["sf"] / (_safe(d["v_i_dmp"]) * (d["i_dmp_eta"] / 100)), 2),
    }
    ge = {
        "sil": round(qe * d["sf"] / (_safe(d["v_e_sil"]) * (d["e_sil_eta"] / 100)), 2),
        "dmp": round(qe * d["sf"] / (_safe(d["v_e_dmp"]) * (d["e_dmp_eta"] / 100)), 2),
        "grl": round(qe * d["sf"] / (_safe(d["v_e_grl"]) * (d["e_grl_eta"] / 100)), 2),
        "da":  round(qe * d["sf"] / (_safe(d["v_e_da"])  * (d["e_da_eta"]  / 100)), 2),
    }
    ig = {k: round(v * d["n_i"], 2) for k, v in gi.items()}
    eg = {k: round(v * d["n_e"], 2) for k, v in ge.items()}

    warns = {
        "i_da":  d["v_i_da"]  > ABS_VELOCITY_LIMITS["i_da"],
        "i_sil": d["v_i_sil"] > ABS_VELOCITY_LIMITS["i_sil"],
        "i_dmp": d["v_i_dmp"] > ABS_VELOCITY_LIMITS["i_dmp"],
        "e_sil": d["v_e_sil"] > ABS_VELOCITY_LIMITS["e_sil"],
        "e_dmp": d["v_e_dmp"] > ABS_VELOCITY_LIMITS["e_dmp"],
        "e_grl": d["v_e_grl"] > ABS_VELOCITY_LIMITS["e_grl"],
        "e_da":  d["v_e_da"]  > ABS_VELOCITY_LIMITS["e_da"],
    }

    return {
        "manufacturer": mfg["name"], "model": model["model"], "kw": model["kw"],
        "n_i": d["n_i"], "n_e": d["n_e"], "sf": d["sf"],
        "catalog": {"oa_m2": oa, "ea_m2": ea, "qcomb_m3min": model["qcomb"], "qcool_m3min": model["qcool"]},
        "oa_calc_from_Q_m2": oa_q, "ea_calc_from_Q_m2": ea_q,
        "OA_total_m2": OA_total, "EA_total_m2": EA_total,
        "per_unit_gross_m2": {"intake": gi, "exhaust": ge},
        "total_gross_m2": {"intake": ig, "exhaust": eg},
        "velocity_warnings": {k: v for k, v in warns.items() if v},
        "basis": "GnCenergy 카탈로그 + GnC에너지 공문(2026-05) 확정값. gross = Q×sf/(V×η)",
    }
