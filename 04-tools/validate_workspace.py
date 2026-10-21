#!/usr/bin/env python3
"""Dependency-free integrity checks for this static workspace."""
from pathlib import Path
from html import escape
import csv, re, sys
root=Path(__file__).resolve().parents[1]; errors=[]
required_roots=('01-workspace','02-examples','03-templates','04-tools')
for name in required_roots:
    if not (root/name).is_dir(): errors.append(f'missing ordered directory: {name}')
for name in ('workspace','examples','templates','tools'):
    if (root/name).exists(): errors.append(f'legacy unnumbered directory remains: {name}')
sample_footer='Sample report · Illustrative data and fictional participants'
def report_copy(value):
    return re.sub(r'\b[Ss]ynthetic\b\s*', '', value)
topics=list((root/'02-examples').glob('T*-*'))
if len(topics)!=3: errors.append(f'expected 3 example topics, found {len(topics)}')
completed=people=0
for topic in topics:
    for rel in ['research-plan.md','interview-guide.md','topic.html','reports/topic-report.html']:
        if not (topic/rel).is_file(): errors.append(f'missing {topic.name}/{rel}')
    def rows(name):
        with (topic/'data'/name).open(encoding='utf8',newline='') as f:return list(csv.DictReader(f))
    ps,ins,es,fs,acts,vs=map(rows,['participants.csv','interviews.csv','evidence.csv','findings.csv','actions.csv','validations.csv'])
    people+=len(ps); pids={x['participant_id'] for x in ps}; iids={x['interview_id'] for x in ins}; eids={x['evidence_id'] for x in es}; fids={x['finding_id'] for x in fs}; aids={x['action_id'] for x in acts}
    for i in ins:
        if i['participant_id'] not in pids: errors.append(f'{topic.name}: unknown participant {i["participant_id"]}')
        if i['status']=='completed':
            completed+=1
            if not i['actual_at'] or not (topic/i['record_path']).is_file(): errors.append(f'{topic.name}: completed {i["interview_id"]} lacks date/source')
    for e in es:
        if e['interview_id'] not in iids or not (topic/e['source_location'].split('#')[0]).is_file(): errors.append(f'{topic.name}: broken evidence {e["evidence_id"]}')
    for f in fs:
        if any(x not in eids for x in filter(None,f['evidence_ids'].split('|'))): errors.append(f'{topic.name}: broken finding evidence {f["finding_id"]}')
    for a in acts:
        if any(x not in fids for x in filter(None,a['finding_ids'].split('|'))): errors.append(f'{topic.name}: broken action finding {a["action_id"]}')
    for v in vs:
        if v['action_id'] not in aids or v['interview_id'] not in iids: errors.append(f'{topic.name}: broken validation {v["validation_id"]}')
    topic_report=topic/'reports'/'topic-report.html'
    topic_html=topic_report.read_text(encoding='utf8') if topic_report.is_file() else ''
    topic_body=topic_html.split('<footer>',1)[0]
    if topic_html.count(sample_footer)!=1 or re.search(r'\b(?:synthetic|fictional|illustrative)\b', topic_body, re.I):
        errors.append(f'{topic.name}: Topic report sample disclosure is not footer-only')
    for f in fs:
        if f['finding_id'] not in topic_html or escape(f['key_point']) not in topic_html:
            errors.append(f'{topic.name}: finding absent from Topic report {f["finding_id"]}')
    for a in acts:
        expected_status='validated' if a['status']=='validated_synthetic' else a['status'].replace('_',' ')
        if any(escape(a[field]) not in topic_html for field in ('action_id','proposed_solution','owner')) or escape(expected_status) not in topic_html:
            errors.append(f'{topic.name}: action incomplete in Topic report {a["action_id"]}')
    for v in vs:
        if v['validation_id'] not in topic_html or escape(report_copy(v['result'])) not in topic_html:
            errors.append(f'{topic.name}: validation absent from Topic report {v["validation_id"]}')
    expected_reports=set()
    for interview in ins:
        report=topic/'reports'/'individuals'/(interview['participant_id']+'-report.html')
        if interview['status']=='completed':
            expected_reports.add(report)
            content=report.read_text(encoding='utf8') if report.is_file() else ''
            report_body=content.split('<footer>',1)[0]
            if content.count(sample_footer)!=1 or re.search(r'\b(?:synthetic|fictional|illustrative)\b', report_body, re.I):
                errors.append(f'{topic.name}: individual report sample disclosure is not footer-only for {interview["interview_id"]}')
            linked=[e for e in es if e['interview_id']==interview['interview_id']]
            if not content or not linked or any(escape(e['content_summary']) not in content for e in linked):
                errors.append(f'{topic.name}: missing report or recorded quote for {interview["interview_id"]}')
            if interview['interview_id'] not in content:
                errors.append(f'{topic.name}: interview ID absent from individual report {interview["interview_id"]}')
            linked_evidence={e['evidence_id'] for e in linked}
            linked_findings={f['finding_id'] for f in fs if linked_evidence.intersection(f['evidence_ids'].split('|'))}
            linked_actions={a['action_id'] for a in acts if linked_findings.intersection(a['finding_ids'].split('|'))}
            for a in acts:
                present=a['action_id'] in content
                if present != (a['action_id'] in linked_actions):
                    errors.append(f'{topic.name}: action relationship differs in individual report {interview["interview_id"]} / {a["action_id"]}')
            for v in vs:
                if (v['validation_id'] in content) != (v['interview_id']==interview['interview_id']):
                    errors.append(f'{topic.name}: validation relationship differs in individual report {interview["interview_id"]} / {v["validation_id"]}')
        elif report.exists():
            errors.append(f'{topic.name}: report exists for incomplete interview {interview["interview_id"]}')
    actual_reports=set((topic/'reports'/'individuals').glob('*.html'))
    if actual_reports!=expected_reports:
        errors.append(f'{topic.name}: individual report inventory differs from completed interviews')
    for evidence in es:
        if escape(evidence['content_summary']) not in topic_html:
            errors.append(f'{topic.name}: evidence absent from Topic report {evidence["evidence_id"]}')
    if not es and 'No evidence yet' not in topic_html:
        errors.append(f'{topic.name}: empty Topic report lacks no-evidence notice')
if people!=10: errors.append(f'expected 10 participants, found {people}')
if completed!=6: errors.append(f'expected 6 completed interviews, found {completed}')
for area in ('01-workspace','03-templates'):
    for document in (root/area).rglob('*.html'):
        content=document.read_text(encoding='utf8')
        if sample_footer in content or 'Illustrative example' in content:
            errors.append(f'non-example HTML contains a sample-report disclosure: {document.relative_to(root)}')
if errors:
    print('FAILED'); print('\n'.join(errors)); sys.exit(1)
for document in root.rglob('*.html'):
    for href in re.findall(r'href="([^"]+)"', document.read_text(encoding='utf8')):
        if href.startswith(('http:', 'https:', '#')): continue
        target=(document.parent/href.split('#')[0]).resolve()
        if not target.exists(): errors.append(f'broken HTML link: {document.relative_to(root)} -> {href}')
if errors:
    print('FAILED'); print('\n'.join(errors)); sys.exit(1)
print(f'PASSED: {len(topics)} topics, {people} participants, {completed} completed interviews; source relationships, report content, and HTML links checked.')
