#!/usr/bin/env python3
"""Validate real research plus isolated test fixtures without applying release rules."""
import argparse
from html import escape, unescape
from pathlib import Path
import re
import subprocess

from build_reports import load, participant_label

SAMPLE_FOOTER = "Sample report · Illustrative data and fictional participants"


def visible_text(html):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()


def check_name_first(html, label, pairs, errors):
    text = visible_text(html)
    if re.search(r"<h[1-3][^>]*>\s*(?:<[^>]+>\s*)*[TPFEAVI]\d{2,3}\b", html, re.I):
        errors.append(f"{label}: a user-facing heading starts with an internal ID")
    if re.search(r"<th[^>]*>\s*ID\s*</th>", html, re.I):
        errors.append(f"{label}: a table uses ID as a primary column")
    for name, internal_id in pairs:
        if name not in text:
            errors.append(f"{label}: missing reader-facing name '{name}'")
        if internal_id in text and name in text and text.index(internal_id) < text.index(name):
            errors.append(f"{label}: {internal_id} appears before its reader-facing name '{name}'")


def topic_directories(root, area):
    return sorted(path for path in (root / area).glob("T*-*") if path.is_dir())


def warn_if_hosted_remote(root):
    if not (root / ".git").exists():
        return
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True
    )
    remote = result.stdout.strip()
    if result.returncode == 0 and ("github.com" in remote or "gitlab.com" in remote):
        print(
            "WARNING: This working directory is connected to a hosted Git remote. "
            "Daily validation does not make interview notes or participant data safe to publish. "
            "Run 04-tools/check_public_release.py only from a clean release copy."
        )


