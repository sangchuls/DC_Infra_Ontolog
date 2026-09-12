# tools/chiller_tools.py
# 냉동기수량계산x(D:\DATA\앱개발\냉동기수량계산x)의 냉동기 대수·저수조 산정 로직을 LangChain @tool로 래핑

from typing import Optional
from langchain_core.tools import tool

from engine.chiller_calc import compute_shared_water, compute_water_chiller, compute_air_chiller


@tool
def calc_shared_water_tank(
    count: Optional[int] = None,
    usage_l_per_day: Optional[float] = None,
    days: Optional[float] = None,
    fire_ton: Optional[float] = None,
) -> dict:
    """부가 저수조(생활용수 + 소방용수) 용량을 산정한다. 수냉/공냉 냉동기 저수조 결과에 공통 가산된다.

    count: 상주 인원수(인)
    usage_l_per_day: 1인당 생활용수 사용량(L/인·일)
    days: 저장 일수
    fire_ton: 소방용수(TON) — 옥내소화전·스프링클러 등 소방 설계기준에 따라 별도 산정한 값
    """
    return compute_shared_water(count, usage_l_per_day, days, fire_ton)


@tool
def calc_water_cooled_chiller(
    it_load_kw: float,
    kcal_factor: Optional[float] = None,
    rt_factor: Optional[float] = None,
    unit_cap_rt: Optional[float] = None,
    spare: Optional[int] = None,
    tank_unit_ton: Optional[float] = None,
    tank_margin: Optional[float] = None,
    shared_water_ton: Optional[float] = None,
) -> dict:
    """수냉식 냉동기 소요 대수 및 저수조 용량을 산정한다.

    it_load_kw: IT 부하(kW)
    kcal_factor: 열량 환산계수(kcal/kWh). 기본 860
    rt_factor: RT 환산계수(kcal/h per USRT). 기본 3,024
    unit_cap_rt: 냉동기 대당 용량(RT)
    spare: 예비 대수
    tank_unit_ton: 냉동기 대당 저수량(TON)
    tank_margin: 저수조 여유율 배수
    shared_water_ton: calc_shared_water_tank 결과의 additional_water_total_ton 값. 지정 시 총 저수조 용량에 합산
    """
    shared = {"additional_water_total_ton": shared_water_ton} if shared_water_ton is not None else None
    return compute_water_chiller(it_load_kw, kcal_factor, rt_factor, unit_cap_rt, spare, tank_unit_ton, tank_margin, shared)


@tool
def calc_air_cooled_chiller(
    it_load_kw: float,
    safety_factor: Optional[float] = None,
    other_load_factor: Optional[float] = None,
    ut_load_factor: Optional[float] = None,
    unit_cap_kw: Optional[float] = None,
    spare: Optional[int] = None,
    hours: Optional[float] = None,
    tank_spare: Optional[int] = None,
    margin_hours: Optional[float] = None,
    margin_mode: Optional[str] = None,
    shared_water_ton: Optional[float] = None,
) -> dict:
    """공냉식 냉동기 소요 대수 및 저수조 용량을 산정한다.

    it_load_kw: IT 부하(kW)
    safety_factor / other_load_factor / ut_load_factor: 안전율 / 기타부하율 / UT부하율
    unit_cap_kw: 냉동기 대당 용량(kW)
    spare: 예비 대수
    hours: 운영 시간
    tank_spare: 저수조용 예비 대수 (margin_mode='spare'일 때 사용)
    margin_hours: 저수조용 여유 시간 (margin_mode='hours'일 때 사용)
    margin_mode: 'spare'(예비대수 반영, 기본값) | 'hours'(여유시간 반영)
    shared_water_ton: calc_shared_water_tank 결과의 additional_water_total_ton 값. 지정 시 총 저수조 용량에 합산
    """
    shared = {"additional_water_total_ton": shared_water_ton} if shared_water_ton is not None else None
    return compute_air_chiller(
        it_load_kw, safety_factor, other_load_factor, ut_load_factor, unit_cap_kw,
        spare, hours, tank_spare, margin_hours, margin_mode, shared,
    )


CHILLER_TOOLS = [calc_shared_water_tank, calc_water_cooled_chiller, calc_air_cooled_chiller]
