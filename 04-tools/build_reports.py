#!/usr/bin/env python3
"""Regenerate user-facing reports and isolated fixture reports."""
from datetime import datetime
from html import escape
from pathlib import Path
import csv
import os
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CSS = '''<style>:root{--ink:#1d2a40;--muted:#58667b;--line:#dce3eb;--blue:#2455b5;--bg:#f5f7fa}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.62 system-ui,-apple-system,Segoe UI,sans-serif;overflow-wrap:anywhere}main{max-width:960px;margin:auto;padding:32px 22px 72px}h1{font-size:clamp(30px,5vw,42px);line-height:1.15;margin:5px 0 12px}h2{font-size:23px;margin:0 0 17px}h3{font-size:18px;margin:0 0 8px}p{margin:0 0 14px}a{color:var(--blue);text-underline-offset:2px}.eyebrow{color:var(--blue);font-size:12px;font-weight:750;letter-spacing:.1em;text-transform:uppercase}.lead{font-size:18px}.nav{display:flex;flex-wrap:wrap;gap:15px;margin:20px 0 28px}.nav a{font-weight:650}section{background:white;border:1px solid var(--line);border-radius:12px;padding:23px;margin:18px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(195px,1fr));gap:12px}.card{border:1px solid var(--line);border-radius:10px;padding:17px;margin:14px 0;background:white}.fact{background:#f2f6fc;padding:12px;border-radius:8px}.label{display:block;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}.record-id{display:block;color:var(--muted);font-size:12px;font-weight:500;margin-top:2px}.pill{display:inline-block;background:#e9f0ff;color:#204798;border-radius:999px;padding:3px 10px;font-size:13px;font-weight:700}.pill.draft{background:#fff1d9;color:#8d5900}.pill.empty{background:#edf0f3;color:#566172}.quote{border-left:3px solid var(--blue);padding:6px 0 6px 17px;margin:12px 0;font-size:17px}.muted{color:var(--muted)}ul{padding-left:22px;margin:9px 0}li{margin:6px 0}footer{color:var(--muted);font-size:13px;margin-top:30px}@media(max-width:600px){main{padding:20px 13px 55px}section{padding:18px}}</style>'''
DASHBOARD_CSS = '''<style>:root{--ink:#172033;--muted:#65708a;--line:#dce3ed;--bg:#f6f8fb;--card:#fff;--blue:#265bd6;--good:#167a48;--warn:#a25d00}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif;overflow-wrap:anywhere}main{max-width:1120px;margin:auto;padding:34px 24px 70px}h1{font-size:32px;line-height:1.15;margin:8px 0}h2{margin-top:34px}h3{margin:0 0 8px}.eyebrow{color:var(--blue);font-weight:700;text-transform:uppercase;letter-spacing:.08em;font-size:12px}.notice{border-left:4px solid var(--blue);background:#edf3ff;padding:12px 16px;border-radius:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:14px}.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px;box-shadow:0 1px 2px #1720330b}.metric{font-size:30px;font-weight:750}.muted{color:var(--muted)}.record-id{display:block;color:var(--muted);font-size:12px;font-weight:500;margin-top:2px}table{width:100%;border-collapse:collapse;background:#fff;border:1px solid var(--line)}th,td{text-align:left;vertical-align:top;padding:10px;border-bottom:1px solid var(--line)}th{background:#edf2f8;font-size:13px}a{color:var(--blue);font-weight:600}.tag{display:inline-block;border-radius:999px;padding:2px 8px;background:#e8efff;color:#1947aa;font-size:12px;font-weight:700}.ok{background:#e1f5e9;color:var(--good)}.wait{background:#fff1db;color:var(--warn)}.noevidence{background:#f1f3f6;color:#566070}code{background:#edf1f6;padding:1px 4px}footer{margin-top:40px;color:var(--muted);font-size:13px}@media(max-width:600px){main{padding:22px 14px 54px}.table-wrap{overflow-x:auto}}</style>'''

def e(value): return escape(str(value), quote=True)
def rows(topic, name):
    with (topic/'data'/name).open(newline='', encoding='utf-8') as f: return list(csv.DictReader(f))
