# Origin and reasoning trail

This project did **not** begin as "build an automation compiler."

It began with a broader question:

> **How can we create our own n8n-like capability using logic and free tools such as GitHub, GitHub Actions, spreadsheets and whatever useful free tools are already available on a computer?**

## 1. Automation before platform

The first abstraction was simple:

```text
event → trigger → condition → action → result → state → next action
```

A visual workflow platform is only one implementation of this logic.

## 2. Existing infrastructure

GitHub already offers repositories, versioning, Actions, webhooks, releases and community. Google offers Sheets, Apps Script and Drive. A normal PC offers files, shell, Python, a browser, local compute and native scheduling.

This changed the question:

> What if we compose existing infrastructure instead of rebuilding every subsystem?

## 3. The computer became first-class

The PC was initially just another runner. That was too narrow.

A computer is a bundle of capabilities:

```text
filesystem + applications + browser + LAN + CPU/GPU + Python + PowerShell + local models + scheduler
```

This suggested routing work by available capabilities rather than by proprietary workflow nodes.

## 4. Escaping platform cost is not enough

If every execution becomes an LLM call, we have merely exchanged one recurring dependency for another.

So another principle emerged:

> **Use AI only where intelligence is actually required.**

Rules, parsers, scripts, APIs, databases and caches should perform deterministic work.

## 5. AI as planner/compiler became a hypothesis

A stronger possibility appeared:

```text
human intent
→ AI helps understand or plan
→ ordinary software executes repeatedly
```

That is where the compiler idea came from. It is an important hypothesis, but it is **not the original problem and not yet the final answer**.

## 6. Avoid creating another mandatory runtime

If our tool must stay in the middle of every execution forever, we risk recreating the lock-in we wanted to escape.

This led to another hypothesis: when possible, generate or configure native/user-owned executors such as PowerShell, Python, Task Scheduler, GitHub Actions, Apps Script or cron/systemd.

## 7. GitHub and Colab changed roles

GitHub became interesting not only as an executor but as distribution, versioning, collaboration, catalog and community.

Colab became interesting as a zero-install playground, but not as durable production infrastructure.

## Current leading direction

```text
intent
→ discover available resources
→ represent requirements
→ choose a sufficient low-cost path
→ generate or compose execution
→ run on native/user-owned resources
```

This remains a hypothesis.

The repository must preserve competing possibilities and experiments so future discoveries can change the architecture without erasing why the project exists.
