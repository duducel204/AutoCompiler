import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from src.autocompiler.compiler import analyze_compile_support, compile_ir


class TestCompilerCapabilityBinding(unittest.TestCase):
    def setUp(self):
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp_dir.name)

    def tearDown(self):
        self.tmp_dir.cleanup()

    def _create_mock_executable(self, name: str, script_content: str) -> Path:
        file_path = self.root / name
        if sys.platform == "win32" and not name.endswith(".cmd") and not name.endswith(".exe"):
            file_path = self.root / f"{name}.cmd"
            # Windows batch script wrapper calling sys.executable
            py_script = self.root / f"{name}_inner.py"
            py_script.write_text(script_content, encoding="utf-8")
            file_path.write_text(f'@echo off\n"{sys.executable}" "{py_script}" %*\n', encoding="utf-8")
        else:
            # POSIX executable script
            file_path.write_text(f"#!{sys.executable}\n" + script_content, encoding="utf-8")
            file_path.chmod(file_path.stat().st_mode | stat.S_IXUSR)
        return file_path

    def test_binding_missing_returns_compile_support_false(self):
        ir = {
            "schema_version": "0.3",
            "name": "test-missing-binding",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "format_step",
                    "skill": "act",
                    "with": {
                        "capability": "custom.formatter",
                        "args": ["hello"],
                    },
                }
            ],
        }
        resolved_execution = {
            "schema_version": "0.1",
            "target": "python-sqlite",
            "requirements": [
                {
                    "capability": "custom.formatter",
                    "provider": "portable-formatter",
                    "status": "resolved",
                    "binding": None,
                }
            ],
        }

        support = analyze_compile_support(ir, "python-sqlite", resolved_execution)
        self.assertFalse(support["supported"])
        mismatches = support["provider_mismatches"]
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["capability"], "custom.formatter")
        self.assertEqual(mismatches[0]["reason"], "missing_executable_binding")

    def test_binding_invalid_executable_returns_compile_support_false(self):
        ir = {
            "schema_version": "0.3",
            "name": "test-invalid-executable",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "format_step",
                    "skill": "act",
                    "with": {
                        "capability": "custom.formatter",
                        "args": ["hello"],
                    },
                }
            ],
        }
        non_existent_path = str(self.root / "non_existent_executable.exe")
        resolved_execution = {
            "schema_version": "0.1",
            "target": "python-sqlite",
            "requirements": [
                {
                    "capability": "custom.formatter",
                    "provider": "portable-formatter",
                    "status": "resolved",
                    "binding": {
                        "executable": non_existent_path,
                    },
                }
            ],
        }

        support = analyze_compile_support(ir, "python-sqlite", resolved_execution)
        self.assertFalse(support["supported"])
        mismatches = support["provider_mismatches"]
        self.assertEqual(len(mismatches), 1)
        self.assertEqual(mismatches[0]["capability"], "custom.formatter")
        self.assertEqual(mismatches[0]["reason"], "binding_executable_not_found")

    def test_valid_executable_binding_returns_compile_support_true(self):
        exe = self._create_mock_executable(
            "formatter",
            "import sys, json\nprint(json.dumps({'formatted': sys.argv[1].upper()}))\n",
        )
        ir = {
            "schema_version": "0.3",
            "name": "test-valid-executable",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "format_step",
                    "skill": "act",
                    "with": {
                        "capability": "custom.formatter",
                        "args": ["hello"],
                    },
                }
            ],
        }
        resolved_execution = {
            "schema_version": "0.1",
            "target": "python-sqlite",
            "requirements": [
                {
                    "capability": "custom.formatter",
                    "provider": "portable-formatter",
                    "status": "resolved",
                    "binding": {
                        "executable": str(exe),
                    },
                }
            ],
        }

        support = analyze_compile_support(ir, "python-sqlite", resolved_execution)
        self.assertTrue(support["supported"])

    def test_artifact_executes_portable_provider_stdout_result_in_context_no_autocompiler_runtime(self):
        exe = self._create_mock_executable(
            "portable_formatter",
            "import sys, json\nval = sys.argv[1] if len(sys.argv) > 1 else ''\nprint(json.dumps({'status': 'ok', 'result': f'FORMATTED:{val}'}))\n",
        )
        ir = {
            "schema_version": "0.3",
            "name": "test-execution-flow",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "format_step",
                    "skill": "act",
                    "with": {
                        "capability": "custom.formatter",
                        "args": ["hello_world"],
                    },
                }
            ],
        }
        resolved_execution = {
            "schema_version": "0.1",
            "target": "python-sqlite",
            "requirements": [
                {
                    "capability": "custom.formatter",
                    "provider": "portable-formatter",
                    "status": "resolved",
                    "binding": {
                        "executable": str(exe),
                    },
                }
            ],
        }

        out_dir = self.root / "compiled_artifact"
        manifest = compile_ir(ir, "python-sqlite", out_dir, resolved_execution=resolved_execution)
        self.assertFalse(manifest["recurring_ai_required"])
        self.assertFalse(manifest["autocompiler_required_after_compile"])

        # Check compiled python artifact does not import autocompiler
        script_path = out_dir / "automation.py"
        script_code = script_path.read_text(encoding="utf-8").lower()
        self.assertNotIn("import autocompiler", script_code)
        self.assertNotIn("from autocompiler", script_code)

        # Run generated artifact
        proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, check=True)
        result = json.loads(proc.stdout)

        self.assertTrue(result["ok"])
        self.assertFalse(result["autocompiler_runtime_used"])
        self.assertFalse(result["recurring_ai_used"])

        step_context = result["context"]["format_step"]
        self.assertEqual(step_context, {"status": "ok", "result": "FORMATTED:hello_world"})

    def test_multiple_arbitrary_capabilities_use_same_mechanism(self):
        exe1 = self._create_mock_executable(
            "uppercase_provider",
            "import sys, json\nprint(json.dumps({'upper': sys.argv[1].upper()}))\n",
        )
        exe2 = self._create_mock_executable(
            "calculator_provider",
            "import sys, json\na, b = int(sys.argv[1]), int(sys.argv[2])\nprint(json.dumps({'sum': a + b}))\n",
        )

        ir = {
            "schema_version": "0.3",
            "name": "test-multi-capability",
            "trigger": {"type": "manual"},
            "steps": [
                {
                    "id": "step_up",
                    "skill": "act",
                    "with": {
                        "capability": "text.uppercase",
                        "args": ["sample_text"],
                    },
                },
                {
                    "id": "step_calc",
                    "skill": "act",
                    "with": {
                        "capability": "math.add",
                        "args": [10, 20],
                    },
                },
            ],
        }
        resolved_execution = {
            "schema_version": "0.1",
            "target": "python-json",
            "requirements": [
                {
                    "capability": "text.uppercase",
                    "provider": "text-upper-tool",
                    "status": "resolved",
                    "binding": {
                        "executable": str(exe1),
                    },
                },
                {
                    "capability": "math.add",
                    "provider": "math-add-tool",
                    "status": "resolved",
                    "binding": {
                        "executable": str(exe2),
                    },
                },
            ],
        }

        out_dir = self.root / "compiled_multi"
        support = analyze_compile_support(ir, "python-json", resolved_execution)
        self.assertTrue(support["supported"])

        compile_ir(ir, "python-json", out_dir, resolved_execution=resolved_execution)
        script_path = out_dir / "automation.py"

        proc = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, check=True)
        result = json.loads(proc.stdout)

        self.assertTrue(result["ok"])
        self.assertEqual(result["context"]["step_up"], {"upper": "SAMPLE_TEXT"})
        self.assertEqual(result["context"]["step_calc"], {"sum": 30})


if __name__ == "__main__":
    unittest.main()