def md(path):
    out, key, buf = {}, 'intro', []
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('## '): out[key]='\n'.join(buf).strip(); key=line[3:].lower(); buf=[]
        else: buf.append(line)
    out[key]='\n'.join(buf).strip()
    return out
def session_notes(topic, interview):
    note=md(topic/interview['record_path'])
    return (note['relevant guide question'],note['analyst interpretation'],note['opportunity'])
def record_id(kind, value): return f'<span class="record-id">Internal {e(kind)} ID: {e(value)}</span>'
def href(from_directory, target): return Path(os.path.relpath(target, from_directory)).as_posix()
def participant_label(d, participant_id):
    person=d['people'][participant_id]; alias=person['alias'].strip() or 'Participant'
    matches=[p for p in d['participants'] if (p['alias'].strip() or 'Participant').casefold()==alias.casefold()]
    if len(matches)==1: return alias
    profile=person['profile'].strip()
    same_profile=[p for p in matches if p['profile'].strip().casefold()==profile.casefold()]
    if profile and len(same_profile)==1: return f'{alias} · {profile}'
    ordinal=matches.index(person)+1
    return f'{alias} · {profile or "Participant"} {ordinal}'
def para(value, d=None):
    if d: value=humanize_text(value,d)
    return ''.join(f'<p>{e(block)}</p>' for block in re.split(r'\n\s*\n',value) if block.strip())
def date(value):
    if not value: return 'Not recorded'
    try: return datetime.fromisoformat(value).strftime('%d %B %Y, %H:%M UTC%z' if 'T' in value else '%d %B %Y')
    except ValueError: return value
def pill(value):
    value='validated' if value=='validated_synthetic' else value
    cls = ' draft' if value in ('draft','proposed','scheduled') else ' empty' if value in ('recruiting','not_scheduled') else ''
    return f'<span class="pill{cls}">{e(value.replace("_"," "))}</span>'
def humanize_text(value,d):
    """Replace internal record references in reader-facing prose with meaningful names."""
    replacements={d['topic_id']:d['title']}
    replacements.update({pid:participant_label(d,pid) for pid in d['people']})
    replacements.update({fid:f['key_point'] for fid,f in d['finding_by_id'].items()})
    replacements.update({aid:a['key_point'] for aid,a in d['action_by_id'].items()})
    for iid,i in d['sessions'].items():
        person=d['people'].get(i['participant_id'],{})
        replacements[iid]=f"{participant_label(d,i['participant_id'])} interview"
    for eid,x in d['evidence_by_id'].items():
        i=d['sessions'].get(x['interview_id'],{})
        person=d['people'].get(i.get('participant_id',''),{})
        replacements[eid]=f"recorded evidence from {participant_label(d,i['participant_id']) if i else 'the participant'}"
    validation_actions={}
    for v in d['validations']:
        action=d['action_by_id'].get(v['action_id'],{})
        validation_actions[v['validation_id']]=action.get('key_point','the action')
        replacements[v['validation_id']]=f"follow-up for {action.get('key_point','the action')}"
    text=str(value)
    for validation_id,action_name in validation_actions.items():
        text=re.sub(rf'\b{re.escape(validation_id)}\s+follow-up\b',f'follow-up for {action_name}',text)
    for internal_id,label in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        text=re.sub(rf'\b{re.escape(internal_id)}\b',label,text)
    return text
def plan_status(d):
    match=re.search(r'Status:\s*([^·\n]+)',d['plan'].get('intro',''),re.I)
    return match.group(1).strip() if match else 'In progress'
def clean_report_copy(body):
    body=body.replace('This small, illustrative sample is chosen to demonstrate workflow coverage—not to estimate a population. Dates and findings are synthetic.','This small sample is not intended to estimate a population.')
    body=body.replace('This material must never be presented as real user research.','')
    body=body.replace('it is illustrative only and not a production outcome.','it is not a production outcome.')
    body=re.sub(r'\bare synthetic,\s*', '', body, flags=re.I)
    body=re.sub(r'\bis illustrative and\s+', '', body, flags=re.I)
    body=re.sub(r'\bsynthetic preparation data\b', 'preparation data', body, flags=re.I)
    body=re.sub(r'\bsynthetic notes\b', 'brief notes', body, flags=re.I)
    body=re.sub(r'\b[Ss]ynthetic\b\s*', '', body)
    body=re.sub(r'\b[Ff]ictional\b\s*', '', body)
    body=re.sub(r'\bbrief\s+brief\b', 'brief', body, flags=re.I)
    body=body.replace('Approved in example','Approval recorded')
    body=re.sub(r'\s+,', ',', body)
    return re.sub(r' {2,}', ' ', body)
