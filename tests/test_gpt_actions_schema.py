import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_gpt_actions_schema", ROOT / "tools" / "generate_gpt_actions_schema.py")
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class GPTActionsSchemaTests(unittest.TestCase):
    def test_schema_is_derived_from_the_exact_mcp_tool_surface(self):
        schema = MODULE.build_schema("https://study-os.example.test")
        contract = json.loads((ROOT / "contracts" / "study-os-mcp-tools.v0.1.json").read_text(encoding="utf-8"))
        expected = {f"/actions/{tool['name']}" for tool in contract["tools"]}
        self.assertEqual(set(schema["paths"]), expected)
        self.assertEqual(schema["x-study-os-mcp-contract-version"], "0.1.0")
        for tool in contract["tools"]:
            operation = schema["paths"][f"/actions/{tool['name']}"]["post"]
            self.assertEqual(operation["operationId"], f"study_os_{tool['name']}")
            request = operation["requestBody"]["content"]["application/json"]["schema"]
            self.assertEqual(request.get("required", []), tool["required_input"])
        event_request = schema["paths"]["/actions/record_learning_event"]["post"]["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(event_request["properties"]["payload"]["type"], "string")
        self.assertIn("JSON-encoded object", event_request["properties"]["payload"]["description"])


if __name__ == "__main__":
    unittest.main()
