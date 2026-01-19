# src/env/bag_c1.py
from typing import Dict
from .bag import Bag
from c1_loader import load_c1


class BagC1(Bag):
    """
    C1 전용 Bag:
    - describe()에서 tool C1을 state-aware로 출력
    - baseline Bag는 그대로 둠
    """

    def __init__(self, game_id: str):
        super().__init__()
        self.game_id = game_id
        self.tool_c1_db: Dict = load_c1("tool", game_id)

    def describe(self, use_index, with_desc=True, ignore_tools=[]):
        if len(self.tools) == 0:
            return "There's currently not tool in your bag."

        output = (
            "Here are the tools in your bag. You can perform 'craft' to use two tools in your bag to craft a new one, "
            "or perfom 'apply' to apply one tool in your bag to an object in the scene:\n"
        )

        # ✅ Tool C1 instruction: Bag 최상단 1회
        if self.tool_c1_db:
            output += (
               "Memory note: Use the tags below as what you remember about how each tool was used before. "
               "Recall the most fitting action for the current situation before trying anything else.\n"
            )

        index = 1
        for name, tool in self.tools.items():
            if name in ignore_tools:
                continue

            if use_index:
                output += f"<{index}> {name}"
            else:
                output += f"<applicable tool> {name}"

            if with_desc:
                output += f": {tool.describe()}"

            # ✅ state-aware tool C1
            if name in self.tool_c1_db and isinstance(self.tool_c1_db[name], dict):
                state_key = str(getattr(tool, "current_state", 0))
                state_info = self.tool_c1_db[name].get(state_key, None)
                if isinstance(state_info, dict):
                    aff = ", ".join(state_info.get("affordance", []))
                    avoid = ", ".join(state_info.get("avoid", []))
                    if aff:
                        output += f" | memory: {aff}"
                    if avoid:
                        output += f" | avoid: {avoid}"

            output += "\n"
            self.action_cache[index] = ("tool", name)
            index += 1

        return output