def page(title, body, sample):
    body=clean_report_copy(body)
    footer = 'Sample report · Illustrative data and fictional participants' if sample else 'User Interview Workspace · Research report'
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>{CSS}<main>{body}<footer>{footer}</footer></main></html>\n'

def load(topic):
    d={name:rows(topic,name+'.csv') for name in ('participants','interviews','evidence','findings','actions','validations')}
    d['people']={p['participant_id']:p for p in d['participants']}
    d['sessions']={i['interview_id']:i for i in d['interviews']}
    d['evidence_by_id']={x['evidence_id']:x for x in d['evidence']}
    d['finding_by_id']={x['finding_id']:x for x in d['findings']}
    d['action_by_id']={x['action_id']:x for x in d['actions']}
    d['topic_id']=topic.name.split('-')[0]
    d['plan']=md(topic/'research-plan.md')
    d['synthesis']=md(topic/'analysis'/'synthesis.md')
    d['title']=(topic/'research-plan.md').read_text(encoding='utf-8').splitlines()[0][2:].split(' — ')[0]
    errors=[]
    for key, table in [('people','participants'),('sessions','interviews'),('evidence_by_id','evidence'),('finding_by_id','findings'),('action_by_id','actions')]:
        if len(d[key])!=len(d[table]): errors.append(f'duplicate ID in {table}')
    for i in d['interviews']:
        iid=i['interview_id']
        if i['participant_id'] not in d['people'] or i['topic_id']!=d['topic_id']: errors.append(f'{iid}: participant or Topic mismatch')
        if i['status']=='completed':
            if not i['actual_at'] or not i['record_path'] or not (topic/i['record_path']).is_file(): errors.append(f'{iid}: missing actual date or note')
            try:
                prompt, interpretation, opportunity=session_notes(topic,i)
                if not all((prompt,interpretation,opportunity)) or prompt not in (topic/'interview-guide.md').read_text(encoding='utf-8'):
                    errors.append(f'{iid}: missing analysis or unmatched guide question')
            except (KeyError,OSError): errors.append(f'{iid}: missing bounded analysis in source note')
        elif i['actual_at'] or i['record_path']: errors.append(f'{iid}: incomplete session has a completed record')
    for x in d['evidence']:
        i=d['sessions'].get(x['interview_id']); source=x['source_location'].split('#')[0]
        if not i or i['status']!='completed' or i['record_path']!=source: errors.append(f'{x["evidence_id"]}: interview/source mismatch')
        elif x['content_summary'] not in (topic/source).read_text(encoding='utf-8'): errors.append(f'{x["evidence_id"]}: quote absent from note')
    for f in d['findings']:
        path=topic/f['detail_path']
        if not path.is_file() or f['key_point'] not in path.read_text(encoding='utf-8').splitlines()[0]: errors.append(f'{f["finding_id"]}: explanation/title mismatch')
        for eid in filter(None,f['evidence_ids'].split('|')):
            if eid not in d['evidence_by_id']: errors.append(f'{f["finding_id"]}: unknown {eid}')
    for a in d['actions']:
        for fid in filter(None,a['finding_ids'].split('|')):
            if fid not in d['finding_by_id']: errors.append(f'{a["action_id"]}: unknown {fid}')
        if a['user_confirmed']=='no' and a['status']!='proposed': errors.append(f'{a["action_id"]}: unapproved status')
    for v in d['validations']:
        if v['action_id'] not in d['action_by_id'] or v['interview_id'] not in d['sessions']: errors.append(f'{v["validation_id"]}: action/interview mismatch')
        if v['completed_at'] and not v['result']: errors.append(f'{v["validation_id"]}: missing result')
    if errors: raise ValueError(topic.name+': '+'; '.join(errors))
    return d

