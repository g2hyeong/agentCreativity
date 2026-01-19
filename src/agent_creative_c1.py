# src/agent_creative_c1.py

from agent_creative import EscapeAgent as BaseCreativeAgent
import env

from env.bag_c1 import BagC1
from c1_loader import load_c1

# 아래 import들은 BaseCreativeAgent가 이미 쓰는 구성과 동일해야 합니다.
from agent_base import *
from cprint import *
from copy import deepcopy

from instruction import BASE_SYS_PROMPT_COT as SYS_ACTION
from instruction import CREATIVE_SYS_FORESEE_TASK as SYS_FORESEE_TASK
from utils import parse_foresee_task_response


def _normalize_game_id(game_name: str) -> str:
    # game3-2-easy / game3-2-hard -> game3-2
    return game_name.replace("-easy", "").replace("-hard", "")


class EscapeAgent(BaseCreativeAgent):
    """
    C1 version agent (without exposing 'C1' token to the agent):
    - Tool memory tags: shown only in BagC1.describe()
    - Item memory tags: appended into task[1] strategy right after a new task is created
    - Item memory instruction: injected only once in forethought() Task branch
    """

    def setup(self, controller, game_name):
        super().setup(controller, game_name)

        game_id = _normalize_game_id(game_name)

        # ✅ Bag 교체: Tool memory tags는 Bag에서만 노출
        env.global_vars.bag = BagC1(game_id)

        # ✅ Item memory DB 로드
        self.item_c1_db = load_c1("item", game_id)

    # -----------------------
    # reflect: new task 생성 직후 Item memory tags 삽입
    # -----------------------
    def reflect(self, log):
        # baseline reflect 수행 (여기서 self.new_task_created가 만들어질 수 있음)
        super().reflect(log)

        # baseline reflect가 new_task_created를 만들면, 여기서 후처리
        if getattr(self, "new_task_created", None):
            new_task, idx = self.new_task_created
            target_item = new_task[3]

            if target_item in getattr(self, "item_c1_db", {}):
                mem = self.item_c1_db[target_item]
                req = ", ".join(mem.get("requires", []))
                avoid = ", ".join(mem.get("avoid", []))

                strategy = self.tasks[idx][1]

                # ✅ 중복 삽입 방지: 'Memory:' 기준
                if "Memory:" not in strategy:
                    mem_line = "Memory:"
                    if req:
                        mem_line += f" likely needs {req}"
                    if avoid:
                        mem_line += f"; avoid {avoid}"

                    self.tasks[idx][1] = (strategy.strip() + " " + mem_line).strip()

    # -----------------------
    # forethought: Task 분기만 override해서 instruction 1줄 삽입
    # (Tool 분기/기타 분기는 baseline 그대로)
    # -----------------------
    def forethought(self, log):
        # 1) new tool collected: baseline 그대로
        if self.new_tool_collected:
            return super().forethought(log)

        # 2) new task created: 여기만 memory instruction 추가
        if self.new_task_created:
            print("\n -=-=-=-=-=-=-=-=-=-=- Forethought Task (Memory) -=-=-=-=-=-=-=-=-=-=- \n")

            prompt = "The current task that you are trying to solve now:\n"
            prompt += (
                f"[Task] Name: {self.new_task_created[0][0]}, Target Item: {self.new_task_created[0][3]}\n"
                f"{self.new_task_created[0][1]}\n\n"
            )

            tools_in_bag = env.global_vars.bag.describe(use_index=False).split("object in the scene:\n")[-1].strip()
            prompt += (
                "Here are all the tools in your bag. You may use 'apply' action to apply a tool to the Target Item in current task and try to solve it:\n"
                f"{tools_in_bag}\n\n"
            )

            prompt += (
                "Here are the hints from the memory pad. You may use them as reference when deciding how to solve current task:\n"
                f"{self.memory_pad}\n\n"
            )

            # ✅ 'C1' 제거, 'combine' 제거: '과거 기억 기반으로 가장 적합한 행동을 떠올려라'
            prompt += (
                "Memory guidance: If the task description includes memory tags (e.g., what the object likely needs / what to avoid), "
                "treat them as what you remember about solving similar objects. "
                "Use this recollection to recall the single most fitting next action before trying alternatives.\n\n"
            )

            prompt += (
                "Please follow the system prompt to output your Thought and Actions. "
                "You should analyze thoroughly and be bold to propose all plausible click, apply, and input actions. "
                "Your response:\n"
            )

            cprint.err(prompt)
            print()

            response = call_LLM(self.controller, SYS_FORESEE_TASK, prompt, self.is_api, self.port)
            response = response.replace("\n\n", "\n").strip()
            cprint.info(response)

            tool_name_list = [tool.name for tool in env.global_vars.bag.tools.values()]
            target_item_name = self.new_task_created[0][3]
            target_task_index = self.new_task_created[1]

            thought, actions = parse_foresee_task_response(
                response, tool_name_list, target_item_name, target_task_index
            )

            self.foresee_actions = actions
            log["foresee"] = {
                "cause": "new_task_created",
                "response": response,
                "thought": thought,
                "actions": actions
            }

            if len(self.foresee_actions) > 0:
                self.position_before_tasks = self.history[-1]["position"]

            # baseline과 동일한 reset 규칙
            if self.stuck:
                pass
            self.new_tool_collected = None
            self.new_task_created = None
            self.prompt_craft = False
            return

        # 3) 나머지는 baseline 그대로
        return super().forethought(log)


if __name__ == "__main__":
    args = parse_args()
    judge = EscapeAgent(args)
    for model in args.models:
        for game in args.games:
            cprint.info(f"Now testing: model {model} on {game}")
            judge.run(model, game)
