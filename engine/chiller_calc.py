# engine/chiller_calc.py
# 냉동기 소요 대수 및 저수조 용량 산정 모듈 (수냉식 / 공냉식)
# 원본: D:\DATA\앱개발\냉동기수량계산x\script.js 의 computeShared/computeWater/computeAir 를 Python으로 포팅
# (원본은 DOM 입력값을 직접 읽는 구조라, 여기서는 동일 공식을 순수 함수로 분리했다)

import math

# index.html 기본값 (부가 저수조)
DEFAULT_SHARED = {"count": 50, "usage_l_per_day": 100, "days": 1, "fire_ton": 100}
# index.html 기본값 (수냉식)
DEFAULT_WATER = {
    "it_load_kw": 38000, "kcal_factor": 860, "rt_factor": 3024,
    "unit_cap_rt": 1500, "spare": 1, "tank_unit_ton": 199, "tank_margin": 2,
}
# index.html 기본값 (공냉식)
DEFAULT_AIR = {
    "it_load_kw": 38000, "safety_factor": 1.1, "other_load_factor": 1.08, "ut_load_factor": 1.08,
    "unit_cap_kw": 2300, "spare": 1, "hours": 24, "tank_spare": 1, "margin_hours": 4,
    "margin_mode": "spare",  # 'spare'(예비대수 반영) | 'hours'(여유시간 반영)
}


def compute_shared_water(count=None, usage_l_per_day=None, days=None, fire_ton=None) -> dict:
    """
    부가 저수조(생활용수 + 소방용수) 용량을 산정한다. 수냉/공냉 결과에 공통 가산된다.

    count: 상주 인원수(인)
    usage_l_per_day: 1인당 사용량(L/인·일)
    days: 저장 일수
    fire_ton: 소방용수(TON) — 옥내소화전·스프링클러 등 소방 설계기준에 따라 별도 산정한 값을 입력
    """
    p = dict(DEFAULT_SHARED)
    for k, v in {"count": count, "usage_l_per_day": usage_l_per_day, "days": days, "fire_ton": fire_ton}.items():
        if v is not None:
            p[k] = v

    domestic_ton = (p["count"] * p["usage_l_per_day"] * p["days"]) / 1000
    total_ton = domestic_ton + p["fire_ton"]
    return {
        "domestic_water_ton": round(domestic_ton, 1),
        "fire_water_ton": p["fire_ton"],
        "additional_water_total_ton": round(total_ton, 1),
    }


def compute_water_chiller(
    it_load_kw=None, kcal_factor=None, rt_factor=None, unit_cap_rt=None,
    spare=None, tank_unit_ton=None, tank_margin=None, shared: dict = None,
) -> dict:
    """
    수냉식 냉동기 소요 대수 및 저수조 용량을 산정한다.

    it_load_kw: IT 부하(kW)
    kcal_factor: 열량 환산계수(kcal/kWh). 기본 860
    rt_factor: RT 환산계수(kcal/h per USRT). 기본 3,024
    unit_cap_rt: 냉동기 대당 용량(RT)
    spare: 예비 대수
    tank_unit_ton: 냉동기 대당 저수량(TON)
    tank_margin: 저수조 여유율 배수
    shared: compute_shared_water() 결과(dict). 지정 시 총 저수조 용량에 합산

    산식: 냉동부하(USRT) = IT부하×열량환산계수 ÷ RT환산계수
          설치대수 = ceil(냉동부하 ÷ 대당용량) + 예비대수
          냉각수 저수조 = 대당저수량 × 가동대수 × 여유율
    """
    p = dict(DEFAULT_WATER)
    for k, v in {
        "it_load_kw": it_load_kw, "kcal_factor": kcal_factor, "rt_factor": rt_factor,
        "unit_cap_rt": unit_cap_rt, "spare": spare, "tank_unit_ton": tank_unit_ton, "tank_margin": tank_margin,
    }.items():
        if v is not None:
            p[k] = v

    heat_kcal_h = p["it_load_kw"] * p["kcal_factor"]
    rt_usrt = heat_kcal_h / p["rt_factor"]
    raw_count = rt_usrt / p["unit_cap_rt"]
    count = max(0, math.ceil(raw_count))
    total_units = count + p["spare"]
    tank_base_ton = p["tank_unit_ton"] * count
    tank_final_ton = tank_base_ton * p["tank_margin"]

    shared_total = shared["additional_water_total_ton"] if shared else 0
    grand_total_ton = tank_final_ton + shared_total

    return {
        "cooling_load_usrt": round(rt_usrt, 1),
        "running_units": count,
        "spare_units": p["spare"],
        "installed_units": total_units,
        "cooling_water_tank_ton": round(tank_final_ton, 1),
        "additional_water_ton": round(shared_total, 1),
        "total_tank_capacity_ton": round(grand_total_ton, 1),
        "basis": "냉동부하=IT부하×860÷3,024(기본값). 설치대수=ceil(부하÷대당용량)+예비. 저수조=대당저수량×가동대수×여유율",
    }


