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

AI may revise candidate IR, but cannot authorize or apply persistent machine changes. A separate session-scoped **Ações locais** control can explicitly expose a narrow browser allowlist to Gemini function calling. Enabling it requires user confirmation and authorization; it does not expose shell, PowerShell, filesystem mutation or arbitrary process execution. See D-025 in [DECISIONS.md](DECISIONS.md).

## Readiness limits

The Basic catalog exposes the ten-workflow local Ready Pack (W-01 through W-05 and W-11 through W-15). Engine coverage is separate: [BASIC_1_0_COVERAGE.md](BASIC_1_0_COVERAGE.md). Visual editing and green tests do not replace real onboarding, authenticated integration or release demonstrations.

Implementation: `src/autocompiler/local_canvas.py`, `first_run.py`, `workflow_lifecycle.py`, `assistant_chat.py`, `templates.py` and `web/local-canvas/index.html`.


## Installed workflow lifecycle

Applied workflows are registered outside the replaceable app payload and remain visible after the Canvas is reopened.

- `GET /api/installations`: list active/ready/disabled installed workflows.
- `GET /api/installations/history?id=...`: inspect independent artifact run history.
- `POST /api/installations/run`: execute/trigger an installed workflow on demand with explicit action authorization.
- `POST /api/installations/disable`: disable an installed workflow; scheduled workflows disable the native Windows task.
- `POST /api/installations/enable`: re-enable an installed workflow.
- `POST /api/installations/remove`: remove the AutoCompiler-owned deployment and generated artifact.

The Canvas home renders these under **Neste computador**. Deterministic artifacts continue to run independently of the Canvas.

## Gemini assistant connection

The Basic assistant no longer treats “API key received” as “AI connected”. `/api/assistant/configure` performs a minimal Gemini `generateContent` probe first. Only a successful provider response marks the assistant connected. Public diagnostics distinguish authentication, permission, quota, model, network and timeout errors without returning the secret key.


## Assistant local browser actions

The assistant can optionally translate explicit natural-language commands into a small set of Gemini function calls. The user must enable **Ações locais** for the current process session before any function can execute.

Current allowlist:

- `browser_open`: launch the detected installed browser;
- `browser_search`: open a Google search for the exact requested query;
- `browser_navigate`: open an explicit `http` or `https` URL.

The executor validates the selected function and its arguments after the model response. Unknown functions are rejected. `file:`, `javascript:`, shell-like schemes and credential-bearing URLs are rejected. The model never receives a generic shell/process tool.

This is **not full browser/RPA automation**. It proves the semantic path `natural language → Gemini functionCall → AutoCompiler allowlist → local execution`. DOM-level click/type/read actions remain a later capability and should use the installed browser extension/native bridge rather than blind keystroke injection.
