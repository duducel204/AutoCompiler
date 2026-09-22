# Principles

1. **Deterministic before probabilistic.** Use parsers, APIs, rules, scripts and caches before LLM inference.
2. **Local before paid cloud.** Prefer user-owned compute when it is reliable and appropriate.
3. **Native before proprietary runtime.** Generate artifacts standard tools can execute.
4. **AI as compiler, repair tool or exception handler.** Do not make inference the default loop.
5. **Permissions before execution.** Filesystem, network, shell and secrets access should be visible before installation/run.
6. **Structured state before prose drift.** Project state and automation definitions should have machine-readable sources.
7. **Portability before convenience lock-in.** Generated artifacts should be inspectable and exportable.
8. **Small universal primitives before hundreds of integrations.** Filesystem, shell, Python, HTTP, browser and AI cover a large initial surface.
9. **Cost is a planning dimension.** Runtime choice should consider money, latency, privacy and reliability.
10. **The compiler should be removable.** Where feasible, uninstalling AutoCompiler must not break generated automations.
