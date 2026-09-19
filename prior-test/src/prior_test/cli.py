from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .analyze import write_analysis_artifacts
from .runner import run


ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    """读取冻结的 protocol 配置；运行记录会完整复制其中的参数。"""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """运行全流程，或在不调用模型的前提下重算既有运行目录的分析产物。"""
    parser = argparse.ArgumentParser(description="Reputation prior-test harness")
    # run 自动完成调用、日志、汇总和画图；
    # analyze 只重算已有目录，不产生新模型请求。
    parser.add_argument("command", choices=["run", "analyze"], help="run executes the full pipeline; analyze regenerates artifacts for an existing run.")
    # 默认使用 v2；旧 v1 配置仅保留用于审计已完成的旧运行。
    parser.add_argument("--config", type=Path, default=ROOT / "configs/pilot_v2.json")
    # 输出目录必须不存在，避免覆盖原始请求和响应。
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--backend", choices=["mock", "ollama"], default="mock")
    parser.add_argument("--max-trials", type=int, default=None)
    args = parser.parse_args()
    if args.command == "run":
        output = args.output or ROOT / "data/runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        config = load_config(args.config)
        prompt_path = ROOT / config["system_prompt_file"]
        count = run(config, prompt_path.read_text(encoding="utf-8"), output, args.backend, args.max_trials)
        print(json.dumps({"run_dir": str(output), "trials": count, "backend": args.backend, "artifacts": ["summary.json", "derived_decisions.csv", "figures/"]}))
    else:
        if args.output is None:
            parser.error("analyze requires --output RUN_DIRECTORY")
        result = write_analysis_artifacts(args.output)
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
