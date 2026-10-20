# Technical Notes — Capability Boundaries

## Verified in this release candidate

- Generated reports are static HTML with inline CSS and relative local links; they do not require a CDN or external network resource.
- `tools/build_reports.py` regenerates Topic and individual reports from Markdown and CSV sources and checks source relationships before writing.
- `tools/validate_workspace.py` checks source structure, IDs, demo counts, report content, and local link targets.
- Relative navigation works when the folder is served to a normal web browser over local HTTP.

## puppyone Desktop observation

The owner reports, with screenshots, that puppyone Desktop renders `dashboard.html`, Topic pages, and report HTML. Clicking links inside the Desktop HTML preview currently fails, even though the same relative links work in an external browser. Treat this as an open product limitation. Open the target file from the folder tree or use an external browser; do not describe in-app navigation as working.

This Work runtime did not independently launch puppyone Desktop, so the rendering statement above is owner-provided evidence rather than an independent pass.

## Agent workflow evidence

The owner reports preliminary success creating a new Topic and using an additional agent for a follow-on step. That does not establish a complete Codex + Claude Code handoff across planning, collection, analysis, approval, validation, and reporting. Full named-client integration and an independent non-developer usability run remain untested.

## Design boundary

Shared files enable collaboration; they do not provide automatic agent scheduling, locking, or concurrent transaction safety. Coordinate writers through `HANDOFF.md` and use explicit human approval before an action changes from proposed to adopted.

If Python is unavailable, an agent may carefully update affected static HTML and must record the manual refresh and its limitations in `HANDOFF.md`. End users are not expected to run Python during normal operation.

