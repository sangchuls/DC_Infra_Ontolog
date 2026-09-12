# agent/tools_common.py
# 프로바이더 비의존 tool 함수 (일반 Python 함수 + Google-style docstring).
# Anthropic(@beta_tool)과 Gemini(자동 함수호출 — 일반 함수를 그대로 tools=[...]에 전달)가 이 정의를 공유한다.
#
# 반환값은 항상 JSON 문자열(str)이다. Anthropic @beta_tool은 함수가 str 또는 이미 형식을 갖춘
# content 블록 목록(각 항목에 "type" 키)만 반환하도록 기대하는데(BetaFunctionToolResultType =
# Union[str, Iterable[BetaContent]]), 일반 dict/list를 그대로 반환하면 "type 필드 없는 content 블록"으로
# 오인되어 400 에러(messages.N.content.0.tool_result.content.0.type: Field required)가 난다.
# Gemini 자동 함수호출 예제도 문자열 반환을 기본으로 하므로, JSON 문자열 반환이 두 프로바이더 모두에 안전하다.

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Optional

from engine.beam_calc import estimate_beam_depth, estimate_slab_thickness
from engine.column_calc import (
    calculate_axial_load, estimate_rc_column, estimate_src_column, recommend_column_type as _recommend_column_type,
)
from engine.foundation_calc import estimate_footing, estimate_retaining_wall
from engine.generator_calc import compute_generator_room
from engine.chiller_calc import compute_shared_water, compute_water_chiller, compute_air_chiller
from agent.knowledge_base import list_projects as _list_projects, load_project as _load_project


def _json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, default=str)


# ── 지식베이스 ────────────────────────────────────────────────────
def list_projects() -> str:
    """등록된 프로젝트 온톨로지 목록을 조회한다. (가평DC, SK울산, 당진GS, 동탄삼성SDS, 문봉신영 등)"""
    return _json(_list_projects())


def load_project(name: str) -> str:
    """지정한 프로젝트의 온톨로지(구조화 사실)와 설명 문서를 불러온다.

    Args:
        name: list_projects로 확인한 프로젝트명 (예: "가평DC_수전용량검토", "SK울산")
    """
    return _json(_load_project(name))


# ── 구조 ──────────────────────────────────────────────────────────
def calc_beam_depth(
    span_m: float, material: str = "RC", support_condition: str = "both_ends_cont",
    wu_kpa: Optional[float] = None, trib_width_m: Optional[float] = None,
    fck_mpa: float = 24.0, fy_mpa: float = 400.0,
) -> str:
    """보 춤/폭을 산정한다 (KDS 41 30 00 Table 7.3-1 사용성 기준 + RC 강도 기준 중 큰 값).

    Args:
        span_m: 스팬 길이(m)
        material: 'RC' | 'Steel' | 'PT' | 'SRC'
        support_condition: 'simply_supported' | 'one_end_cont' | 'both_ends_cont' | 'cantilever'
        wu_kpa: 설계하중강도(kPa). RC + 하중정보가 있을 때만 강도기준 계산
        trib_width_m: 부하폭(m)
        fck_mpa: 콘크리트 압축강도(MPa)
        fy_mpa: 철근 항복강도(MPa)
    """
    return _json(estimate_beam_depth(span_m, material, support_condition, wu_kpa, trib_width_m, fck_mpa, fy_mpa))


def calc_slab_thickness(
    span_m: float, material: str = "RC", is_two_way: bool = False,
    support_condition: str = "both_ends_cont", two_way_type: str = "beam_slab",
) -> str:
    """슬래브 두께(mm)를 산정한다 (KDS 41 30 00 Table 7.3-2).

    Args:
        span_m: 스팬 길이(m)
        material: 'RC' | 'PT'
        is_two_way: 2방향 슬래브 여부
        support_condition: 1방향일 때 지지조건
        two_way_type: 2방향일 때 'flat_plate' | 'flat_slab' | 'beam_slab'
    """
    return _json(estimate_slab_thickness(span_m, material, is_two_way, support_condition, two_way_type))


