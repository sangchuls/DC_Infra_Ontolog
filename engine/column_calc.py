# engine/column_calc.py
# 수직 부재 (기둥) 규격 산정 모듈

import math


def calculate_axial_load(
    tributary_area: float,
    dead_load: float,
    live_load: float,
    floors: int,
    importance_factor: float = 1.0,
) -> float:
    """
    영향면적법으로 기둥에 작용하는 총 설계 축력(kN)을 계산합니다.
    P = A × (DL + LL) × n × I
    """
    load_per_floor = tributary_area * (dead_load + live_load)
    total_load = load_per_floor * floors * importance_factor
    return round(total_load, 2)


_COLUMN_DISCLAIMER = (
    "⚠ 1차 가정단면 (개략 산정). "
    "철근 기여분·세장비(좌굴)·편심 및 2축 휨은 미반영. "
    "실제 배근검토 시 축력-모멘트 상관관계(P-M Interaction) 별도 필요."
)


def estimate_rc_column(axial_load_kn: float, fck_mpa: float = 24) -> dict:
    """
    RC 기둥 정사각형 단면 추정.
    간략식: A_req = P_u / (0.3 × fck)
    ※ 순콘크리트 기여분만 고려한 1차 가정 — 철근비 ρ=0 가정, 세장비·편심 미반영
    """
    axial_load_n = axial_load_kn * 1000
    req_area_mm2 = axial_load_n / (0.3 * fck_mpa)
    side_mm = math.sqrt(req_area_mm2)
    practical_side = (int(side_mm) // 100 + 1) * 100

    return {
        "type": "RC",
        "label": "RC 기둥",
        "fck_mpa": fck_mpa,
        "axial_load_kn": axial_load_kn,
        "req_area_mm2": round(req_area_mm2, 0),
        "size_mm": practical_side,
        "section": f"{practical_side} × {practical_side}",
        "basis": "P_u / (0.3 × fck) — 영향면적법 1차 가정단면",
        "disclaimer": _COLUMN_DISCLAIMER,
    }


def estimate_src_column(axial_load_kn: float, fck_mpa: float = 27, fy_mpa: float = 355) -> dict:
    """
    SRC(Steel Reinforced Concrete) 기둥 단면 추정.
    강재 단면이 전체 단면의 약 4~6% 부담 가정.
    """
    axial_load_n = axial_load_kn * 1000
    # 콘크리트 + 강재 합성 효과로 RC 대비 약 25% 단면 절감
    req_area_mm2 = axial_load_n / (0.38 * fck_mpa)
    side_mm = math.sqrt(req_area_mm2)
    practical_side = (int(side_mm) // 100 + 1) * 100

    # 적정 내장 H형강 규격 추정 (단면의 약 5%)
    steel_area_mm2 = req_area_mm2 * 0.05
    h_side = math.sqrt(steel_area_mm2 / 1.2)
    h_size = (int(h_side) // 50 + 1) * 50

    return {
        "type": "SRC",
        "label": "SRC 기둥",
        "fck_mpa": fck_mpa,
        "axial_load_kn": axial_load_kn,
        "size_mm": practical_side,
        "section": f"{practical_side} × {practical_side}",
        "h_beam": f"H-{h_size}×{h_size} (내장 H형강 예상)",
        "basis": "합성단면 P_u / (0.38 × fck) 1차 가정단면 (RC 대비 약 25% 절감 가정)",
        "disclaimer": _COLUMN_DISCLAIMER,
    }


def recommend_column_type(axial_load_kn: float) -> str:
    """
    축력 크기에 따라 최적 기둥 공법을 추천합니다.
    """
    if axial_load_kn < 5000:
        return "RC"
    elif axial_load_kn < 15000:
        return "SRC"
    else:
        return "SRC"  # 초고하중은 SRC 또는 CFT 검토 권장