def evidence_card(x,d,prefix):
    i=d['sessions'][x['interview_id']]; person=d['people'][i['participant_id']]
    return f'<div class="card"><span class="label">{e(participant_label(d,i["participant_id"]))} · {e(date(i["actual_at"]))} · Recorded evidence</span><blockquote class="quote">{e(x["content_summary"])}</blockquote><p class="muted"><a href="{prefix}{e(i["record_path"])}">Original interview note</a></p>{record_id("evidence",x["evidence_id"])}</div>'

def individual(topic,d,i,sample):
    person=d['people'][i['participant_id']]; iid=i['interview_id']; prompt,reading,opportunity=session_notes(topic,i)
    evidence=[x for x in d['evidence'] if x['interview_id']==iid]; ids={x['evidence_id'] for x in evidence}
    findings=[f for f in d['findings'] if ids.intersection(f['evidence_ids'].split('|'))]; fids={f['finding_id'] for f in findings}
    actions=[a for a in d['actions'] if fids.intersection(a['finding_ids'].split('|'))]
    validations=[v for v in d['validations'] if v['interview_id']==iid]
    quotes=''.join(evidence_card(x,d,'../../') for x in evidence)
    broader=''.join(f'<div class="card"><h3>{e(f["key_point"])}</h3>{record_id("finding",f["finding_id"])}<p><strong>This participant’s contribution.</strong> The recorded statement shown above is part of the evidence for this finding.</p><p><strong>Broader context.</strong> This Topic finding also draws on other linked interviews; those participants’ views are presented in the Topic report.</p><p><a href="../topic-report.html#{e(f["finding_id"])}">Read the broader finding in the Topic Research Report</a></p></div>' for f in findings) or '<p>This interview is not yet linked to a Topic finding.</p>'
    solutions=''.join(f'<div class="card"><h3>{e(a["key_point"])}</h3>{record_id("action",a["action_id"])}<p><strong>Proposed solution.</strong> {e(a["proposed_solution"])}</p><p><strong>Why it appears here.</strong> This Topic-level proposal responds to a broader finding that includes this participant’s evidence. It is an analyst recommendation, not the participant’s requested design.</p><p><strong>Owner.</strong> {e(a["owner"])} · <strong>Due.</strong> {e(date(a["due_date"]))} · <strong>Priority.</strong> {e(a["priority"])} · <strong>Status.</strong> {pill(a["status"])} · <strong>Approval recorded.</strong> {e(a["user_confirmed"])}</p></div>' for a in actions) or '<p>No Topic-level action is connected to this participant’s evidence.</p>'
    followup=''.join(f'<div class="card"><h3>Follow-up: {e(d["action_by_id"][v["action_id"]]["key_point"])}</h3>{record_id("validation",v["validation_id"])}{record_id("action",v["action_id"])}<p><strong>Participant.</strong> {e(participant_label(d,i["participant_id"]))} · {e(date(i["actual_at"]))}</p><p><strong>Method and date.</strong> {e(v["planned_method"])} · {e(date(v["completed_at"] or v["planned_at"]))}</p><p><strong>Recorded result.</strong> {e(v["result"] or "Pending")}</p><p><strong>Further follow-up.</strong> {e(v["followup_needed"])} · {e(humanize_text(v["next_step"],d))}</p>{record_id("interview",iid)}</div>' for v in validations) or '<p>No follow-up or validation result is recorded for this participant.</p>'
    display_name=participant_label(d,i['participant_id'])
    body=f'''<p class="eyebrow">Individual Interview Report</p><h1>{e(display_name)}</h1><p class="lead">{e(d['title'])} · Source-linked interview record.</p><nav class="nav"><a href="../topic-report.html">{e(d['title'])} Topic Report</a><a href="../../topic.html">{e(d['title'])} Workspace</a><a href="../../{e(i['record_path'])}">{e(display_name)} interview note</a></nav>
    <section><h2>Interview overview</h2><div class="grid"><div class="fact"><span class="label">Interview date</span>{e(date(i['actual_at']))}</div><div class="fact"><span class="label">Background</span>{e(person['profile'])}</div><div class="fact"><span class="label">Method</span>{e(i['method'])}</div><div class="fact"><span class="label">Interview status</span>{pill(i['status'])}{record_id("interview",iid)}</div></div></section>
    <section><h2>Executive Summary</h2><p>{e(reading)}</p><p><strong>Research recommendation.</strong> {e(opportunity)}</p></section>
    <section><h2>Key question and recorded response</h2><p><strong>Relevant guide question:</strong> “{e(prompt)}”</p><p class="muted">The note does not record the exact question asked or a full Q&amp;A transcript. The statement below is verbatim from the source.</p>{quotes}</section>
    <section><h2>Participant evidence and interpretation</h2><p><strong>Evidence.</strong> The participant’s recorded statement appears above.</p><p><strong>Interpretation.</strong> {e(reading)}</p><p><strong>Recommendation.</strong> {e(opportunity)}</p></section>
    <section><h2>Related Topic Findings / Broader Context</h2>{broader}</section>
    <section><h2>Related proposed solutions and ownership</h2>{solutions}</section><section><h2>Participant follow-up and validation</h2>{followup}</section>
    <section><h2>Research Limitations</h2><p>The source is one brief interview note rather than a complete transcript. The report does not add an unrecorded question, behavior, or outcome. Broader findings, actions, and validation states come from the linked Topic records.</p></section>'''
    return page(display_name+' | Individual Interview Report',body,sample)

