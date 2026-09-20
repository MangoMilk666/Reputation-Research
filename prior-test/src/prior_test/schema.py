from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


# 主任务只接受这两个方向，避免无意间把 HOLD 或解释文本当作有效决策。
VALID_ACTIONS = {"BUY", "SELL"}


@dataclass(frozen=True)
class HistoryRecord:
    """source 过去一次预测及其已实现的市场状态。"""

    period: int
    source_action: str
    realized_state: str

    @property
    def is_correct(self) -> bool:
        """按 BUY→UP、SELL→DOWN 的冻结规则判断该条预测是否正确。"""
        return (self.source_action == "BUY" and self.realized_state == "UP") or (
            self.source_action == "SELL" and self.realized_state == "DOWN"
        )


@dataclass(frozen=True)
class OwnTradeRecord:
    """receiver 自己的历史成交记录，用于构成一致的个人资产路径。"""

    period: int
    action: str
    quantity: int
    execution_price: float


@dataclass(frozen=True)
class PortfolioState:
    """当前 portfolio 与价格参照点；所有字段都将在公开 context 中保持一致。"""

    cash: float
    inventory: int
    average_cost_basis: float
    current_price: float
    all_time_high: float
    all_time_low: float
    reference_price_state: str | None

    @property
    def current_position_market_value(self) -> float:
        """返回当前持仓市值，供 renderer 与校验器使用同一计算口径。"""
        return self.inventory * self.current_price

    @property
    def unrealized_gain_loss(self) -> float:
        """返回持仓相对平均成本的未实现盈亏。"""
        return self.inventory * (self.current_price - self.average_cost_basis)


@dataclass(frozen=True)
class Scenario:
    """研究者侧完整情境，包含不可直接泄漏到 prompt 的配对结构。"""

    family_id: str
    private_reliability: float
    private_direction: str
    source_action: str | None
    portfolio: PortfolioState | None
    own_history: list[OwnTradeRecord]
    histories: dict[str, list[HistoryRecord]]
    context_variant: str = "legacy_v2"

    @property
    def signal_relation(self) -> str | None:
        """标记 source 与 private signal 是一致还是冲突，供分析分层使用。"""
        if self.source_action is None:
            return None
        private_action = "BUY" if self.private_direction == "UP" else "SELL"
        return "agreement" if self.source_action == private_action else "conflict"


@dataclass(frozen=True)
class Trial:
    """一次随机化模型调用及其所属情境和处理组。"""

    trial_id: str
    scenario: Scenario
    treatment_id: str
    replicate_id: int
    order_index: int


def to_jsonable(value: Any) -> Any:
    """将嵌套 dataclass 递归转换为可写入不可变 JSONL 的普通对象。"""
    if hasattr(value, "__dataclass_fields__"):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    return value
