# agent/tools.py
# Anthropic 전용 @beta_tool 래퍼. 실제 로직은 tools_common.py 에 있고 여기서는 데코레이션만 한다.

from anthropic import beta_tool

from agent import tools_common as _c

list_projects = beta_tool(_c.list_projects)
load_project = beta_tool(_c.load_project)
calc_beam_depth = beta_tool(_c.calc_beam_depth)
calc_slab_thickness = beta_tool(_c.calc_slab_thickness)
calc_column_and_footing = beta_tool(_c.calc_column_and_footing)
calc_retaining_wall = beta_tool(_c.calc_retaining_wall)
calc_generator_room_openings = beta_tool(_c.calc_generator_room_openings)
calc_chiller_sizing = beta_tool(_c.calc_chiller_sizing)

ALL_AGENT_TOOLS = [
    list_projects, load_project,
    calc_beam_depth, calc_slab_thickness, calc_column_and_footing, calc_retaining_wall,
    calc_generator_room_openings,
    calc_chiller_sizing,
]
