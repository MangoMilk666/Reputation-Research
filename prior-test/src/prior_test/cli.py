from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from .analyze import write_analysis_artifacts
from .runner import run


ROOT = Path(__file__).resolve().parents[2]


def load_config(path: Path) -> dict:
    """Read the frozen protocol configuration.
        读取冻结的 protocol 配置。"""
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    """Run the full pipeline or recompute artifacts.
        运行全流程或重算既有产物。"""
    parser = argparse.ArgumentParser(description="Reputation prior-test harness")
    # `run` 是日常使用的完整实验命令，自动完成全部数据与图表产物；
    # `analyze` 不调用模型，只针对一个既有运行目录重新计算 summary、派生表与图。
    parser.add_argument("command", choices=["run", "analyze"], help="run executes the full pipeline; analyze regenerates artifacts for an existing run.")
    # protocol 配置 JSON 路径。默认 `configs/pilot_v1.json`
    parser.add_argument("--config", type=Path, default=ROOT / "configs/pilot_v1.json")
    # 本次运行输出目录。目录必须不存在，防止覆盖原始数据。
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--backend", choices=["mock", "ollama"], default="mock")
    parser.add_argument("--max-trials", type=int, default=None)
    args = parser.parse_args()
    if args.command == "run":
        output = args.output or ROOT / "data/runs" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        count = run(load_config(args.config), (ROOT / "prompts/system_v1.txt").read_text(encoding="utf-8"), output, args.backend, args.max_trials)
        print(json.dumps({"run_dir": str(output), "trials": count, "backend": args.backend, "artifacts": ["summary.json", "derived_decisions.csv", "figures/"]}))
    else:
        if args.output is None:
            parser.error("analyze requires --output RUN_DIRECTORY")
        result = write_analysis_artifacts(args.output)
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
