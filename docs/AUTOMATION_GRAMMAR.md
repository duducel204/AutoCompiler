# Automation Grammar Specification

This document defines the provider-neutral grammar for AutoCompiler workflows.

## Primitives

1. **trigger**: Initiates workflow execution (schedule, webhook, manual, event).
2. **get / check**: Retrieves data or evaluates system status.
3. **transform**: Pure data transformation or mapping.
4. **IF / ELSE / SWITCH**: Conditional branching logic.
5. **foreach**: Iteration over collections.
6. **act**: Action execution with side effects.
7. **state**: Durable state persistence.
8. **wait / continue**: Delays or signal-based resumption.
9. **notify**: Alert or notification delivery.
10. **error policy / retry / timeout / fallback**: Resiliency and error handling constructs.
11. **variables & data references**: Scoped workflow variables and expressions.

## Canonical Workflows

- **`W-01` (Instant Workflow)**: Manual or webhook trigger → get data → transform → act → notify.
- **`W-10` (Persistent Workflow)**: Scheduled trigger → check state → foreach item → transform → act → update state → error policy (retry/fallback).
