# tools/structural_tools.py
# structural_estimator(D:\DATA\앱개발\structural_estimator)의 구조 산정 엔진을 LangChain @tool로 래핑
# 엔진 로직 자체는 engine/*.py 에 그대로 복사되어 있으며, 여기서는 호출 인터페이스만 정의한다.

from typing import Optional
from langchain_core.tools import tool

from engine.beam_calc import estimate_beam_depth, estimate_slab_thickness
from engine.column_calc import (
    calculate_axial_load, estimate_rc_column, estimate_src_column, recommend_column_type,
)
from engine.foundation_calc import estimate_footing, estimate_retaining_wall


@tool
def calc_beam_depth(
    span_m: float,
    material: str = "RC",
    support_condition: str = "both_ends_cont",
    wu_kpa: Optional[float] = None,
    trib_width_m: Optional[float] = None,
    fck_mpa: float = 24.0,
    fy_mpa: float = 400.0,
) -> dict:
    """보 춤/폭을 산정한다(KDS 41 30 00 Table 7.3-1 사용성 기준 + RC 강도 기준 중 큰 값 채택).

    material: 'RC' | 'Steel' | 'PT' | 'SRC'
    support_condition: 'simply_supported' | 'one_end_cont' | 'both_ends_cont' | 'cantilever'
    wu_kpa, trib_width_m: RC + 설계하중 정보가 있을 때만 강도기준 계산에 사용
    """
    return estimate_beam_depth(span_m, material, support_condition, wu_kpa, trib_width_m, fck_mpa, fy_mpa)


@tool
def calc_slab_thickness(
    span_m: float,
    material: str = "RC",
    is_two_way: bool = False,
    support_condition: str = "both_ends_cont",
    two_way_type: str = "beam_slab",
) -> dict:
    """슬래브 두께(mm)를 산정한다(KDS 41 30 00 Table 7.3-2 기준).

    material: 'RC' | 'PT'
    two_way_type: 'flat_plate' | 'flat_slab' | 'beam_slab' (is_two_way=True일 때만 사용)
    """
    return estimate_slab_thickness(span_m, material, is_two_way, support_condition, two_way_type)


@tool
def calc_column_axial_load(
    tributary_area_m2: float,
    dead_load_kpa: float,
    live_load_kpa: float,
    floors: int,
    importance_factor: float = 1.0,
) -> float:
    """영향면적법으로 기둥에 작용하는 총 설계 축력(kN)을 계산한다. P = A × (DL+LL) × 층수 × 중요도계수."""
    return calculate_axial_load(tributary_area_m2, dead_load_kpa, live_load_kpa, floors, importance_factor)


@tool
def calc_rc_column_section(axial_load_kn: float, fck_mpa: float = 24.0) -> dict:
    """RC 정사각형 기둥 단면을 1차 가정 산정한다(A_req = P_u / (0.3×fck)). 세장비·편심·P-M 상관관계 미반영."""
    return estimate_rc_column(axial_load_kn, fck_mpa)


@tool
def calc_src_column_section(axial_load_kn: float, fck_mpa: float = 27.0, fy_mpa: float = 355.0) -> dict:
    """SRC(철골철근콘크리트) 기둥 단면 및 내장 H형강 규격을 1차 가정 산정한다."""
    return estimate_src_column(axial_load_kn, fck_mpa, fy_mpa)


@tool
def recommend_column_type(axial_load_kn: float) -> str:
    """축력 크기에 따라 적합한 기둥 공법('RC' 또는 'SRC')을 추천한다. (기준: 5,000kN / 15,000kN)"""
    from engine.column_calc import recommend_column_type as _f
    return _f(axial_load_kn)


@tool
def calc_footing(axial_load_kn: float, column_span_m: float, bearing_capacity_kpa: float = 200.0) -> dict:
    """독립기초/매트기초 여부를 판단하고 규격을 산정한다(A_f = P / q_a)."""
    return estimate_footing(axial_load_kn, column_span_m, bearing_capacity_kpa)


@tool
def calc_retaining_wall(
    basement_depth_m: float,
    soil_gamma_kn_m3: float = 18.0,
    phi_deg: float = 30.0,
    surcharge_kpa: float = 10.0,
    wall_type: str = "basement",
) -> dict:
    """지하층 토압벽체 두께를 산정한다.

    wall_type: 'basement'(지하외벽 구속형, 정지토압 K0 적용, 기본값) | 'retaining'(옹벽 자립형, 능동토압 Ka 적용)
    """
    return estimate_retaining_wall(basement_depth_m, soil_gamma_kn_m3, phi_deg, surcharge_kpa, wall_type)


STRUCTURAL_TOOLS = [
    calc_beam_depth,
    calc_slab_thickness,
    calc_column_axial_load,
    calc_rc_column_section,
    calc_src_column_section,
    recommend_column_type,
    calc_footing,
    calc_retaining_wall,
]
