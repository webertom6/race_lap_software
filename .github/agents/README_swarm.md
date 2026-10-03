# generic-swarm

Reusable `swarm` agents for OpenCode and GitHub Copilot. The workflow uses one
planner, one implementation worker, and an optional simplifier.

## Agents

`swarm` plans the work, inspects the repository, defines the implementation
scope, and delegates one task to `swarm-worker`. It does not edit code.

`swarm-worker` implements the assigned change, related tests, and required
documentation. It reports its changes and focused verification to `swarm`.

`swarm-code-simplifier` makes one behavior-preserving cleanup pass after a
non-trivial implementation. It reports possible behavioral issues instead of
changing them.

`swarm` accepts or rejects the worker's result, requests corrections when
needed, and makes the final `COMPLETE`, `REPLAN`, or `BLOCKED` decision.

## Adopt it

1. Copy `.opencode/` into a project that uses OpenCode, or copy `.github/` into
   a project that uses GitHub Copilot.
2. Ask your agents to adapt the copied instructions to the project's existing
   conventions, skills, verification commands, and code-generation workflow.

The agents expect the target project to provide its own root `AGENTS.md` with
repository instructions and verification requirements.

## Models

Use a strong reasoning model for `swarm`. Claude Sonnet 5.0, Claude Opus 5.5 (seems to be at level of Fable 5.1 but 40% cheaper), and GPT-6 Sol (always choose GPT-6 family or higher for whatever model at openAI, better and cheaper) are good choices for planning, judgment, and
acceptance decisions.

Use a strong coding model for `swarm-worker`. It performs the implementation
and verification work.

Use a smaller careful model for `swarm-code-simplifier`. Its work is limited to
behavior-preserving cleanup of changed files.