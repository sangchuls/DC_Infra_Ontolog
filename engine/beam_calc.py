# engine/beam_calc.py
# 수평 부재 (보 & 슬래브) 규격 산정 모듈

import math

BEAM_DEPTH_RATIOS = {
    "RC": {
        "simply_supported": {"ratio": 16,   "basis": "KDS 41 30 00 Table 7.3-1 단순지지"},
        "one_end_cont":     {"ratio": 18.5, "basis": "KDS 41 30 00 Table 7.3-1 일단연속"},
        "both_ends_cont":   {"ratio": 21,   "basis": "KDS 41 30 00 Table 7.3-1 양단연속"},
        "cantilever":       {"ratio": 8,    "basis": "KDS 41 30 00 Table 7.3-1 캔틸레버"},
        "width_ratio": 0.5,
        "label": "RC 보",
        "note": "KDS 41 30 00 Table 7.3-1 처짐 검토 생략 최소두께 (fy=400MPa 기준)",
    },
    "Steel": {
        "simply_supported": {"ratio": 20,   "basis": "실무 경험치 (Steel L/20~L/24 범위)"},
        "one_end_cont":     {"ratio": 22,   "basis": "실무 경험치 (Steel L/20~L/24 범위)"},
        "both_ends_cont":   {"ratio": 24,   "basis": "실무 경험치 (Steel L/20~L/24 범위)"},
        "cantilever":       {"ratio": 10,   "basis": "실무 경험치"},
        "width_ratio": 0.4,
        "label": "철골 보",
        "note": "KDS 직접 비율식 없음 — 실무 경험치 (L/20~L/24). 처짐은 별도 검토 필요",
    },
    "PT": {
        "simply_supported": {"ratio": 30,   "basis": "실무 경험치 (PT L/30~L/45 범위)"},
        "one_end_cont":     {"ratio": 37,   "basis": "실무 경험치 (PT L/30~L/45 범위)"},
        "both_ends_cont":   {"ratio": 45,   "basis": "실무 경험치 (PT L/30~L/45 범위)"},
        "cantilever":       {"ratio": 15,   "basis": "실무 경험치"},
        "width_ratio": 0.4,
        "label": "PT 보",
        "note": "KDS 직접 비율식 없음 — 실무 경험치 (L/30~L/45). 긴장력·장기처짐 별도 검토 필요",
    },
    "SRC": {
        "simply_supported": {"ratio": 18,   "basis": "실무 경험치 (SRC L/18~L/22 범위)"},
        "one_end_cont":     {"ratio": 20,   "basis": "실무 경험치 (SRC L/18~L/22 범위)"},
        "both_ends_cont":   {"ratio": 22,   "basis": "실무 경험치 (SRC L/18~L/22 범위)"},
        "cantilever":       {"ratio": 9,    "basis": "실무 경험치"},
        "width_ratio": 0.45,
        "label": "SRC 보",
        "note": "KDS 직접 비율식 없음 — 실무 경험치 (L/18~L/22). 합성단면 내력 별도 검토 필요",
    },
}

SUPPORT_CONDITION_LABELS = {
    "simply_supported": "단순지지",
    "one_end_cont":     "일단연속",
    "both_ends_cont":   "양단연속",
    "cantilever":       "캔틸레버",
}


