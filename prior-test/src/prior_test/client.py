from __future__ import annotations

import json
import random
import re
import time
from urllib.request import Request, urlopen
from dataclasses import dataclass


@dataclass
class Completion:
    content: str
    request_id: str | None
    usage: dict
    latency_ms: int


class MockClient:
    """确定性开发客户端，只验证数据链路，绝不代表实证结果。"""
    def complete(self, *, user_context: str, seed: int, **_: object) -> Completion:
        started = time.perf_counter()
        # mock 与 Ollama 使用同一份渲染文本，便于尽早发现字段名或格式变化。
        private_direction = re.search(r"directional_implication: (UP|DOWN)", user_context).group(1)
        private_action = "BUY" if private_direction == "UP" else "SELL"
        source_action = re.search(r"observed_order: (BUY|SELL)", user_context)
        # 必须匹配 source.history 的缩进字段，不能把 own_trading_history 误判为 source 历史。
        if not source_action or "\n  history:" not in user_context:
            action = private_action
        else:
            records = re.findall(r"prediction: (BUY|SELL); realized_state: (UP|DOWN)", user_context)
            correct = sum((prediction == "BUY") == (realized == "UP") for prediction, realized in records)
            probability = {12: 0.35, 16: 0.60, 18: 0.80}[correct]
            action = source_action.group(1) if random.Random(seed).random() < probability else private_action
        return Completion(json.dumps({"action": action}), "mock", {}, int((time.perf_counter() - started) * 1000))


class OllamaClient:
    def __init__(self, base_url: str, model: str, temperature: float, max_tokens: int, thinking: bool | str | None = None):
        from openai import OpenAI
        # Ollama 提供 OpenAI 兼容端点，普通模型可以直接通过官方 SDK 调用。
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model, self.temperature, self.max_tokens, self.thinking = model, temperature, max_tokens, thinking
        # 当协议显式控制 thinking 时，必须使用 Ollama 原生端点，避免兼容层忽略该参数。
        self.native_chat_url = f"{base_url.removesuffix('/v1').rstrip('/')}/api/chat"

    def complete(self, *, system_prompt: str, user_context: str, seed: int, **_: object) -> Completion:
        started = time.perf_counter()
        if self.thinking is not None:
            return self._complete_native(system_prompt, user_context, started)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_context}],
            temperature=self.temperature, max_tokens=self.max_tokens, seed=seed,
            response_format={"type": "json_object"},
        )
        usage = response.usage.model_dump() if response.usage else {}
        return Completion(response.choices[0].message.content or "", getattr(response, "_request_id", None), usage, int((time.perf_counter() - started) * 1000))

    def _complete_native(self, system_prompt: str, user_context: str, started: float) -> Completion:
        """使用 Ollama 原生接口，确保 `think` 不会在 OpenAI 兼容层被忽略。"""
        # JSON Schema 只约束输出格式，不会向模型泄漏正确答案或 treatment 标签。
        payload = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_context}],
            "options": {"temperature": self.temperature, "num_predict": self.max_tokens},
            "think": self.thinking,
            "format": {
                "type": "object",
                "properties": {"action": {"type": "string", "enum": ["BUY", "SELL"]}},
                "required": ["action"],
                "additionalProperties": False,
            },
            "stream": False,
        }
        request = Request(self.native_chat_url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
        usage = {key: body[key] for key in ("prompt_eval_count", "eval_count", "total_duration", "load_duration") if key in body}
        return Completion(body["message"].get("content", ""), None, usage, int((time.perf_counter() - started) * 1000))


def parse_action(content: str) -> str:
    """拒绝解释性文本和格式错误回复，避免其被误计为有效交易。"""
    payload = json.loads(content)
    if set(payload) != {"action"} or payload["action"] not in {"BUY", "SELL"}:
        raise ValueError("response must be exactly {'action': 'BUY'|'SELL'}")
    return payload["action"]
