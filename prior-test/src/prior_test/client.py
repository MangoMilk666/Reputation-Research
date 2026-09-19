from __future__ import annotations

import json
import random
import re
import time
from dataclasses import dataclass


@dataclass
class Completion:
    content: str
    request_id: str | None
    usage: dict
    latency_ms: int


class MockClient:
    """Deterministic development client; never represents empirical evidence.
    确定性的开发客户端；绝不代表实证结果。
    """
    def complete(self, *, user_context: str, seed: int, **_: object) -> Completion:
        started = time.perf_counter()
        # The mock consumes the same rendered text as Ollama. / mock 与 Ollama 使用同一渲染文本。
        private_direction = re.search(r"directional_implication: (UP|DOWN)", user_context).group(1)
        private_action = "BUY" if private_direction == "UP" else "SELL"
        source_action = re.search(r"current_action: (BUY|SELL)", user_context)
        if not source_action or "history:" not in user_context:
            action = private_action
        else:
            records = re.findall(r"prediction: (BUY|SELL); realized_state: (UP|DOWN)", user_context)
            correct = sum((prediction == "BUY") == (realized == "UP") for prediction, realized in records)
            probability = {12: 0.35, 16: 0.60, 18: 0.80}[correct]
            action = source_action.group(1) if random.Random(seed).random() < probability else private_action
        return Completion(json.dumps({"action": action}), "mock", {}, int((time.perf_counter() - started) * 1000))


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float, max_tokens: int):
        from openai import OpenAI
        # Ollama exposes an OpenAI-compatible endpoint. / Ollama 提供 OpenAI 兼容端点。
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model, self.temperature, self.max_tokens = model, temperature, max_tokens

    def complete(self, *, system_prompt: str, user_context: str, seed: int, **_: object) -> Completion:
        started = time.perf_counter()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_context}],
            temperature=self.temperature, max_tokens=self.max_tokens, seed=seed,
            response_format={"type": "json_object"},
        )
        usage = response.usage.model_dump() if response.usage else {}
        return Completion(response.choices[0].message.content or "", getattr(response, "_request_id", None), usage, int((time.perf_counter() - started) * 1000))


def parse_action(content: str) -> str:
    """Reject explanations and malformed replies.
    拒绝解释性文本与格式错误回复。"""
    payload = json.loads(content)
    if set(payload) != {"action"} or payload["action"] not in {"BUY", "SELL"}:
        raise ValueError("response must be exactly {'action': 'BUY'|'SELL'}")
    return payload["action"]
