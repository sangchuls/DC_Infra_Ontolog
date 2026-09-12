# engine/foundation_calc.py
# 하부 구조 (기초 & 지하 토압 옹벽) 규격 산정 모듈

import math


def estimate_footing(
    axial_load_kn: float,
    column_span_m: float,
    bearing_capacity_kpa: float = 200.0,
) -> dict:
    """
    독립기초 또는 매트기초 여부 판단 및 규격 산정.
    A_f = P / q_a
    """
    # 필요 기초 면적 (m²)
    req_area_m2 = axial_load_kn / bearing_capacity_kpa

    # 정방형 기초 한 변 길이
    side_m = math.sqrt(req_area_m2)
    # 100mm 단위 올림
    side_mm = (int(side_m * 1000) // 100 + 1) * 100
    side_m_practical = side_mm / 1000

    # 기초 두께: 한 변의 약 1/3 ~ 1/4, 최소 500mm
    thickness_mm = max(500, (int(side_mm * 0.3) // 50 + 1) * 50)

    # 기둥 간격 대비 기초 면적 비율로 매트/독립 판단
    bay_area_m2 = column_span_m * column_span_m
    coverage_ratio = req_area_m2 / bay_area_m2

    if coverage_ratio >= 0.5:
        footing_type = "매트기초 (Mat Foundation)"
        recommendation = "개별 기초 면적이 기둥 간격의 50% 이상 → 매트기초 권장"
    else:
        footing_type = "독립기초 (Isolated Footing)"
        recommendation = f"개별 기초 면적 비율 {coverage_ratio:.0%} → 독립기초 적용 가능"

    return {
        "type": footing_type,
        "axial_load_kn": axial_load_kn,
        "bearing_capacity_kpa": bearing_capacity_kpa,
        "req_area_m2": round(req_area_m2, 2),
        "side_m": side_m_practical,
        "thickness_mm": thickness_mm,
        "section": f"{side_m_practical:.1f}m × {side_m_practical:.1f}m × T{thickness_mm}mm",
        "coverage_ratio": round(coverage_ratio, 3),
        "recommendation": recommendation,
    }


def estimate_retaining_wall(
    basement_depth_m: float,
    soil_gamma: float = 18.0,    # 흙 단위중량 (kN/m³)
    phi_deg: float = 30.0,       # 내부마찰각 (도)
    surcharge_kpa: float = 10.0, # 지표 상재하중 (kN/m²)
    wall_type: str = "basement",  # 'basement'(지하외벽·구속형) | 'retaining'(옹벽·자립형)
) -> dict:
    """
    지하층 토압벽체 두께 추정.

    ▸ wall_type = 'retaining' (옹벽 자립형):
        랭킨 능동토압 Ka = tan²(45 - φ/2) 적용
        벽체가 변위(회전/이동) 가능한 경우에 성립
    ▸ wall_type = 'basement' (지하외벽 구속형, 기본값):
        정지토압 K0 = 1 - sin(φ) 적용
        상하 슬래브에 구속되어 거의 이동 불가 → 능동토압보다 K0가 실제에 가까움
        K0 > Ka 이므로 더 보수적(불리한) 설계값임
    """
    phi_rad = math.radians(phi_deg)

    if wall_type == "retaining":
        K = math.tan(math.radians(45) - phi_rad / 2) ** 2   # Ka (능동토압)
        pressure_type = "능동토압 (Ka, 랭킨)"
        pressure_note = "옹벽 자립형 — 벽체 변위 가능 조건 성립 시 적용"
    else:  # 'basement' 구속형 지하외벽
        K = 1.0 - math.sin(phi_rad)                          # K0 (정지토압)
        pressure_type = "정지토압 (K0, Jaky)"
        pressure_note = "지하외벽 구속형 — 상하 슬래브 구속으로 변위 불가, 능동토압 과소 → K0 적용"

    Ka_ref = math.tan(math.radians(45) - phi_rad / 2) ** 2   # 비교용 Ka 항상 산출

    H = basement_depth_m
    # 토압 합력 — 선택된 K 계수 사용
    Pa_triangular = 0.5 * K * soil_gamma * H ** 2
    Pa_surcharge  = K * surcharge_kpa * H
    Pa_total      = Pa_triangular + Pa_surcharge

    # 벽체 두께 추정: H/10 ~ H/12, 최소 300mm
    raw_thickness_m = H / 10.0
    thickness_mm = max(300, (int(raw_thickness_m * 1000) // 50 + 1) * 50)

    # 배면 수직 철근량 개략 추정 (단위: mm²/m)
    moment_kn_m = Pa_triangular * H / 3 + Pa_surcharge * H / 2
    fyk = 400
    d_eff = thickness_mm - 80
    As_req_mm2 = round((moment_kn_m * 1e6) / (0.9 * fyk * d_eff), 0) if d_eff > 0 else 0

    return {
        "depth_m":            H,
        "wall_type":          wall_type,
        "pressure_type":      pressure_type,
        "pressure_note":      pressure_note,
        "K":                  round(K, 4),
        "Ka_ref":             round(Ka_ref, 4),
        "Pa_total_kn_m":      round(Pa_total, 2),
        "thickness_mm":       thickness_mm,
        "section":            f"T{thickness_mm}mm / m",
        "moment_kn_m":        round(moment_kn_m, 2),
        "As_req_mm2_per_m":   As_req_mm2,
        "rebar_note":         f"소요 철근량 약 {As_req_mm2:.0f} mm²/m (배면 수직근, SD400 기준)",
        "note":               "개략 산정값. 기초 자중·편심·침하 검토는 별도 필요",
    }
