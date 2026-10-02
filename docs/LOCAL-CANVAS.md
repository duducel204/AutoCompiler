# AutoCompiler Local Canvas

## Current implementation — 2026-10-02

The local HTTP workspace includes Basic utilities, optional AI-assisted draft development, and a horizontal Builder Canvas. It exposes operational state and automation drafts, not private model reasoning.

## Run

From a repository checkout with Python available:

```powershell
$env:PYTHONPATH = "src"
python -m autocompiler.local_canvas
```

Open `http://127.0.0.1:8765`. The default binds to loopback. This developer launch does not prove one-package Windows onboarding.

## Available flows

- `/api/state` and `/api/workspace`: capability/workspace snapshots.
- `/api/preflight`: read-only Windows assessment and preparation plan; `/api/preflight/authorize` and `/api/preflight/apply`: authorize and prepare.
- `/api/templates`, `/api/utilities`, `/api/templates/instantiate`: readiness catalog and draft creation.
- `/api/workflow/validate`, `/api/workflow/load`, `/api/workflow/save`: draft validation and storage.
- `/api/workflow/plan`, `/api/workflow/authorize`, `/api/workflow/apply`: explicit plan, consent, compilation/execution and verification.
- `/api/ai/draft` and `/api/assistant/*`: optional build-time AI drafting and conversation.
- `/api/acquisition/git` and `/api/acquisition/git/apply`: implemented acquisition inspection/application flow.

Buttons now invoke backend operations with real effects. The earlier UI-only description is obsolete. Direct `/api/workflow/compile_and_run` is rejected with `authorization_required`; application follows the stored-plan lifecycle.

## Authorization and credentials

`WorkflowPlanStore` and `MachinePreparationStore` retain plans and authorization in process memory; applied plans are marked consumed. Workflow application checks consent and verifies artifacts, authorized IR and execution results.

This is a local single-user server. Plan authorization represents consent to a change, not an account login or OAuth implementation. The endpoints do not establish authenticated multi-user/network deployment support.

Optional Gemini credentials can be configured through `/api/assistant/configure` or `AUTOCOMPILER_CHAT_API_KEY`, with provider/model environment settings. Session configuration stays in process memory; status responses do not expose the key. `/api/assistant/clear` clears in-memory configuration; environment-provided credentials remain available until removed from the process environment. Backend provider requests send the key over HTTPS in `x-goog-api-key`.

AI may revise candidate IR, but cannot authorize or apply machine changes. See D-025 in [DECISIONS.md](DECISIONS.md).

## Readiness limits

The Basic catalog marks PDF organization ready and W-02 through W-05 in validation. Engine coverage is separate: [BASIC_1_0_COVERAGE.md](BASIC_1_0_COVERAGE.md). Visual editing and green tests do not replace real onboarding, authenticated integration or release demonstrations.

Implementation: `src/autocompiler/local_canvas.py`, `first_run.py`, `workflow_lifecycle.py`, `assistant_chat.py`, `templates.py` and `web/local-canvas/index.html`.
