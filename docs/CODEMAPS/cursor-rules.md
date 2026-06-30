# Cursor Rules Index

**Last Updated:** 2026-06-30  
**Entry router:** [`.cursorrules`](../../.cursorrules) (short — do not duplicate rule bodies there)

Glob-scoped rules live in [`.cursor/rules/`](../../.cursor/rules/). Cursor auto-loads matching `.mdc` files when you edit paths covered by their globs. This index is the on-demand catalog per [Lecture 04](https://github.com/walkinglabs/learn-harness-engineering/blob/main/docs/en/lectures/lecture-04-why-one-giant-instruction-file-fails/index.md).

## Always Applied

| Rule file | Purpose |
| --- | --- |
| [`dev_workflow.mdc`](../../.cursor/rules/dev_workflow.mdc) | Task Master development workflow |
| [`taskmaster.mdc`](../../.cursor/rules/taskmaster.mdc) | Task Master MCP tools and CLI reference |
| [`self_improve.mdc`](../../.cursor/rules/self_improve.mdc) | When and how to add or update rules |
| [`cursor_rules.mdc`](../../.cursor/rules/cursor_rules.mdc) | Required structure for new `.mdc` rule files |

## Agent-Requestable (read when the task needs them)

| Rule file | Apply when |
| --- | --- |
| [`database-integration.mdc`](../../.cursor/rules/database-integration.mdc) | Database operations, queries, auth + DB integration |
| [`robshocks-react-component-rules.mdc`](../../.cursor/rules/robshocks-react-component-rules.mdc) | Creating or refactoring React components |
| [`commit-messages.mdc`](../../.cursor/rules/commit-messages.mdc) | Writing git commit messages |
| [`project-mangement-document-creation.mdc`](../../.cursor/rules/project-mangement-document-creation.mdc) | Creating project management documents |
| [`install-shadcn.mdc`](../../.cursor/rules/install-shadcn.mdc) | Installing or adding shadcn components |

## Deprecated — Do Not Follow

These rules target Clerk/Next.js patterns from another project. This repo uses **JWT + Vite + FastAPI**. Ignore them (see hard constraint #10 in `.cursorrules`).

| Rule file | Why deprecated |
| --- | --- |
| [`clerk-setup-refactoring-maintenance.mdc`](../../.cursor/rules/clerk-setup-refactoring-maintenance.mdc) | Clerk auth / Next.js middleware |
| [`file-folder-component-creation.mdc`](../../.cursor/rules/file-folder-component-creation.mdc) | Next.js `src/` layout conventions |

## Layer Patterns (codemaps, not `.mdc` yet)

Project-specific backend, frontend, execution, and integration patterns live in codemaps until dedicated scoped rules are added:

| When editing | Read |
| --- | --- |
| `backend/**/*.py` | [backend.md](./backend.md) |
| `frontend/src/**/*.{ts,tsx}` | [frontend.md](./frontend.md) |
| Tier / execution / xpath services | [execution-engine.md](./execution-engine.md) + [ADR-002](../../documentation/ADR-002-test-execution-engine.md) |
| Models, crud, migrations | [database.md](./database.md) |
| ReqIQ proxy, Hermes, Stagehand | [integrations.md](./integrations.md) |

## Adding a New Rule

1. **Repo-wide hard constraint** → add to `.cursorrules` (keep ≤15 items).
2. **Path-scoped pattern** → new `.cursor/rules/<name>.mdc` with `globs` + `description`; add a row here.
3. **Architecture map** → update the relevant `docs/CODEMAPS/*.md`.
4. **ADR-level decision** → `documentation/ADR-*.md`.

Each rule needs **source** (why), **applicability** (when), and **expiry** (when to remove). See [`self_improve.mdc`](../../.cursor/rules/self_improve.mdc).