def calc_column_and_footing(
    tributary_area_m2: float, dead_load_kpa: float, live_load_kpa: float, floors: int,
    importance_factor: float = 1.0, fck_mpa: float = 27.0, column_span_m: Optional[float] = None,
    bearing_capacity_kpa: float = 200.0,
) -> str:
    """기둥 축력·단면(RC/SRC 비교)과 기초 규격을 한번에 산정한다.

    Args:
        tributary_area_m2: 기둥 부하면적(m²), 보통 스팬x*스팬y
        dead_load_kpa: 고정하중(kPa)
        live_load_kpa: 활하중(kPa)
        floors: 층수
        importance_factor: 중요도계수
        fck_mpa: 콘크리트 압축강도(MPa)
        column_span_m: 기초 산정용 기둥 간격(m). 미지정시 tributary_area의 제곱근 사용
        bearing_capacity_kpa: 지반 허용 지내력(kPa)
    """
    axial = calculate_axial_load(tributary_area_m2, dead_load_kpa, live_load_kpa, floors, importance_factor)
    span = column_span_m if column_span_m is not None else tributary_area_m2 ** 0.5
    return _json({
        "axial_load_kn": axial,
        "recommended_type": _recommend_column_type(axial),
        "rc_column": estimate_rc_column(axial, fck_mpa),
        "src_column": estimate_src_column(axial, fck_mpa),
        "footing": estimate_footing(axial, span, bearing_capacity_kpa),
    })


def calc_retaining_wall(
    basement_depth_m: float, soil_gamma_kn_m3: float = 18.0, phi_deg: float = 30.0,
    surcharge_kpa: float = 10.0, wall_type: str = "basement",
) -> str:
    """지하층 토압벽체 두께를 산정한다.

    Args:
        basement_depth_m: 지하 깊이(m)
        soil_gamma_kn_m3: 흙 단위중량(kN/m³)
        phi_deg: 내부마찰각(도)
        surcharge_kpa: 지표 상재하중(kPa)
        wall_type: 'basement'(지하외벽 구속형, 기본) | 'retaining'(옹벽 자립형)
    """
    return _json(estimate_retaining_wall(basement_depth_m, soil_gamma_kn_m3, phi_deg, surcharge_kpa, wall_type))


# ── 발전기 ────────────────────────────────────────────────────────
def calc_generator_room_openings(
    manufacturer: str = "cummins", kw: Optional[float] = None,
    n_i: Optional[int] = None, n_e: Optional[int] = None, sf: Optional[float] = None,
) -> str:
    """발전기실 급배기(그릴·소음기·댐퍼) 소요 개구면적을 산정한다. 절대풍속 한계 초과시 경고를 포함한다.

    Args:
        manufacturer: 'cummins' | 'cat' | 'mtu' | 'rehlko'
        kw: Stand-by Power(kW). 미지정시 제조사 대표모델 사용
        n_i: 급기 대수 (기본 8)
        n_e: 배기 대수 (기본 8)
        sf: 여유율 배수 (기본 1.2)
    """
    return _json(compute_generator_room(manufacturer=manufacturer, kw=kw, n_i=n_i, n_e=n_e, sf=sf))


# ── 냉동기 ────────────────────────────────────────────────────────
def calc_chiller_sizing(
    it_load_kw: float, cooling_method: str = "water",
    domestic_water_count: Optional[int] = None, domestic_water_usage_l_per_day: Optional[float] = None,
    domestic_water_days: Optional[float] = None, fire_water_ton: Optional[float] = None,
) -> str:
    """IT부하로부터 냉동기 소요대수·저수조 용량을 산정한다 (부가 저수조 포함).

    Args:
        it_load_kw: IT 부하(kW)
        cooling_method: 'water'(수냉식) | 'air'(공냉식)
        domestic_water_count: 상주 인원수(인)
        domestic_water_usage_l_per_day: 1인당 생활용수 사용량(L/인·일)
        domestic_water_days: 저장 일수
        fire_water_ton: 소방용수(TON, 소방 설계기준에 따라 별도 산정된 값)
    """
    shared = compute_shared_water(domestic_water_count, domestic_water_usage_l_per_day, domestic_water_days, fire_water_ton)
    if cooling_method == "air":
        chiller = compute_air_chiller(it_load_kw=it_load_kw, shared=shared)
    else:
        chiller = compute_water_chiller(it_load_kw=it_load_kw, shared=shared)
    return _json({"shared_water": shared, "chiller": chiller})


ALL_TOOL_FUNCS = [
    list_projects, load_project,
    calc_beam_depth, calc_slab_thickness, calc_column_and_footing, calc_retaining_wall,
    calc_generator_room_openings,
    calc_chiller_sizing,
]
