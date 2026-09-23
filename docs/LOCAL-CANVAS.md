# AutoCompiler Local Canvas

First HTTP prototype of the observable human + AutoCompiler workspace.

## Purpose

The Canvas is not a display of private model reasoning. It exposes operational state: objectives, capability catalog state, branches, user decisions, events and evidence.

## Run

From the repository root:

```powershell
$env:PYTHONPATH = "src"
python -m autocompiler.local_canvas
```

Open:

`http://127.0.0.1:8765`

No external package is required for this first version.

## Current slice

- local HTTP server bound to loopback only;
- real CapabilityCatalog snapshot at `/api/state`;
- visual capability panel;
- objective input;
- three preserved strategy branches (REUSE / ACQUIRE / BUILD);
- observable execution stream.

The buttons currently create local UI events only. They do not execute shell commands, mutate the repository, call AI APIs or promote capabilities.

## Next boundary

Future actions must use explicit event/command contracts and Trust Gate rules before the UI is allowed to request protected mutations.
