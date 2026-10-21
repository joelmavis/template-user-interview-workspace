# Release Status — User Interview Workspace v1.0

**Published:** 2026-10-20  
**Repository:** https://github.com/joelmavis/template-user-interview-workspace  
**Default branch:** `main`  
**License:** MIT

## Final package review

| Area | Result | Notes |
|---|---|---|
| Product name and copy | Ready | User-facing copy uses **User Interview Workspace** and avoids template-brand marketing language or unsupported claims. |
| Example / real-data separation | Ready | `02-examples/` contains clearly identified sample research. `01-workspace/` is empty in the public repository and protected by `.gitignore`. |
| Data and report consistency | Ready | 3 Topics, 10 participants, 6 completed interviews, 3 Topic reports, and 6 individual reports pass the repository validator. |
| README and non-developer onboarding | Ready | Quick Start, report guidance, privacy boundaries, maintainer commands, and the known Desktop limitation are documented. |
| Agent workflow | Ready | `AGENTS.md`, `CLAUDE.md`, `PLAYBOOK.md`, and `HANDOFF.md` define roles, evidence rules, approvals, and handoffs. |
| Secrets, personal records, and machine paths | Ready | The pre-publication scan found no embedded credentials, real client records, or absolute developer-machine paths. |
| Temporary/runtime artifacts | Ready | Local metadata and Python cache files were removed and are ignored. |
| External assets and dependencies | Ready | No copied third-party assets or external report dependencies were found. |
| License | Ready | The repository includes an MIT `LICENSE`. |
| Git repository | Ready | Public GitHub repository on `main`; local branch tracks `origin/main`. |
| Desktop in-app navigation | Known product limitation | puppyone Desktop renders HTML according to owner evidence, but clicked links do not navigate in preview. External-browser navigation works. |
| Full multi-client / non-developer testing | Open | Complete Codex + Claude Code and independent non-developer usability runs are not evidenced. |

## Validation commands

```sh
python3 04-tools/build_reports.py
python3 04-tools/validate_workspace.py
```

Latest result:

```text
Refreshed 3 Topic reports and 6 individual reports; source relationships checked.
PASSED: 3 topics, 10 participants, 6 completed interviews; source relationships, report content, and HTML links checked.
```

## Repository metadata

**GitHub About**  
A ready-to-use workspace for planning user interviews, tracing evidence into findings, tracking approved actions, and recording follow-up validation with file-based AI agents.

**Suggested topics**  
`user-research`, `user-interviews`, `research-ops`, `qualitative-research`, `ai-agents`, `markdown`, `csv`, `static-html`

**Templates listing description**  
Plan interviews, keep source notes and evidence connected, turn findings into accountable actions, and track follow-up validation in one local workspace.

## Remaining handoff

Send the repository URL to the colleague responsible for the website Templates catalog. No website listing submission was performed from this workspace.

