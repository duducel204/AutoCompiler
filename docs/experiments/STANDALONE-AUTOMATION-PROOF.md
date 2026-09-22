# Standalone automation proof

This milestone tests a stronger claim than recipe execution: AutoCompiler can **manufacture an automation that no longer depends on AutoCompiler**.

```text
compile once -> generated/ folder -> Python stdlib only -> repeat independently
```

The generated automation watches a configured source on each invocation, copies `.txt` files to a destination, and records every result in its own SQLite `history.db`.

Default Windows proof folders:

- `~/Desktop/AutoCompiler-Inbox`
- `~/Desktop/AutoCompiler-Processados`

Build:

```powershell
python build_standalone_demo.py
```

Then create the input folder/file and run the generated artifact directly:

```powershell
New-Item "$HOME\Desktop\AutoCompiler-Inbox" -ItemType Directory -Force
"PROVA" | Set-Content "$HOME\Desktop\AutoCompiler-Inbox\entrada.txt"
python .\generated\folder-automation\automation.py
```

After compilation, the generated folder can be copied elsewhere. Its execution requires Python's standard library, but does not import or call AutoCompiler and uses no recurring AI.

This milestone deliberately proves runtime independence before native scheduler installation. Scheduling is the next layer, because the earlier real-Windows evidence showed that detected PowerShell does not imply script execution authorization.
