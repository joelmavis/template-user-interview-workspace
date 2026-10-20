# QA Checklist and Current Results

**Assessment date:** 2026-10-20  
**Repository test environment:** local macOS Work runtime, Python 3, static files served over `http://127.0.0.1` for browser checks  
**Owner-observed environment:** puppyone Desktop; screenshots and owner report supplied outside this runtime

Status meanings: **Passed** = verified in the stated environment; **Partially Tested** = useful but incomplete evidence; **Failed** = observed defect in the workspace; **Not Tested** = no adequate evidence; **Known Product Limitation** = observed outside the template and still open.

| Check | Status | Environment and evidence |
|---|---|---|
| Source schema, required files, and ID references | Passed | `python3 tools/validate_workspace.py` checked required columns, source paths, and interview → evidence → finding → action → validation references on 2026-10-20. |
| Example inventory | Passed | Validator reported 3 Topics, 10 participants, and 6 completed interviews. File inventory contains 3 Topic reports and 6 individual reports. |
| Report regeneration | Passed | `python3 tools/build_reports.py` reported: “Refreshed 3 Topic reports and 6 individual reports; source relationships checked.” |
| Report content and evidence boundaries | Passed | Validator checked attributed quotations, findings, actions, validation results, and relative links. Individual reports label participant evidence separately from broader Topic context. |
| T01 example research loop | Passed | Source records and reports connect F001 → A001 → V001. Each example report carries one concise sample-data statement in its footer. |
| T02 finding support | Passed | F001 concerns first-step clarity and stays within E001–E002; it does not claim unrecorded workaround behavior. |
| T03 no-data state | Passed | Topic report states that recruitment has not produced evidence, findings, actions, or validation. No individual reports are generated. |
| Static relative links in files | Passed | Repository validator resolved local HTML and source-file targets. |
| Relative links in a normal browser | Passed | Served locally over HTTP and exercised in the Work runtime browser on 2026-10-20; dashboard-to-Topic and report navigation worked. |
| Offline / no-CDN report rendering | Passed | Generated report HTML contains inline CSS and no external scripts, fonts, images, or stylesheets. |
| Small-screen wrapping and long text | Passed | Reports use responsive grids and `overflow-wrap`; browser inspection found no horizontal overflow at the tested viewport. |
| Special characters and dates | Passed | UTF-8 declarations are present; generated update stamps use `UTC+08:00`, source interview times retain `UTC+0800`, and curly apostrophes and quotation marks rendered in the normal browser test. |
| puppyone Desktop HTML rendering | Partially Tested | Owner-provided screenshots/report say the dashboard, Topic Workspace, and report HTML render. This runtime did not independently launch puppyone Desktop. |
| puppyone Desktop link navigation | Known Product Limitation | Owner reports that clicking links in Desktop preview fails while the same links work in an external browser. Open files from the folder tree or use an external browser. This is not claimed as fixed. |
| Creating a new Topic and follow-on agent step | Partially Tested | Owner reports initial success creating a Topic and using an additional agent for a later step. The full workflow and all handoff rules were not independently exercised here. |
| Codex + Claude Code end-to-end handoff | Not Tested | No documented run in both named clients covers the complete research loop. |
| Independent non-developer usability test | Not Tested | No observed participant has completed the workflow unaided. |

## Maintainer regression flow

Work on a disposable copy. Create a Topic from `templates/topic-template`, add only supplied participant data and notes, extract evidence, review a finding, propose an action, obtain explicit approval, record a validation, regenerate reports, and run `python3 tools/validate_workspace.py`. Record the environment, date, result, and any limitation in `HANDOFF.md`.