def validate_topic(topic, sample, errors):
    try:
        data = load(topic)
    except (KeyError, OSError, ValueError) as error:
        errors.append(str(error))
        return 0, 0
    for rel in ("research-plan.md", "interview-guide.md", "topic.html", "reports/topic-report.html"):
        if not (topic / rel).is_file():
            errors.append(f"missing {topic.name}/{rel}")
    topic_report = topic / "reports/topic-report.html"
    topic_html = topic_report.read_text(encoding="utf-8") if topic_report.is_file() else ""
    workspace_html = (topic / "topic.html").read_text(encoding="utf-8") if (topic / "topic.html").is_file() else ""
    topic_body = topic_html.split("<footer>", 1)[0]
    shared_pairs = [
        *[(participant_label(data, participant["participant_id"]), participant["participant_id"]) for participant in data["participants"]],
        *[(finding["key_point"], finding["finding_id"]) for finding in data["findings"]],
        *[(action["key_point"], action["action_id"]) for action in data["actions"]],
    ]
    check_name_first(workspace_html, f"{topic.name}/topic.html", shared_pairs, errors)
    check_name_first(topic_html, f"{topic.name}/reports/topic-report.html", shared_pairs, errors)
    if sample:
        if topic_html.count(SAMPLE_FOOTER) != 1 or re.search(
            r"\b(?:synthetic|fictional|illustrative)\b", topic_body, re.I
        ):
            errors.append(f"{topic.name}: Topic report sample disclosure is not footer-only")
    elif SAMPLE_FOOTER in topic_html:
        errors.append(f"{topic.name}: real Topic report contains a sample disclosure")
    for evidence in data["evidence"]:
        if escape(evidence["content_summary"]) not in topic_html:
            errors.append(f"{topic.name}: evidence absent from Topic report {evidence['evidence_id']}")
    for finding in data["findings"]:
        if finding["finding_id"] not in topic_html or escape(finding["key_point"]) not in topic_html:
            errors.append(f"{topic.name}: finding absent from Topic report {finding['finding_id']}")
    for action in data["actions"]:
        expected_status = "validated" if action["status"] == "validated_synthetic" else action["status"].replace("_", " ")
        if any(escape(action[field]) not in topic_html for field in ("action_id", "proposed_solution", "owner")) or escape(expected_status) not in topic_html:
            errors.append(f"{topic.name}: action incomplete in Topic report {action['action_id']}")
    for validation in data["validations"]:
        result = re.sub(r"\b[Ss]ynthetic\b\s*", "", validation["result"])
        if validation["validation_id"] not in topic_html or escape(result) not in topic_html:
            errors.append(f"{topic.name}: validation absent from Topic report {validation['validation_id']}")
    completed = 0
    expected_reports = set()
    for interview in data["interviews"]:
        report = topic / "reports/individuals" / f"{interview['participant_id']}-report.html"
        if interview["status"] == "completed":
            completed += 1
            expected_reports.add(report)
            content = report.read_text(encoding="utf-8") if report.is_file() else ""
            body = content.split("<footer>", 1)[0]
            report_pairs=[(participant_label(data, interview["participant_id"]), interview["participant_id"])]
            if sample:
                if content.count(SAMPLE_FOOTER) != 1 or re.search(
                    r"\b(?:synthetic|fictional|illustrative)\b", body, re.I
                ):
                    errors.append(f"{topic.name}: individual sample disclosure is not footer-only for {interview['interview_id']}")
            elif SAMPLE_FOOTER in content:
                errors.append(f"{topic.name}: real individual report contains a sample disclosure for {interview['interview_id']}")
            linked = [item for item in data["evidence"] if item["interview_id"] == interview["interview_id"]]
            if not content or not linked or any(escape(item["content_summary"]) not in content for item in linked):
                errors.append(f"{topic.name}: missing report or recorded quote for {interview['interview_id']}")
            if interview["interview_id"] not in content:
                errors.append(f"{topic.name}: interview ID absent from individual report {interview['interview_id']}")
            linked_evidence = {item["evidence_id"] for item in linked}
            linked_findings = {
                finding["finding_id"] for finding in data["findings"]
                if linked_evidence.intersection(finding["evidence_ids"].split("|"))
            }
            linked_actions = {
                action["action_id"] for action in data["actions"]
                if linked_findings.intersection(action["finding_ids"].split("|"))
            }
            report_pairs.extend(
                (finding["key_point"], finding["finding_id"])
                for finding in data["findings"] if finding["finding_id"] in linked_findings
            )
            report_pairs.extend(
                (action["key_point"], action["action_id"])
                for action in data["actions"] if action["action_id"] in linked_actions
            )
            check_name_first(content, f"{topic.name}/{report.name}", report_pairs, errors)
            for action in data["actions"]:
                present = action["action_id"] in content
                if present != (action["action_id"] in linked_actions):
                    errors.append(
                        f"{topic.name}: action relationship differs in individual report "
                        f"{interview['interview_id']} / {action['action_id']}"
                    )
            for validation in data["validations"]:
                present = validation["validation_id"] in content
                if present != (validation["interview_id"] == interview["interview_id"]):
                    errors.append(
                        f"{topic.name}: validation relationship differs in individual report "
                        f"{interview['interview_id']} / {validation['validation_id']}"
                    )
        elif report.exists():
            errors.append(f"{topic.name}: report exists for incomplete interview {interview['interview_id']}")
    report_dir = topic / "reports/individuals"
    actual_reports = set(report_dir.glob("*.html")) if report_dir.is_dir() else set()
    if actual_reports != expected_reports:
        errors.append(f"{topic.name}: individual report inventory differs from completed interviews")
    if not data["evidence"] and "No evidence yet" not in topic_html:
        errors.append(f"{topic.name}: empty Topic report lacks no-evidence notice")
    return len(data["participants"]), completed


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    root = args.root.resolve()
    errors = []
    for name in ("01-workspace", "03-templates", "04-tools", "05-tests"):
        if not (root / name).is_dir():
            errors.append(f"missing ordered directory: {name}")
    if (root / "02-examples").exists():
        errors.append("user-visible 02-examples directory must not be present")
    for name in ("workspace", "examples", "templates", "tools"):
        if (root / name).exists():
            errors.append(f"legacy unnumbered directory remains: {name}")
    fixtures = topic_directories(root, "05-tests/fixtures/research-topics")
    workspace = topic_directories(root, "01-workspace")
    if len(fixtures) != 3:
        errors.append(f"expected 3 isolated research fixtures, found {len(fixtures)}")
    fixture_people = fixture_completed = user_people = user_completed = 0
    for topic in fixtures:
        people, completed = validate_topic(topic, True, errors)
        fixture_people += people
        fixture_completed += completed
    for topic in workspace:
        people, completed = validate_topic(topic, False, errors)
        user_people += people
        user_completed += completed
    dashboard = root / "dashboard.html"
    dashboard_html = dashboard.read_text(encoding="utf-8") if dashboard.is_file() else ""
    dashboard_pairs=[]
    for topic in workspace:
        try:
            data=load(topic)
        except (KeyError,OSError,ValueError):
            continue
        dashboard_pairs.append((data["title"],data["topic_id"]))
    check_name_first(dashboard_html, "dashboard.html", dashboard_pairs, errors)
    if fixture_people != 10:
        errors.append(f"expected 10 fixture participants, found {fixture_people}")
    if fixture_completed != 6:
        errors.append(f"expected 6 completed fixture interviews, found {fixture_completed}")
    if re.search(r"\b(?:Example|Sample report|fictional participants)\b", dashboard_html, re.I):
        errors.append("dashboard.html exposes test-fixture or sample content")
    if not workspace and "Start your first interview Topic" not in dashboard_html:
        errors.append("dashboard.html lacks the first-Topic empty state")
    for document in root.rglob("*.html"):
        text = document.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"]+)"', text):
            if href.startswith(("http:", "https:", "#")):
                continue
            target = (document.parent / href.split("#")[0]).resolve()
            if not target.exists():
                errors.append(f"broken HTML link: {document.relative_to(root)} -> {href}")
    if errors:
        print("FAILED")
        print("\n".join(errors))
        return 1
    print(
        f"PASSED User Workspace Mode: {len(workspace)} user topics / {user_people} participants / "
        f"{user_completed} completed interviews; {len(fixtures)} isolated fixtures / {fixture_people} fixture participants / "
        f"{fixture_completed} completed fixture interviews; source relationships, name-first reports, empty state, and links checked."
    )
    warn_if_hosted_remote(root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