def compute_air_chiller(
    it_load_kw=None, safety_factor=None, other_load_factor=None, ut_load_factor=None,
    unit_cap_kw=None, spare=None, hours=None, tank_spare=None, margin_hours=None,
    margin_mode=None, shared: dict = None,
) -> dict:
    """
    공냉식 냉동기 소요 대수 및 저수조 용량을 산정한다.

    it_load_kw: IT 부하(kW)
    safety_factor / other_load_factor / ut_load_factor: 안전율 / 기타부하율 / UT부하율
    unit_cap_kw: 냉동기 대당 용량(kW)
    spare: 예비 대수
    hours: 운영 시간
    tank_spare: 저수조 산정용 예비 대수 (margin_mode='spare'일 때 사용)
    margin_hours: 여유 시간 (margin_mode='hours'일 때 사용)
    margin_mode: 'spare'(예비대수 반영) | 'hours'(여유시간 반영) — 저수조 여유를 어느 쪽으로 반영할지
    shared: compute_shared_water() 결과(dict). 지정 시 총 저수조 용량에 합산

    산식: 종합부하(kW) = IT부하 × 안전율 × 기타부하율 × UT부하율
          설치대수 = ceil(종합부하 ÷ 대당용량) + 예비대수
          냉각수 저수조(TON) = 저수조용대수 × 저수조용시간 × 1(TON 환산)
    """
    p = dict(DEFAULT_AIR)
    for k, v in {
        "it_load_kw": it_load_kw, "safety_factor": safety_factor, "other_load_factor": other_load_factor,
        "ut_load_factor": ut_load_factor, "unit_cap_kw": unit_cap_kw, "spare": spare, "hours": hours,
        "tank_spare": tank_spare, "margin_hours": margin_hours, "margin_mode": margin_mode,
    }.items():
        if v is not None:
            p[k] = v

    load_kw = p["it_load_kw"] * p["safety_factor"] * p["other_load_factor"] * p["ut_load_factor"]
    raw_count = load_kw / p["unit_cap_kw"]
    count = max(0, math.ceil(raw_count))
    total_units = count + p["spare"]

    if p["margin_mode"] == "spare":
        tank_count, tank_hours = count + p["tank_spare"], p["hours"]
    else:
        tank_count, tank_hours = count, p["hours"] + p["margin_hours"]
    tank_ton = tank_count * tank_hours * 1

    shared_total = shared["additional_water_total_ton"] if shared else 0
    grand_total_ton = tank_ton + shared_total

    return {
        "total_load_kw": round(load_kw, 1),
        "running_units": count,
        "spare_units": p["spare"],
        "installed_units": total_units,
        "cooling_water_tank_ton": round(tank_ton, 1),
        "additional_water_ton": round(shared_total, 1),
        "total_tank_capacity_ton": round(grand_total_ton, 1),
        "margin_mode": p["margin_mode"],
        "basis": "종합부하=IT부하×안전율×기타부하율×UT부하율. 설치대수=ceil(부하÷대당용량)+예비. 저수조=저수조용대수×저수조용시간×1TON",
    }
