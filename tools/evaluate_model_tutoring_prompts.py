#!/usr/bin/env python3
"""Record prompt-version evaluation for a completed generic DSA run.

This first pilot compares the immutable registry identity and the observed
artifact metrics.  Metamorphic cases are structural input variants: they test
that public paraphrases/numeric substitutions preserve source variable
bindings without pretending that a new live model run occurred.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TOOLS = ROOT / "tools"
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(TOOLS))

import run_dual_luna_transcript as raw  # noqa: E402
from study_os.prompt_registry import DEFAULT_PROMPT_REGISTRY  # noqa: E402
import run_model_tutoring_all_dsa as runner  # noqa: E402


def _variant(statement: str, index: int) -> str:
    if index % 2:
        return statement.replace("Determine", "Decide").replace("Find", "Locate")
    return statement + " Example values may be replaced without changing the algorithmic relation."


def evaluate(
    corpus: dict[str, Any], *, acceptance_report: dict[str, Any], plans: list[dict[str, Any]],
) -> dict[str, Any]:
    definitions = [item.to_payload() for item in DEFAULT_PROMPT_REGISTRY.definitions]
    provenance_checks: list[dict[str, Any]] = []
    for plan in plans:
        payload = plan.get("plan_payload", {})
        provenance = payload.get("provenance", {}) if isinstance(payload, dict) else {}
        try:
            DEFAULT_PROMPT_REGISTRY.verify(
                version=str(provenance["prompt_version"]),
                prompt_hash=str(provenance["prompt_hash"]),
            )
            result = "passed"
        except (KeyError, ValueError) as exc:
            result = f"failed: {exc}"
        provenance_checks.append({"scenario_id": plan.get("scenario_id"), "status": result})

    metamorphic: list[dict[str, Any]] = []
    for index, scenario in enumerate(corpus.get("scenarios", [])):
        public = runner.build_decomposer_payload(scenario)
        transformed = dict(scenario)
        transformed["problem"] = _variant(str(scenario["problem"]), index)
        variant_payload = runner.build_decomposer_payload(transformed)
        metamorphic.append({
            "scenario_id": scenario["id"],
            "variant_kind": "paraphrase" if index % 2 else "numeric_or_example_substitution",
            "source_variables_preserved": public["variable_names"] == variant_payload["variable_names"],
            "hidden_annotations_absent": "expected" not in variant_payload and "learner_signal" not in variant_payload,
        })

    return {
        "schema_version": "study-os.model-tutoring-prompt-evaluation.v0.1",
        "evaluation_kind": "completed-artifact-plus-structural-metamorphic",
        "registry": {"schema_version": "study-os.model-tutoring-prompt-registry.v0.1", "definitions": definitions},
        "observed_run": {
            "acceptance_status": acceptance_report.get("status"),
            "scenario_count": acceptance_report.get("scenario_count"),
            "exchange_count": acceptance_report.get("exchange_count"),
            "visible_message_count": acceptance_report.get("visible_message_count"),
            "calibration_agreement": acceptance_report.get("calibration", {}).get("agreement"),
        },
        "provenance_checks": provenance_checks,
        "metamorphic": {
            "cases": metamorphic,
            "all_source_variables_preserved": all(item["source_variables_preserved"] for item in metamorphic),
            "all_hidden_annotations_absent": all(item["hidden_annotations_absent"] for item in metamorphic),
            "live_model_variants_executed": False,
        },
        "status": "passed" if acceptance_report.get("status") == "passed" and all(item["status"] == "passed" for item in provenance_checks) else "failed",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate immutable model-tutoring prompt provenance")
    parser.add_argument("--corpus", type=Path, default=raw.DEFAULT_CORPUS)
    parser.add_argument("--acceptance", type=Path, default=ROOT / "artifacts" / "model-tutoring-all-dsa-acceptance.json")
    parser.add_argument("--plans", type=Path, default=ROOT / "artifacts" / "model-tutoring-all-dsa-plans.jsonl")
    parser.add_argument("--report", type=Path, default=ROOT / "artifacts" / "model-tutoring-prompt-evaluation.json")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    acceptance = json.loads(args.acceptance.read_text(encoding="utf-8"))
    plans = [json.loads(line) for line in args.plans.read_text(encoding="utf-8").splitlines() if line.strip()]
    report = evaluate(raw.load_corpus(args.corpus), acceptance_report=acceptance, plans=plans)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "plans": len(plans), "metamorphic_cases": len(report["metamorphic"]["cases"])}, indent=2))
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
