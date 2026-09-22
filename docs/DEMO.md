# One-command proof

The fastest current proof of the AutoCompiler core on Windows is:

```powershell
.\RUN-DEMO.ps1
```

or:

```powershell
python demo.py
```

The demo performs a vertical slice in one command:

1. discovers the machine capabilities;
2. asks the planner for Python + durable state;
3. selects providers already available;
4. executes a deterministic recipe;
5. writes `.autocompiler/DEMO_OK.txt`;
6. writes execution state to `.autocompiler/state.db`;
7. reports whether recurring AI was used.

Success is explicit:

```text
=== AUTOCOMPILER DEMO: PASS ===
```

This proves the local discovery → planning → provider selection → recipe execution → persistent state path. It does not yet prove natural-language compilation.
