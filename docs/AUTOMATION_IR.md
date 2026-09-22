# Automation IR — Draft 0.1

The IR is the project's most important interface. It separates intent understanding from execution technology.

## Design goals

- human-readable YAML/JSON;
- schema-validatable;
- target-neutral where possible;
- explicit permissions;
- explicit AI use;
- explicit state requirements;
- compilable to multiple targets.

## Draft shape

```yaml
version: "0.1"
name: example

description: Example automation

trigger:
  type: schedule
  every: day
  at: "19:00"

capabilities:
  filesystem:
    read: ["~/Documents/**"]
    write: ["D:/Backup/**"]
  network:
    allow: []

steps:
  - id: sync
    action: filesystem.sync
    from: "~/Documents"
    to: "D:/Backup"

state:
  type: local

policy:
  prefer:
    - deterministic
    - local
  ai_runtime: forbidden
  paid_cloud: avoid
```

## Key distinction

The IR describes **what is required**, not the implementation details of a specific platform. A compiler may map the same `schedule` trigger to Windows Task Scheduler, GitHub cron, Apps Script trigger or systemd timer.
