from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# The main task has exactly two legal actions. / 主任务严格只有两种合法行动。
VALID_ACTIONS = {"BUY", "SELL"}


@dataclass(frozen=True)
class HistoryRecord:
    """One complete historical source record. / 一条完整的 source 历史记录。"""
    period: int
    source_action: str
    realized_state: str

    @property
    def is_correct(self) -> bool:
        return (self.source_action == "BUY" and self.realized_state == "UP") or (
            self.source_action == "SELL" and self.realized_state == "DOWN"
        )


@dataclass(frozen=True)
class Scenario:
    """Researcher-side scenario object. / 仅研究者侧持有的情境对象。"""
    family_id: str
    direction: str
    private_reliability: float
    private_direction: str
    source_action: str
    histories: dict[str, list[HistoryRecord]]


@dataclass(frozen=True)
class Trial:
    """One randomized model invocation. / 一次随机化的模型调用。"""
    trial_id: str
    scenario: Scenario
    treatment_id: str
    replicate_id: int
    order_index: int


def to_jsonable(value: Any) -> Any:
    """Convert nested dataclasses for immutable JSONL storage.
    将嵌套 dataclass 转换为适合不可变 JSONL 存储的结构。
    """
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