def topic_report(topic,d,sample):
    done=[i for i in d['interviews'] if i['status']=='completed']; pending=[i for i in d['interviews'] if i['status']!='completed']
    syn=d['synthesis']; plan=d['plan']
    people=''.join(f'<li><a href="individuals/{e(i["participant_id"])}-report.html">{e(participant_label(d,i["participant_id"]))} · {e(date(i["actual_at"]))}</a></li>' for i in done) or '<li>No completed interviews or individual reports.</li>'
    upcoming=''.join(f'<li>{e(participant_label(d,i["participant_id"]))} · {e(i["status"].replace("_"," "))} · {e(date(i["planned_at"]))}</li>' for i in pending) or '<li>No initial interviews pending.</li>'
    finding_html=''
    for f in d['findings']:
        sections=md(topic/f['detail_path']); quotes=''.join(evidence_card(d['evidence_by_id'][eid],d,'../') for eid in f['evidence_ids'].split('|') if eid)
        finding_html+=f'<article class="card" id="{e(f["finding_id"])}"><h3>{e(f["key_point"])}</h3>{record_id("finding",f["finding_id"])}<p><strong>Detailed explanation.</strong> {e(sections.get("detailed explanation",""))}</p><p><strong>Recorded evidence.</strong></p>{quotes}<p><strong>Interpretation and potential impact.</strong> {e(sections.get("interpretation and potential impact",sections.get("interpretation","")))}</p><p><strong>Limit.</strong> {e(f["evidence_limitations"])} · <strong>Status.</strong> {pill(f["status"])}</p><p><a href="../{e(f["detail_path"])}">Finding source: {e(f["key_point"])}</a></p></article>'
    if not finding_html: finding_html='<p><strong>No evidence yet.</strong> There are no completed interviews or research findings.</p>'
    action_html=''
    for a in d['actions']:
        refs=', '.join(f'<a href="#{e(fid)}">{e(d["finding_by_id"][fid]["key_point"])}</a>' for fid in a['finding_ids'].split('|') if fid)
        rationale=md(topic/a['rationale_detail_path']).get('intro','').splitlines()[-1]
        action_html+=f'<article class="card"><h3>{e(a["key_point"])}</h3>{record_id("action",a["action_id"])}<p><strong>Proposed solution.</strong> {e(a["proposed_solution"])}</p><p><strong>Rationale and evidence.</strong> This addresses {refs}; the recorded statements and limits appear above. {e(humanize_text(rationale,d))}</p><div class="grid"><div class="fact"><span class="label">Owner</span>{e(a["owner"])}</div><div class="fact"><span class="label">Priority / due date</span>{e(a["priority"])} · {e(date(a["due_date"]))}</div><div class="fact"><span class="label">Execution status</span>{pill(a["status"])}</div><div class="fact"><span class="label">Approval recorded</span>{e(a["user_confirmed"])}</div></div><p><a href="../{e(a["rationale_detail_path"])}">Action record: {e(a["key_point"])}</a></p></article>'
    if not action_html: action_html='<p>No solution has been adopted or assigned. Review evidence before proposing one.</p>'
    validation_html=''.join(f'<article class="card"><h3>Follow-up: {e(d["action_by_id"][v["action_id"]]["key_point"])}</h3>{record_id("validation",v["validation_id"])}{record_id("action",v["action_id"])}<p><strong>Plan.</strong> {e(v["planned_method"])} on {e(date(v["planned_at"]))}.</p><p><strong>Completed.</strong> {e(date(v["completed_at"]))}. <strong>Recorded result.</strong> {e(v["result"] or "Pending")}</p><p><strong>Next step.</strong> {e(humanize_text(v["next_step"],d))} · Further follow-up: {e(v["followup_needed"])}.</p><p class="muted">Participant: {e(participant_label(d,d["sessions"][v["interview_id"]]["participant_id"]))}. One follow-up does not establish wider impact.</p>{record_id("interview",v["interview_id"])}</article>' for v in d['validations']) or '<p>No follow-up or validation result is recorded.</p>'
    dashboard_href=href(topic/'reports',ROOT/'dashboard.html')
    body=f'''<p class="eyebrow">Topic Research Report</p><h1>{e(d['title'])}</h1><p class="lead">{e(plan.get('decision question',''))}</p><nav class="nav"><a href="../topic.html">{e(d['title'])} Workspace</a><a href="{e(dashboard_href)}">Home Dashboard</a><a href="../research-plan.md">{e(d['title'])} Plan</a></nav><p>{pill(str(len(done))+' of '+str(len(d['participants']))+' interviews completed')} {pill(str(len(d['actions']))+' recorded actions')}</p>
    <section><h2>Executive Summary</h2>{para(syn.get('executive summary','No evidence yet.'),d)}</section>
    <section><h2>Research Overview</h2><p><strong>Research question.</strong> {e(plan.get('decision question',''))}</p><p><strong>Method and sample.</strong> {e(plan.get('method and sample rationale',''))}</p><div class="grid"><div class="card"><h3>Completed interviews</h3><ul>{people}</ul></div><div class="card"><h3>Upcoming or unscheduled</h3><ul>{upcoming}</ul></div></div></section>
    <section><h2>Detailed Findings</h2>{finding_html}</section><section><h2>Patterns and differences</h2>{para(syn.get('patterns and differences','No evidence yet.'),d)}</section>
    <section><h2>Opportunities and priorities</h2>{para(syn.get('next research question','Await interview evidence.'),d)}</section>
    <section><h2>Proposed solutions and action plan</h2>{action_html}</section><section><h2>Follow-up and validation</h2>{validation_html}</section>
    <section><h2>Research limits and next step</h2>{para(syn.get('limitations',''),d)}{para(syn.get('next research question',''),d)}</section>'''
    return page(d['title']+' | Topic Research Report',body,sample)