def _rc_depth_for_strength(span_m, wu_kpa, trib_width_m, fck_mpa=24.0, fy_mpa=400.0):
    """RC 보 강도 기준 최소 춤 역산. b=d/2, rho=0.35*rho_b 가정."""
    wu_line = wu_kpa * trib_width_m
    Mu_kNm  = wu_line * span_m**2 / 8.0 * 0.8
    if Mu_kNm <= 0.0:
        return None
    b1    = max(0.65, 0.85 - 0.007 * max(0.0, fck_mpa - 28.0))
    rho_b = 0.85 * b1 * fck_mpa / fy_mpa * 600.0 / (600.0 + fy_mpa)
    rho   = 0.35 * rho_b
    alpha     = rho * fy_mpa / (1.7 * fck_mpa)
    coeff_Nmm = 0.85 * rho * 0.5 * fy_mpa * (1.0 - alpha / 2.0)
    if coeff_Nmm <= 0.0:
        return None
    d = (Mu_kNm * 1.0e6 / coeff_Nmm) ** (1.0 / 3.0)
    h = d + 70.0
    return {
        "depth_mm": (int(h) // 50 + 1) * 50,
        "Mu_kNm":   round(Mu_kNm, 1),
        "wu_kN_m":  round(wu_line, 2),
        "rho_pct":  round(rho * 100, 3),
    }


def estimate_beam_depth(span_m, material="RC", support_condition="both_ends_cont",
                        wu_kpa=None, trib_width_m=None, fck_mpa=24.0, fy_mpa=400.0):
    """
    보 춤/폭 산정.
    사용성 기준(KDS 41 30 00 Table 7.3-1)과 강도 기준(Mu 역산) 중 큰 값 채택.
    강도 기준은 RC + 하중 정보 제공 시에만 계산.
    """
    span_mm = span_m * 1000
    cfg  = BEAM_DEPTH_RATIOS.get(material, BEAM_DEPTH_RATIOS["RC"])
    cond = cfg.get(support_condition, cfg["both_ends_cont"])
    ratio        = cond["ratio"]
    depth_mm_svc = (int(span_mm / ratio) // 50 + 1) * 50

    depth_mm_str = None
    str_info     = None
    if material.upper() == "RC" and wu_kpa and trib_width_m:
        str_info = _rc_depth_for_strength(span_m, wu_kpa, trib_width_m, fck_mpa, fy_mpa)
        if str_info:
            depth_mm_str = str_info["depth_mm"]

    if depth_mm_str and depth_mm_str > depth_mm_svc:
        depth_mm, governs_by = depth_mm_str, "strength"
    else:
        depth_mm, governs_by = depth_mm_svc, "serviceability"

    width_mm = (int(depth_mm * cfg["width_ratio"]) // 50 + 1) * 50

    result = {
        "material":                material,
        "label":                   cfg["label"],
        "span_m":                  span_m,
        "depth_mm":                depth_mm,
        "width_mm":                width_mm,
        "depth_mm_serviceability": depth_mm_svc,
        "depth_mm_strength":       depth_mm_str,
        "governs_by":              governs_by,
        "ratio_used":              ratio,
        "support_condition":       support_condition,
        "support_label":           SUPPORT_CONDITION_LABELS.get(support_condition, support_condition),
        "basis":                   cond["basis"],
        "note":                    cfg["note"],
    }
    if str_info:
        result["strength_Mu_kNm"] = str_info["Mu_kNm"]
        result["strength_wu_kNm"] = str_info["wu_kN_m"]
    return result


SLAB_THICKNESS_RATIOS = {
    "RC": {
        "one_way": {
            "simply_supported": {"ratio": 20,  "basis": "KDS 41 30 00 Table 7.3-2 단순지지"},
            "one_end_cont":     {"ratio": 24,  "basis": "KDS 41 30 00 Table 7.3-2 일단연속"},
            "both_ends_cont":   {"ratio": 28,  "basis": "KDS 41 30 00 Table 7.3-2 양단연속"},
            "cantilever":       {"ratio": 10,  "basis": "KDS 41 30 00 Table 7.3-2 캔틸레버"},
        },
        "two_way": {
            "flat_plate":  {"ratio": 33, "basis": "플랫플레이트 근사 ln/33 (αf=0 기준)"},
            "flat_slab":   {"ratio": 36, "basis": "플랫슬래브(드롭패널) 근사 ln/36"},
            "beam_slab":   {"ratio": 30, "basis": "보-슬래브 2방향 참고 근사치 (αf≥2)"},
        },
        "min_mm": 100,
        "note": "KDS 41 30 00 Table 7.3-2. 2방향 슬래브는 순경간·보 강성비(αf) 별도 검토 필요",
    },
    "PT": {
        "one_way": {
            "simply_supported": {"ratio": 35, "basis": "실무 경험치 PT 1방향 (L/30~L/40)"},
            "one_end_cont":     {"ratio": 40, "basis": "실무 경험치 PT 1방향"},
            "both_ends_cont":   {"ratio": 45, "basis": "실무 경험치 PT 1방향"},
            "cantilever":       {"ratio": 15, "basis": "실무 경험치 PT 캔틸레버"},
        },
        "two_way": {
            "flat_plate":  {"ratio": 45, "basis": "실무 경험치 PT 2방향 플랫플레이트"},
            "flat_slab":   {"ratio": 50, "basis": "실무 경험치 PT 2방향 플랫슬래브"},
            "beam_slab":   {"ratio": 40, "basis": "실무 경험치 PT 2방향 보-슬래브"},
        },
        "min_mm": 100,
        "note": "KDS 직접 비율식 없음 — 실무 경험치. 장기처짐·긴장력 손실 별도 검토 필요",
    },
}


def estimate_slab_thickness(span_m, material="RC", is_two_way=False,
                            support_condition="both_ends_cont", two_way_type="beam_slab"):
    """슬래브 두께(mm) 추정."""
    span_mm = span_m * 1000
    cfg  = SLAB_THICKNESS_RATIOS.get(material, SLAB_THICKNESS_RATIOS["RC"])
    if is_two_way:
        tw    = cfg["two_way"].get(two_way_type, cfg["two_way"]["beam_slab"])
        ratio = tw["ratio"]; basis = tw["basis"]
        slab_type = f"2방향 슬래브 ({two_way_type})"
    else:
        ow    = cfg["one_way"].get(support_condition, cfg["one_way"]["both_ends_cont"])
        ratio = ow["ratio"]; basis = ow["basis"]
        slab_type = "1방향 슬래브 ({})".format(
            SUPPORT_CONDITION_LABELS.get(support_condition, support_condition))

    thickness_mm = max(cfg["min_mm"], (int(span_mm / ratio) // 10 + 1) * 10)
    return {
        "slab_type":         slab_type,
        "material":          material,
        "span_m":            span_m,
        "thickness_mm":      thickness_mm,
        "ratio_used":        ratio,
        "basis":             basis,
        "note":              cfg["note"],
        "is_two_way":        is_two_way,
        "support_condition": support_condition if not is_two_way else two_way_type,
    }
