from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from tools.check_application_contract_inventory import (
    ApplicationContractInventoryFailure,
    check_application_contract_inventory,
    runtime_method_names,
    validate_inventory,
)

ROOT = Path(__file__).resolve().parents[1]
INVENTORY_PATH = ROOT / "contracts" / "application-operation-inventory.v0.1.json"
MCP_CONTRACT_PATH = ROOT / "contracts" / "study-os-mcp-tools.v0.1.json"


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"expected JSON object in {path}")
    return value


class ApplicationContractInventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.inventory = load_json(INVENTORY_PATH)
        self.mcp_contract = load_json(MCP_CONTRACT_PATH)
        self.runtime_methods = runtime_method_names()

    def assert_invalid(self, inventory: dict[str, Any], mcp_contract: dict[str, Any] | None = None) -> None:
        with self.assertRaises(ApplicationContractInventoryFailure):
            validate_inventory(inventory, mcp_contract or self.mcp_contract, self.runtime_methods)

    def test_current_inventory_matches_mcp_and_runtime_boundaries(self) -> None:
        check_application_contract_inventory()

    def test_inventory_phase_must_reflect_partial_implementation(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        mutated["status"] = "pre_implementation"
        self.assert_invalid(mutated)

    def test_missing_mcp_mapping_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        mutated["operations"].pop()
        self.assert_invalid(mutated)

    def test_required_request_field_drift_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        operation = next(item for item in mutated["operations"] if item["mcp_tool"] == "checkpoint")
        operation["required_request_fields"].remove("evidence_ids")
        self.assert_invalid(mutated)

    def test_start_session_optional_field_or_normalization_drift_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        operation = next(item for item in mutated["operations"] if item["mcp_tool"] == "start_session")
        operation["optional_request_fields"].remove("metadata")
        self.assert_invalid(mutated)

        mutated = copy.deepcopy(self.inventory)
        operation = next(item for item in mutated["operations"] if item["mcp_tool"] == "start_session")
        operation["request_normalization"]["metadata"] = "null_is_distinct"
        self.assert_invalid(mutated)

    def test_command_and_idempotency_drift_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        operation = next(item for item in mutated["operations"] if item["mcp_tool"] == "record_assessment")
        operation["kind"] = "query"
        operation["idempotency"] = "not_required"
        self.assert_invalid(mutated)

    def test_missing_runtime_method_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        operation = next(item for item in mutated["operations"] if item["mcp_tool"] == "status")
        operation["current_service_method"] = "invented_status_method"
        self.assert_invalid(mutated)

    def test_early_http_or_transport_authority_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        operation = next(item for item in mutated["operations"] if item["mcp_tool"] == "resume")
        operation["http_exposure"] = "enabled"
        operation["semantic_authority"] = "transport"
        self.assert_invalid(mutated)

    def test_error_vocabulary_drift_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.inventory)
        mutated["error_model"]["categories"].append("frontend_decides")
        self.assert_invalid(mutated)


if __name__ == "__main__":
    unittest.main()