def topic_workspace(topic,d,sample):
    sessions_by_person={pid:[] for pid in d['people']}
    for interview in d['interviews']:
        sessions_by_person.setdefault(interview['participant_id'],[]).append(interview)
    participant_rows=[]
    for participant in d['participants']:
        pid=participant['participant_id']; interviews=sessions_by_person.get(pid,[]); display_name=participant_label(d,pid)
        reports=[]
        for interview in interviews:
            if interview['status']=='completed':
                reports.append(f'<a href="reports/individuals/{e(pid)}-report.html">Open {e(display_name)}’s interview report</a>')
        report_cell='<br>'.join(reports) if reports else '—'
        participant_rows.append(
            f'<tr><td><strong>{e(display_name)}</strong>{record_id("participant",pid)}'
            f'<span class="muted">{e(participant["profile"])}</span></td>'
            f'<td>{e(participant["recruitment_status"].replace("_"," ").title())}</td><td>{report_cell}</td></tr>'
        )
    findings=[]
    for finding in d['findings']:
        sections=md(topic/finding['detail_path']); source_items=[]
        for evidence_id in filter(None,finding['evidence_ids'].split('|')):
            evidence=d['evidence_by_id'][evidence_id]; interview=d['sessions'][evidence['interview_id']]
            person=d['people'][interview['participant_id']]; display_name=participant_label(d,interview['participant_id'])
            source_items.append(
                f'<li><strong>{e(display_name)}</strong> — {e(evidence["content_summary"])} '
                f'<a href="{e(interview["record_path"])}">Original interview note</a></li>'
            )
        evidence_list=f'<ul>{"".join(source_items)}</ul>' if source_items else '<p>No recorded evidence is linked yet.</p>'
        findings.append(
            f'<div class="card" id="{e(finding["finding_id"])}"><h3>{e(finding["key_point"])}</h3>'
            f'{record_id("finding",finding["finding_id"])}<p><strong>Detailed explanation.</strong> '
            f'{e(sections.get("detailed explanation",""))}</p><p><strong>Evidence sources.</strong></p>{evidence_list}'
            f'<p><strong>Limit.</strong> {e(finding["evidence_limitations"])} · <strong>Status.</strong> '
            f'<span class="tag">{e(finding["status"])}</span></p>'
            f'<p><a href="{e(finding["detail_path"])}">Finding source: {e(finding["key_point"])}</a></p></div>'
        )
    finding_html=''.join(findings) or '<p class="notice"><b>No evidence yet.</b> Complete interviews before generating findings.</p>'
    actions=[]
    for action in d['actions']:
        linked=', '.join(
            f'<a href="#{e(fid)}">{e(d["finding_by_id"][fid]["key_point"])}</a>'
            for fid in filter(None,action['finding_ids'].split('|'))
        )
        actions.append(
            f'<div class="card"><h3>{e(action["key_point"])}</h3>{record_id("action",action["action_id"])}'
            f'<p>{e(action["proposed_solution"])}</p><p><strong>Responds to.</strong> {linked or "No linked finding"}</p>'
            f'<p><strong>Owner.</strong> {e(action["owner"])} · <strong>Status.</strong> '
            f'<span class="tag">{e("validated" if action["status"]=="validated_synthetic" else action["status"].replace("_"," "))}</span> · '
            f'<strong>Approval recorded.</strong> {e(action["user_confirmed"])}</p>'
            f'<p><a href="{e(action["rationale_detail_path"])}">Action record: {e(action["key_point"])}</a></p></div>'
        )
    action_html=''.join(actions) or '<p class="muted">No actions yet.</p>'
    done=sum(interview['status']=='completed' for interview in d['interviews'])
    dashboard_href=href(topic,ROOT/'dashboard.html')
    body=f'''<p class="eyebrow">Topic Workspace</p><h1>{e(d['title'])}</h1>
    <div class="grid"><div class="card"><h3>Research overview</h3><p>{e(d['plan'].get('decision question',''))}</p><span class="tag">{e(plan_status(d))}</span></div><div class="card"><h3>Interview progress</h3><p class="metric">{done} / {len(d['participants'])}</p><p class="muted">Initial interviews complete</p></div></div>
    <h2>Participants &amp; Interviews</h2><div class="table-wrap"><table><tr><th>Participant</th><th>Status</th><th>Report</th></tr>{''.join(participant_rows)}</table></div>
    <h2>Key Findings</h2>{finding_html}<h2>Recommendations &amp; Actions</h2>{action_html}
    <h2>Next Steps</h2>{para(d['synthesis'].get('next research question','Await interview evidence.'),d)}
    <h2>Reports</h2><p><a href="reports/topic-report.html">Open Topic Research Report</a> · <a href="{e(dashboard_href)}">Home Dashboard</a></p>'''
    body=clean_report_copy(body)
    footer='Sample workspace · Illustrative data and fictional participants' if sample else 'User Interview Workspace · Topic workspace'
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(d["title"])}</title>{DASHBOARD_CSS}<main>{body}<footer>{footer}</footer></main></html>\n'

