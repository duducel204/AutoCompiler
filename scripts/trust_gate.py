from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.autocompiler.trust import classify_failure, report
TESTS=[
 "tests.test_discover",
 "tests.test_planner_runtime",
 "tests.test_intent",
 "tests.test_standalone",
 "tests.test_ir_compiler",
 "tests.test_b2_b3",
 "tests.test_environment_resolution",
 "tests.test_windows_base",
 "tests.test_windows_provisioner",
 "tests.test_first_run",
 "tests.test_trust_architecture",
 "tests.test_real_provisioning_vertical",
 "tests.test_external_provider_e030",
 "tests.test_capability_catalog",
 "tests.test_capability_contracts",
 "tests.test_local_canvas",
 "tests.test_workspace",
 "tests.test_git_acquisition",
 "tests.test_canvas_protocol",
 "tests.test_canvas_bridge",
 "tests.test_canvas_projector",
 "tests.test_whatsapp_automation",
 "tests.test_vault_provider",
 "tests.test_canonical_capabilities",
 "tests.test_capability_closure",
 "tests.test_capability_closure_service",
 "tests.test_workflow_capability_resume",
 "tests.test_local_canvas_capability_resume",
 "tests.test_compiler_capability_binding",
 "tests.test_state_dedup",
 "tests.test_reliability",
 "tests.test_coverage_w01_w05",
 "tests.test_templates",
 "tests.test_ai_draft",
 "tests.test_assistant_chat",
 "tests.test_assistant_actions",
 "tests.test_gemini_client",
 "tests.test_workflow_lifecycle",
 "tests.test_workflow_installations",
 "tests.test_ay_core",
 "tests.test_ay_scripts",
 "tests.test_node_context_index",
 "tests.test_node_context_spider",
 "tests.test_capability_closure_e2e",
 "tests.test_repo_contract_diff",
 "tests.test_ay_cycle_state",
]

def run(cmd):
    p=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
    return p.returncode,p.stdout+"\n"+p.stderr

def main():
    evidence=[]
    for module in TESTS:
        code,log=run([sys.executable,"-m","unittest",module,"-v"])
        evidence.append({"check":module,"ok":code==0})
        if code:
            failure=classify_failure(log)
            print(json.dumps({"gate":"FAIL","check":module,"failure":report(failure)},indent=2))
            print(log[-8000:],file=sys.stderr)
            return 1
    code,log=run([sys.executable,"build_b1.py"])
    evidence.append({"check":"build_b1","ok":code==0})
    if code:
        failure=classify_failure(log)
        print(json.dumps({"gate":"FAIL","check":"build_b1","failure":report(failure)},indent=2))
        print(log[-8000:],file=sys.stderr)
        return 1
    print(json.dumps({"gate":"PASS","contract":"restore invariants, never manufacture green","checks":evidence},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
