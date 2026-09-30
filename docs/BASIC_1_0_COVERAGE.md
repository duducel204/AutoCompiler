# Basic 1.0 Coverage Matrix

| Primitive | Status | Evidence / Benchmark |
|---|---|---|
| `schema_version` | FULL | Schema 0.3 frozen in `schemas/automation-ir.schema.json` |
| `trigger` | FULL | Manual, schedule, webhook |
| `get / check` | FULL | `get`, `check` primitives supported |
| `transform` | FULL | `data.map`, `transform` primitives |
| `IF / ELSE / SWITCH` | FULL | `flow.condition`, `flow.branch`, `if_else`, `switch` |
| `foreach` | FULL | `foreach` collection iteration primitive |
| `act` | FULL | `filesystem.copy`, `act` primitives |
| `state` | FULL | `state.record`, `state` persistence |
| `wait / continue` | FULL | `wait` primitive |
| `notify` | FULL | `notify` primitive |
| `error_policy` | FULL | `retry`, `timeout`, `fallback` primitives |
| `variables` | FULL | Scoped workflow variables and data references |