def home_dashboard(loaded):
    workspace=[item for item in loaded if not item[1]]
    def topic_cards(items):
        cards=[]
        for topic,_,d in items:
            done=sum(i['status']=='completed' for i in d['interviews']); rel=topic.relative_to(ROOT).as_posix()
            cards.append(
                f'<div class="card"><h3>{e(d["title"])}</h3><p>{e(d["plan"].get("decision question",""))}</p>'
                f'<p><span class="tag">{e(plan_status(d))}</span> · {done}/{len(d["participants"])} interviews</p>'
                f'<a href="{e(rel)}/topic.html">Open {e(d["title"])} Workspace</a> · '
                f'<a href="{e(rel)}/reports/topic-report.html">Open Research Report</a></div>'
            )
        return ''.join(cards)
    action_rows=[]
    for topic,_,d in loaded:
        action_rows.append(
            f'<tr><td><strong>{e(d["title"])}</strong></td><td><span class="tag">{e(plan_status(d))}</span></td>'
            f'<td>{e(humanize_text(d["synthesis"].get("next research question","Await interview evidence."),d))}</td></tr>'
        )
    people=sum(len(d['participants']) for _,_,d in workspace)
    completed=sum(sum(i['status']=='completed' for i in d['interviews']) for _,_,d in workspace)
    open_actions=sum(sum(a['status'] in ('proposed','in_progress') for a in d['actions']) for _,_,d in workspace)
    if workspace:
        workspace_section=f'''<div class="grid"><div class="card"><h3>Research Topics</h3><p class="metric">{len(workspace)}</p></div><div class="card"><h3>Participants</h3><p class="metric">{people}</p></div><div class="card"><h3>Completed interviews</h3><p class="metric">{completed}</p></div><div class="card"><h3>Open actions</h3><p class="metric">{open_actions}</p></div></div><h2>Your Research Topics</h2><div class="grid">{topic_cards(workspace)}</div>'''
        next_actions=f'''<h2>Next Actions</h2><div class="table-wrap"><table><tr><th>Topic</th><th>Status</th><th>Next step</th></tr>{''.join(action_rows)}</table></div>'''
    else:
        workspace_section='''<h2>Start your first interview Topic</h2><div class="card"><h3>Your workspace is ready</h3><p>Tell your agent what you want to learn and who you want to interview. It will create the Topic, prepare the interview guide, and keep the records and reports up to date.</p><p><strong>Try:</strong> <i>“I want to understand why customers leave during checkout. Help me create a Topic and prepare the first interview.”</i></p></div>'''
        next_actions=''
    body=f'''<p class="eyebrow">Interview research</p><h1>User Interview Workspace</h1><p>A ready-to-use workflow for planning interviews, reviewing evidence, tracking improvements, and checking results with your agents.</p>
    {workspace_section}{next_actions}
    <h2>Reports &amp; Insights</h2><p>Open a Topic Workspace to find its Topic Report and completed individual reports. Pages lead with meaningful names and descriptions; internal IDs remain available only as supporting traceability details.</p><p><a href="README.md">Read the non-developer guide</a> · <a href="QA_CHECKLIST.md">QA status</a></p>'''
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>User Interview Workspace</title>{DASHBOARD_CSS}<main>{body}<footer>Static local HTML · Generated from Markdown and CSV source files</footer></main></html>\n'

