# Research Topic Playbook

## 1. Create and agree
Start from either the user's natural-language research goal or readable local files. Pasted URLs are not a separate input mode. Planner records the decision problem, scope, participant criteria, method, sample rationale, dates, and explicit user confirmation in `research-plan.md`. Prepare open questions in `interview-guide.md`; wait for approval before using it.

## 2. Coordinate
Coordinator adds participants and planned dates. `planned_at` is an intention; `actual_at` is only filled after the interview. New rounds create new interview rows.

## 3. Document source material
Turn notes supplied by the user into one Markdown record per session. Keep quotations, observations, and summary distinct. No supplied notes means no completed interview and no report.

## 4. Synthesize evidence
Analyst makes Evidence IDs tied to a source location, then creates Findings with limits and conflicting evidence. A small sample can indicate a pattern, never population proof.

## 5. Review and act
Propose actions with rationale, owner, due date, status and linked findings. Reviewer verifies sources. Only record `user_confirmed=yes` after the user approves.

## 6. Validate and learn
Record validation plan, actual date, result and follow-up need. Mark solved, partially solved, or needs more research—not a success without a result. Refresh reports and state the next question.

## Completion conditions

A Topic is complete only when its evidence is traceable, each action has an owner/status, validation is recorded or explicitly pending, limitations are visible, and reports reflect the latest confirmed data. HTML should lead with Topic names, participant aliases, finding titles, evidence content and action names; IDs remain secondary traceability details.

## Validation modes

During normal research, regenerate reports and run `python3 04-tools/validate_workspace.py`. It validates every real Topic under `01-workspace/` and uses isolated fixtures under `05-tests/` for regression coverage; populated research is expected.

`python3 04-tools/check_public_release.py` is only for preparing the blank public template. Run it from a clean release copy, not after each user edit. Its blank-workspace requirement must never be satisfied by deleting interviews, evidence, findings, actions, or validation records from a user's workspace.
