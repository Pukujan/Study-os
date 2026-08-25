from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INVENTORY = ROOT / "contracts" / "application-operation-inventory.v0.1.json"
DEFAULT_MCP_CONTRACT = ROOT / "contracts" / "study-os-mcp-tools.v0.1.json"
DEFAULT_RUNTIME_SOURCES = (
    ROOT / "src" / "study_os" / "services" / "runtime.py",
    ROOT / "src" / "study_os" / "services" / "runtime_base.py",
)


class ApplicationContractInventoryFailure(RuntimeError):
    pass


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ApplicationContractInventoryFailure(f"{path} must contain a JSON object")
    return value


def runtime_method_names(paths: tuple[Path, ...] = DEFAULT_RUNTIME_SOURCES) -> set[str]:
    names: set[str] = set()
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                names.add(node.name)
    return names


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ApplicationContractInventoryFailure(message)


def _require_string_list(value: object, label: str) -> list[str]:
    _require(isinstance(value, list), f"{label} must be a list")
    result = list(value)
    _require(all(isinstance(item, str) for item in result), f"{label} must contain only strings")
    return result


def validate_inventory(
    inventory: dict[str, Any],
    mcp_contract: dict[str, Any],
    runtime_methods: set[str],
) -> None:
    _require(inventory.get("inventory_version") == "0.1.0", "inventory_version must remain 0.1.0")
    _require(
        inventory.get("status") == "partial_implementation",
        "application contract inventory must reflect the current partial E11a implementation",
    )

    planned = inventory.get("planned_application_contract")
    _require(isinstance(planned, dict), "planned_application_contract must be an object")
    _require(planned.get("version") == inventory.get("inventory_version"), "planned application version must match inventory version")
    _require(planned.get("canonical_authoring") == "python_pydantic_v2_models", "canonical authoring decision drifted")
    _require(planned.get("canonical_package") == "study_os.application.contracts", "canonical package decision drifted")
    projections = set(_require_string_list(planned.get("generated_projections"), "generated_projections"))
    _require(
        projections == {"json_schema", "openapi_later", "typescript_client_later"},
        "generated projections must remain canonical-schema-first with OpenAPI/TypeScript deferred",
    )
    _require(planned.get("domain_depends_on_contract_library") is False, "domain must not depend on the application contract library")
    _require(planned.get("http_implementation_status") == "deferred", "HTTP implementation must remain deferred")
    _require(planned.get("frontend_implementation_status") == "deferred", "frontend implementation must remain deferred")

    versioning = inventory.get("versioning")
    _require(isinstance(versioning, dict), "versioning must be an object")
    _require(versioning.get("application_contract_version_is_independent") is True, "application contract version must remain independent")
    _require(versioning.get("compatible_same_major_default") == "additive_response_fields_only", "same-major compatibility policy drifted")
    _require(versioning.get("breaking_change_requires_major_version") is True, "breaking changes must require a major version")
    _require(versioning.get("field_semantics_may_not_be_silently_reused") is True, "field semantics may not be silently reused")
    _require(versioning.get("deprecation_requires_removal_plan") is True, "deprecations require a removal plan")
    _require(versioning.get("request_unknown_fields") == "reject_unless_explicit_extension_point", "request unknown-field policy drifted")
    _require(versioning.get("response_unknown_fields") == "clients_may_ignore_additive_same_major_fields", "response unknown-field policy drifted")

    serialization = inventory.get("serialization")
    _require(isinstance(serialization, dict), "serialization must be an object")
    _require(serialization.get("encoding") == "utf-8-json", "application JSON encoding decision drifted")
    _require(serialization.get("timestamps") == "rfc3339-utc-z", "timestamp serialization decision drifted")
    _require(serialization.get("identifiers") == "opaque_strings", "identifier policy drifted")
    _require(serialization.get("non_finite_numbers") == "forbidden", "non-finite numbers must remain forbidden")
    _require(serialization.get("null_and_absent_are_distinct") is True, "null and absent must remain distinct by default")
    _require(
        serialization.get("operation_specific_normalization_must_be_explicit") is True,
        "operation-specific compatibility normalization must be explicit",
    )
    _require(
        serialization.get("canonical_hash_serialization") == "sorted_keys_compact_json_when_fingerprinting",
        "idempotency fingerprint serialization decision drifted",
    )

    error_model = inventory.get("error_model")
    _require(isinstance(error_model, dict), "error_model must be an object")
    _require(error_model.get("envelope") == "application_error_envelope", "application error envelope decision drifted")
    contract_error_categories = _require_string_list(mcp_contract.get("error_categories"), "MCP error_categories")
    inventory_error_categories = _require_string_list(error_model.get("categories"), "inventory error categories")
    _require(inventory_error_categories == contract_error_categories, "application error categories must match the durable MCP/runtime vocabulary")
    _require(error_model.get("safe_public_detail_only") is True, "errors must expose safe public detail only")
    _require(error_model.get("transport_status_is_not_semantic_authority") is True, "transport status must not own semantic authority")

    privacy = inventory.get("client_privacy_boundary")
    _require(isinstance(privacy, dict), "client_privacy_boundary must be an object")
    forbidden_fields = set(_require_string_list(privacy.get("forbidden_fields"), "client forbidden_fields"))
    _require(
        {"raw_private_evidence", "private_transcript_body", "secret", "credential", "hidden_holdout_answer"} <= forbidden_fields,
        "client privacy boundary is missing a required forbidden field class",
    )
    _require(privacy.get("frontend_semantic_authority") is False, "frontend must not gain semantic authority")
    _require(privacy.get("transport_semantic_authority") is False, "transport must not gain semantic authority")

    mcp_tools = mcp_contract.get("tools")
    operations = inventory.get("operations")
    _require(isinstance(mcp_tools, list), "MCP tools must be a list")
    _require(isinstance(operations, list), "inventory operations must be a list")
    _require(len(operations) == len(mcp_tools) == 13, "inventory must map exactly the existing 13 MCP tools")

    mcp_by_name: dict[str, dict[str, Any]] = {}
    for raw_tool in mcp_tools:
        _require(isinstance(raw_tool, dict), "every MCP tool entry must be an object")
        name = raw_tool.get("name")
        _require(isinstance(name, str) and name, "every MCP tool must have a name")
        _require(name not in mcp_by_name, f"duplicate MCP tool {name}")
        mcp_by_name[name] = raw_tool

    seen_mcp: set[str] = set()
    seen_application: set[str] = set()
    for raw_operation in operations:
        _require(isinstance(raw_operation, dict), "every application inventory operation must be an object")
        mcp_tool = raw_operation.get("mcp_tool")
        application_operation = raw_operation.get("application_operation")
        service_method = raw_operation.get("current_service_method")
        _require(isinstance(mcp_tool, str) and mcp_tool in mcp_by_name, f"unknown MCP mapping {mcp_tool!r}")
        _require(mcp_tool not in seen_mcp, f"duplicate application mapping for MCP tool {mcp_tool}")
        seen_mcp.add(mcp_tool)
        _require(isinstance(application_operation, str) and application_operation, f"{mcp_tool}: application_operation is required")
        _require(application_operation not in seen_application, f"duplicate application operation {application_operation}")
        seen_application.add(application_operation)
        _require(isinstance(service_method, str) and service_method in runtime_methods, f"{mcp_tool}: mapped runtime method {service_method!r} does not exist")

        contract_tool = mcp_by_name[mcp_tool]
        mutating = contract_tool.get("mutating") is True
        expected_kind = "command" if mutating else "query"
        expected_idempotency = "required" if contract_tool.get("idempotency_required") is True else "not_required"
        _require(raw_operation.get("kind") == expected_kind, f"{mcp_tool}: command/query classification drifted")
        _require(raw_operation.get("idempotency") == expected_idempotency, f"{mcp_tool}: idempotency classification drifted")
        required_request_fields = _require_string_list(raw_operation.get("required_request_fields"), f"{mcp_tool} required_request_fields")
        _require(
            required_request_fields == _require_string_list(contract_tool.get("required_input"), f"{mcp_tool} MCP required_input"),
            f"{mcp_tool}: required request fields drifted from MCP contract",
        )
        optional_request_fields = _require_string_list(raw_operation.get("optional_request_fields", []), f"{mcp_tool} optional_request_fields")
        _require(
            not (set(required_request_fields) & set(optional_request_fields)),
            f"{mcp_tool}: request fields cannot be both required and optional",
        )
        _require(
            _require_string_list(raw_operation.get("required_result_fields"), f"{mcp_tool} required_result_fields")
            == _require_string_list(contract_tool.get("required_output"), f"{mcp_tool} MCP required_output"),
            f"{mcp_tool}: required result fields drifted from MCP contract",
        )
        if mcp_tool == "start_session":
            _require(
                optional_request_fields == ["source_client", "metadata"],
                "start_session optional compatibility fields drifted",
            )
            normalization = raw_operation.get("request_normalization")
            _require(isinstance(normalization, dict), "start_session request_normalization must be an object")
            _require(
                normalization.get("source_client") == "absent_or_null_to_null",
                "start_session source_client normalization drifted",
            )
            _require(
                normalization.get("metadata")
                == "absent_or_null_to_empty_object_before_runtime_idempotency_fingerprint",
                "start_session metadata normalization drifted",
            )
        persistence_effect = raw_operation.get("persistence_effect")
        _require(isinstance(persistence_effect, str) and persistence_effect, f"{mcp_tool}: persistence_effect is required")
        if mutating:
            _require(persistence_effect != "none", f"{mcp_tool}: durable command must declare its persistence effect")
        else:
            _require(persistence_effect == "none", f"{mcp_tool}: query must not declare a persistence effect")
        _require(isinstance(raw_operation.get("evidence_requirement"), str) and raw_operation["evidence_requirement"], f"{mcp_tool}: evidence_requirement is required")
        _require(isinstance(raw_operation.get("observable_transition"), str) and raw_operation["observable_transition"], f"{mcp_tool}: observable_transition is required")
        _require(raw_operation.get("semantic_authority") == "application", f"{mcp_tool}: semantic authority must remain application")
        _require(raw_operation.get("error_policy") == error_model.get("envelope"), f"{mcp_tool}: error policy drifted")
        _require(raw_operation.get("http_exposure") == "deferred", f"{mcp_tool}: HTTP exposure must remain deferred")

    _require(seen_mcp == set(mcp_by_name), "application inventory does not map the exact MCP tool set")


def check_application_contract_inventory(
    inventory_path: Path = DEFAULT_INVENTORY,
    mcp_contract_path: Path = DEFAULT_MCP_CONTRACT,
    runtime_sources: tuple[Path, ...] = DEFAULT_RUNTIME_SOURCES,
) -> None:
    validate_inventory(
        _load_json(inventory_path),
        _load_json(mcp_contract_path),
        runtime_method_names(runtime_sources),
    )


def main() -> int:
    check_application_contract_inventory()
    print("Study OS application contract inventory checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
