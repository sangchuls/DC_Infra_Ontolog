# tools/generator_tools.py
# generator-calc(D:\DATA\앱개발\generator-calc)의 발전기실 흡배기 산정 로직을 LangChain @tool로 래핑

from typing import Optional
from langchain_core.tools import tool

from engine.generator_calc import compute_generator_room


@tool
def calc_generator_room_openings(
    manufacturer: str = "cummins",
    kw: Optional[float] = None,
    n_i: Optional[int] = None,
    n_e: Optional[int] = None,
    sf: Optional[float] = None,
) -> dict:
    """발전기실 급배기(그릴·소음기·댐퍼) 소요 개구 면적을 산정한다.

    manufacturer: 'cummins' | 'cat' | 'mtu' | 'rehlko'
    kw: Stand-by Power(kW). 미지정 시 제조사 대표 모델(카탈로그 is_default) 사용
    n_i / n_e: 급기/배기 대수. 미지정 시 기본 8대
    sf: 여유율 배수. 미지정 시 기본 1.2
    반환값에는 절대 풍속 한계(물리적 제약) 초과 시 velocity_warnings 가 포함된다.
    """
    return compute_generator_room(manufacturer=manufacturer, kw=kw, n_i=n_i, n_e=n_e, sf=sf)


GENERATOR_TOOLS = [calc_generator_room_openings]
