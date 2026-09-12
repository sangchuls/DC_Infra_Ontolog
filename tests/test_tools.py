"""LangChain @tool 래핑 레이어 스모크 테스트. langchain-core 필요.
실행: python tests/test_tools.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import ALL_TOOLS, STRUCTURAL_TOOLS, GENERATOR_TOOLS, CHILLER_TOOLS

if __name__ == "__main__":
    print(f"총 {len(ALL_TOOLS)}개 tool 등록됨 "
          f"(structural {len(STRUCTURAL_TOOLS)} / generator {len(GENERATOR_TOOLS)} / chiller {len(CHILLER_TOOLS)})\n")
    for t in ALL_TOOLS:
        print(f"- {t.name}: {t.description.strip().splitlines()[0]}")

    print("\n--- invoke 테스트 ---")
    beam_tool = next(t for t in ALL_TOOLS if t.name == "calc_beam_depth")
    print("calc_beam_depth:", beam_tool.invoke({"span_m": 10.0, "material": "RC"}))

    gen_tool = next(t for t in ALL_TOOLS if t.name == "calc_generator_room_openings")
    print("calc_generator_room_openings:", gen_tool.invoke({"manufacturer": "cummins", "kw": 3000})["OA_total_m2"])

    chiller_tool = next(t for t in ALL_TOOLS if t.name == "calc_water_cooled_chiller")
    print("calc_water_cooled_chiller:", chiller_tool.invoke({"it_load_kw": 38000})["installed_units"])

    print("\nAll tool wrapper smoke tests passed.")
