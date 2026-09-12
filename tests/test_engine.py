"""엔진 순수 함수 스모크 테스트 (langchain 미설치 상태에서도 실행 가능).
실행: python tests/test_engine.py  (데이터센터통합검토시스템/ 를 cwd로)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.beam_calc import estimate_beam_depth, estimate_slab_thickness
from engine.column_calc import calculate_axial_load, estimate_rc_column, estimate_src_column, recommend_column_type
from engine.foundation_calc import estimate_footing, estimate_retaining_wall
from engine.generator_calc import compute_generator_room
from engine.chiller_calc import compute_shared_water, compute_water_chiller, compute_air_chiller


def approx(a, b, tol=0.05):
    return abs(a - b) <= tol


def test_structural():
    beam = estimate_beam_depth(10.0, "RC")
    assert beam["depth_mm"] > 0
    slab = estimate_slab_thickness(10.0, "RC", is_two_way=True)
    assert slab["thickness_mm"] >= 100
    axial = calculate_axial_load(100.0, 6.0, 12.0, 5, 1.5)
    assert axial == 100.0 * (6.0 + 12.0) * 5 * 1.5
    col = estimate_rc_column(axial, 27.0)
    assert col["size_mm"] > 0
    footing = estimate_footing(axial, 10.0, 200.0)
    assert footing["req_area_m2"] > 0
    rw = estimate_retaining_wall(8.0)
    assert rw["thickness_mm"] >= 300
    print("[OK] structural:", beam["depth_mm"], "mm /", slab["thickness_mm"], "mm /", axial, "kN /", recommend_column_type(axial))


def test_generator():
    r = compute_generator_room(manufacturer="cummins", kw=3000)
    # generator-calc/app.jsx 의 DEF(cummins 3000kW) 기준 검증값
    assert r["catalog"]["oa_m2"] == 7.2
    assert r["catalog"]["ea_m2"] == 5.7
    assert approx(r["OA_total_m2"], 69.12)
    assert approx(r["EA_total_m2"], 54.72)
    assert approx(r["per_unit_gross_m2"]["intake"]["da"], 8.64)
    assert approx(r["per_unit_gross_m2"]["exhaust"]["da"], 6.84)
    assert r["velocity_warnings"] == {}, "기본값은 절대풍속 한계를 넘지 않아야 함"
    print("[OK] generator:", r["model"], "OA=", r["OA_total_m2"], "EA=", r["EA_total_m2"])


def test_chiller():
    shared = compute_shared_water()
    assert shared["additional_water_total_ton"] == 105.0

    water = compute_water_chiller(it_load_kw=38000, shared=shared)
    assert water["running_units"] == 8
    assert water["installed_units"] == 9
    assert approx(water["total_tank_capacity_ton"], 3289.0, tol=1.0)

    air = compute_air_chiller(it_load_kw=38000, shared=shared)
    assert air["running_units"] == 22
    assert air["installed_units"] == 23
    assert approx(air["total_tank_capacity_ton"], 657.0, tol=1.0)
    print("[OK] chiller: water=", water["installed_units"], "대 /", water["total_tank_capacity_ton"],
          "TON, air=", air["installed_units"], "대 /", air["total_tank_capacity_ton"], "TON")


if __name__ == "__main__":
    test_structural()
    test_generator()
    test_chiller()
    print("\nAll engine smoke tests passed.")
