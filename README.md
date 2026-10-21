# User Interview Workspace

## Folder order

- `01-workspace/` — private research created by the user.
- `02-examples/` — three complete illustrative Topics.
- `03-templates/` — the clean Topic starter.
- `04-tools/` — report generation and validation utilities.

User Interview Workspace is a ready-to-use workflow for planning interviews, preserving source notes, turning evidence into findings, tracking approved actions, and recording follow-up validation. It is designed for non-developers working with compatible file-based agents.

## Quick Start

1. Open this folder in puppyone Desktop, then open `dashboard.html`.
2. Tell an agent what you want to learn in your own words, for example: “Help me create a Topic about the checkout experience and prepare an interview guide.”
3. Review the research plan and questions before any participant or interview data is added.
4. Give the agent your confirmed notes. Review proposed findings and explicitly approve any action before it is treated as adopted.
5. Ask the agent to refresh the reports, then read the Topic and individual reports from the dashboard.

You do not need to edit CSV files or run Python during normal use.

## What you will see

- **Home Dashboard** — an overview of the three example Topics and their current stages.
- **Topic Workspace** — participant progress, findings, actions, next steps, and report links for one study.
- **Individual Interview Report** — one participant’s date, background, recorded question and answer, verbatim evidence, interpretation, recommendation, related Topic context, and follow-up status.
- **Topic Research Report** — the full cross-participant analysis, detailed findings, proposed solutions, owners, execution status, and validation results.

Markdown files preserve the original plans, notes, and detailed research sources. CSV files hold structured status and references. Generated HTML provides the readable view.

## Start a new Topic through agent chat

Ask an agent to copy `03-templates/topic-template/` into `01-workspace/`, assign the next Topic ID, and guide you one decision at a time. The agent should read `AGENTS.md`, `PLAYBOOK.md`, and the latest relevant entry in `HANDOFF.md` before editing. It must not invent participants, quotations, findings, actions, or outcomes.

Agents share files; they do not automatically schedule one another or safely edit the same CSV at the same time. Let one writer finish and record a handoff before another edits shared data.

## Example research and private work

`02-examples/` contains three complete sample research Topics. Example report footers identify the data and participants as illustrative; the names, interviews, actions, and outcomes are not real user feedback.

Put real research only in `01-workspace/`. The repository ignores working material inside that folder while retaining its empty placeholder, which reduces the risk of accidentally committing private notes. Before sharing any copy, still inspect it for names, contact details, transcripts, credentials, and client information.

## Reading and refreshing reports

Open [Home Dashboard](dashboard.html), choose a Topic, then open its Topic or individual report. Reports are designed to stand alone; linked Markdown remains the evidence source for detailed review.

When confirmed source data changes, ask an agent: “Regenerate the reports and run the workspace validation.” Agents can use:

```sh
python3 04-tools/build_reports.py
python3 04-tools/validate_workspace.py
```

These are maintainer and agent commands, not end-user setup steps.

## Known limitation

Owner testing confirms that puppyone Desktop renders the dashboard, Topic pages, and reports, but links clicked inside its HTML preview currently do not navigate. The same relative links work in an external browser. Until the Desktop product issue is resolved, open the target file from the folder tree or use an external browser. See `QA_CHECKLIST.md` for the evidence boundary.

## More guidance

- [Research workflow](PLAYBOOK.md)
- [Current QA results](QA_CHECKLIST.md)
- [Technical capability notes](TECHNICAL_NOTES.md)
- [Agent coordination rules](AGENTS.md)