def main():
    topics=[]
    for parent,sample in ((ROOT/'05-tests'/'fixtures'/'research-topics',True),(ROOT/'01-workspace',False)):
        topics.extend((topic,sample) for topic in sorted(parent.glob('T*-*')) if topic.is_dir())
    loaded=[(topic,sample,load(topic)) for topic,sample in topics]  # Check all source relationships before writing.
    generated=[(ROOT/'dashboard.html',home_dashboard([item for item in loaded if not item[1]]))]
    report_count=0
    for topic,sample,d in loaded:
        generated.append((topic/'topic.html',topic_workspace(topic,d,sample)))
        generated.append((topic/'reports'/'topic-report.html',topic_report(topic,d,sample)))
        report_count+=1
        for i in d['interviews']:
            if i['status']=='completed':
                generated.append((topic/'reports'/'individuals'/(i['participant_id']+'-report.html'),individual(topic,d,i,sample)))
                report_count+=1
    for path,content in generated: path.write_text(content,encoding='utf-8')
    fixture_count=sum(sample for _,sample,_ in loaded)
    user_count=len(loaded)-fixture_count
    print(f'Refreshed Home Dashboard and {user_count} user Topic Workspaces; validated and regenerated {fixture_count} isolated test fixtures; {report_count} reports checked.')

if __name__=='__main__':
    try: main()
    except (KeyError,ValueError,OSError) as exc: print(f'Report refresh stopped: {exc}',file=sys.stderr); sys.exit(1)
