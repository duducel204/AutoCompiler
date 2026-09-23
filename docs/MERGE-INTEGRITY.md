# Merge integrity

AutoCompiler distinguishes **validation** from **enforcement**.

The canonical Trust Gate can prove whether a candidate satisfies repository invariants. GitHub branch governance must separately prevent an unvalidated candidate from entering `main`.

## Observed repository state

Audit through PR #21 found three historical merges with at least one red check: PR #13, PR #14 and PR #18. Their repairs are recorded in `data/pr-validation-ledger.csv`.

PRs #1–#10 predate the modern Trust Gate. Their ledger status means only that all checks available on those exact PR heads were green; it does not claim retroactive execution of today's gate.

The integrated current tree is covered by later successful canonical gates.

## Merge invariant

For every future PR:

1. Freeze the candidate head SHA.
2. Observe the canonical Trust Gate on that exact SHA.
3. Require success before merge.
4. Merge only that SHA.
5. Verify the resulting main state.
6. Record exceptions explicitly; never relabel a red merge as green because a later commit repaired it.

## Enforcement gap

At the time of this audit, GitHub reports `main.protected = false`, required status-check enforcement is off, and the repository has no rulesets. Therefore the Trust Gate is currently a detector, not a server-side merge barrier.

The target repository rule is:

- target: `main`
- require pull request before merging
- require status checks before merging
- required check: final canonical `Trust Gate` job
- require branch to be up to date before merging
- block force pushes and deletion
- do not allow bypass for ordinary merges

Until that rule exists, the repository process must treat a green exact-head Trust Gate as a mandatory human merge precondition.
