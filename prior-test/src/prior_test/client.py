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
    def __init__(self, base_url: str, model: str, temperature: float, max_tokens: int, thinking: bool | str | None = None):
        from openai import OpenAI
        # Ollama exposes an OpenAI-compatible endpoint. / Ollama 提供 OpenAI 兼容端点。
        self.client = OpenAI(base_url=base_url, api_key="ollama")
        self.model, self.temperature, self.max_tokens, self.thinking = model, temperature, max_tokens, thinking
        # Ollama's native endpoint is required when a protocol explicitly controls thinking.
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
        # JSON Schema constrains the final answer without exposing an answer or treatment label.
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
    """Reject explanations and malformed replies.
    拒绝解释性文本与格式错误回复。"""
    payload = json.loads(content)
    if set(payload) != {"action"} or payload["action"] not in {"BUY", "SELL"}:
        raise ValueError("response must be exactly {'action': 'BUY'|'SELL'}")
    return payload["action"]
