#!/usr/bin/env python3
"""Regenerate only demo Topic and individual HTML reports from existing records."""
from datetime import datetime
from html import escape
from pathlib import Path
import csv
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
CSS = '''<style>:root{--ink:#1d2a40;--muted:#58667b;--line:#dce3eb;--blue:#2455b5;--bg:#f5f7fa}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.62 system-ui,-apple-system,Segoe UI,sans-serif;overflow-wrap:anywhere}main{max-width:960px;margin:auto;padding:32px 22px 72px}h1{font-size:clamp(30px,5vw,42px);line-height:1.15;margin:5px 0 12px}h2{font-size:23px;margin:0 0 17px}h3{font-size:18px;margin:0 0 8px}p{margin:0 0 14px}a{color:var(--blue);text-underline-offset:2px}.eyebrow{color:var(--blue);font-size:12px;font-weight:750;letter-spacing:.1em;text-transform:uppercase}.lead{font-size:18px}.nav{display:flex;flex-wrap:wrap;gap:15px;margin:20px 0 28px}.nav a{font-weight:650}section{background:white;border:1px solid var(--line);border-radius:12px;padding:23px;margin:18px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(195px,1fr));gap:12px}.card{border:1px solid var(--line);border-radius:10px;padding:17px;margin:14px 0;background:white}.fact{background:#f2f6fc;padding:12px;border-radius:8px}.label{display:block;font-size:12px;font-weight:700;letter-spacing:.04em;text-transform:uppercase;color:var(--muted);margin-bottom:4px}.pill{display:inline-block;background:#e9f0ff;color:#204798;border-radius:999px;padding:3px 10px;font-size:13px;font-weight:700}.pill.draft{background:#fff1d9;color:#8d5900}.pill.empty{background:#edf0f3;color:#566172}.quote{border-left:3px solid var(--blue);padding:6px 0 6px 17px;margin:12px 0;font-size:17px}.muted{color:var(--muted)}ul{padding-left:22px;margin:9px 0}li{margin:6px 0}footer{color:var(--muted);font-size:13px;margin-top:30px}@media(max-width:600px){main{padding:20px 13px 55px}section{padding:18px}}</style>'''

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
def para(value): return ''.join(f'<p>{e(block)}</p>' for block in re.split(r'\n\s*\n',value) if block.strip())
def date(value):
    if not value: return 'Not recorded'
    try: return datetime.fromisoformat(value).strftime('%d %B %Y, %H:%M UTC%z' if 'T' in value else '%d %B %Y')
    except ValueError: return value
def pill(value):
    value='validated' if value=='validated_synthetic' else value
    cls = ' draft' if value in ('draft','proposed','scheduled') else ' empty' if value in ('recruiting','not_scheduled') else ''
    return f'<span class="pill{cls}">{e(value.replace("_"," "))}</span>'
def page(title, body):
    body=body.replace('This small, illustrative sample is chosen to demonstrate workflow coverage—not to estimate a population. Dates and findings are synthetic.','This small sample is not intended to estimate a population.')
    body=body.replace('This material must never be presented as real user research.','')
    body=body.replace('it is illustrative only and not a production outcome.','it is not a production outcome.')
    body=body.replace('The single V001 follow-up is illustrative and cannot establish general improvement.','The single V001 follow-up cannot establish general improvement.')
    body=re.sub(r'\b[Ss]ynthetic\b\s*', '', body)
    body=re.sub(r'\b[Ff]ictional\b\s*', '', body)
    body=body.replace('Approved in demo','Approval recorded')
    body=re.sub(r' {2,}', ' ', body)
    return f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)}</title>{CSS}<main>{body}<footer>Sample report · Illustrative data and fictional participants</footer></main></html>\n'

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
    return f'<div class="card"><span class="label">Recorded evidence · {e(x["evidence_id"])} · {e(person["alias"])} · {e(date(i["actual_at"]))}</span><blockquote class="quote">{e(x["content_summary"])}</blockquote><p class="muted"><a href="{prefix}{e(i["record_path"])}">Original interview note</a></p></div>'

def individual(topic,d,i):
    person=d['people'][i['participant_id']]; iid=i['interview_id']; prompt,reading,opportunity=session_notes(topic,i)
    evidence=[x for x in d['evidence'] if x['interview_id']==iid]; ids={x['evidence_id'] for x in evidence}
    findings=[f for f in d['findings'] if ids.intersection(f['evidence_ids'].split('|'))]; fids={f['finding_id'] for f in findings}
    actions=[a for a in d['actions'] if fids.intersection(a['finding_ids'].split('|'))]
    validations=[v for v in d['validations'] if v['interview_id']==iid]
    quotes=''.join(evidence_card(x,d,'../../') for x in evidence)
    broader=''.join(f'<div class="card"><h3>{e(f["key_point"])} <span class="muted">({e(f["finding_id"])})</span></h3><p><strong>This participant’s contribution.</strong> {e(", ".join(ids.intersection(f["evidence_ids"].split("|"))))} supplies the recorded statement shown above.</p><p><strong>Broader context.</strong> This Topic finding also draws on other linked interviews; those participants’ views are presented in the Topic report.</p><p><a href="../topic-report.html#{e(f["finding_id"])}">Read the broader finding in the Topic Research Report</a></p></div>' for f in findings) or '<p>This interview is not yet linked to a Topic finding.</p>'
    solutions=''.join(f'<div class="card"><h3>{e(a["key_point"])} <span class="muted">({e(a["action_id"])})</span></h3><p><strong>Proposed solution.</strong> {e(a["proposed_solution"])}</p><p><strong>Why it appears here.</strong> This Topic-level proposal responds to a broader finding that includes this participant’s evidence. It is an analyst recommendation, not the participant’s requested design.</p><p><strong>Owner.</strong> {e(a["owner"])} · <strong>Due.</strong> {e(date(a["due_date"]))} · <strong>Priority.</strong> {e(a["priority"])} · <strong>Status.</strong> {pill(a["status"])} · <strong>Approved in demo.</strong> {e(a["user_confirmed"])}</p></div>' for a in actions) or '<p>No Topic-level action is connected to this participant’s evidence.</p>'
    followup=''.join(f'<div class="card"><h3>{e(v["validation_id"])} · Follow-up for {e(v["action_id"])}</h3><p><strong>Record scope.</strong> This validation links to {e(iid)}, this participant’s interview record.</p><p><strong>Method and date.</strong> {e(v["planned_method"])} · {e(date(v["completed_at"] or v["planned_at"]))}</p><p><strong>Recorded result.</strong> {e(v["result"] or "Pending")}</p><p><strong>Further follow-up.</strong> {e(v["followup_needed"])} · {e(v["next_step"])}</p></div>' for v in validations) or '<p>No follow-up or validation result is recorded for this participant.</p>'
    body=f'''<p class="eyebrow">Individual Interview Report</p><h1>{e(person['alias'])}</h1><p class="lead">{e(d['title'])} · Source-linked interview record.</p><nav class="nav"><a href="../topic-report.html">Topic Research Report</a><a href="../../topic.html">Topic Workspace</a><a href="../../{e(i['record_path'])}">Original interview note</a></nav>
    <section><h2>Interview overview</h2><div class="grid"><div class="fact"><span class="label">Interview date</span>{e(date(i['actual_at']))}</div><div class="fact"><span class="label">Background</span>{e(person['profile'])}</div><div class="fact"><span class="label">Method</span>{e(i['method'])}</div><div class="fact"><span class="label">Session</span>{e(iid)} · {pill(i['status'])}</div></div></section>
    <section><h2>Executive Summary</h2><p>{e(reading)}</p><p><strong>Research recommendation.</strong> {e(opportunity)}</p></section>
    <section><h2>Key question and recorded response</h2><p><strong>Relevant guide question:</strong> “{e(prompt)}”</p><p class="muted">The note does not record the exact question asked or a full Q&amp;A transcript. The statement below is verbatim from the source.</p>{quotes}</section>
    <section><h2>Participant evidence and interpretation</h2><p><strong>Evidence.</strong> The participant’s recorded statement appears above.</p><p><strong>Interpretation.</strong> {e(reading)}</p><p><strong>Recommendation.</strong> {e(opportunity)}</p></section>
    <section><h2>Related Topic Findings / Broader Context</h2>{broader}</section>
    <section><h2>Related proposed solutions and ownership</h2>{solutions}</section><section><h2>Participant follow-up and validation</h2>{followup}</section>
    <section><h2>Research Limitations</h2><p>The source is one brief interview note rather than a complete transcript. The report does not add an unrecorded question, behavior, or outcome. Broader findings, actions, and validation states come from the linked Topic records.</p></section>'''
    return page(person['alias']+' | Individual Interview Report',body)

def topic_report(topic,d):
    done=[i for i in d['interviews'] if i['status']=='completed']; pending=[i for i in d['interviews'] if i['status']!='completed']
    syn=d['synthesis']; plan=d['plan']
    people=''.join(f'<li><a href="individuals/{e(i["participant_id"])}-report.html">{e(d["people"][i["participant_id"]]["alias"])} · {e(date(i["actual_at"]))}</a></li>' for i in done) or '<li>No completed interviews or individual reports.</li>'
    upcoming=''.join(f'<li>{e(d["people"][i["participant_id"]]["alias"])} · {e(i["status"].replace("_"," "))} · {e(date(i["planned_at"]))}</li>' for i in pending) or '<li>No initial interviews pending.</li>'
    finding_html=''
    for f in d['findings']:
        sections=md(topic/f['detail_path']); quotes=''.join(evidence_card(d['evidence_by_id'][eid],d,'../') for eid in f['evidence_ids'].split('|') if eid)
        finding_html+=f'<article class="card" id="{e(f["finding_id"])}"><h3>{e(f["finding_id"])} · {e(f["key_point"])}</h3><p><strong>Detailed explanation.</strong> {e(sections.get("detailed explanation",""))}</p><p><strong>Recorded evidence.</strong></p>{quotes}<p><strong>Interpretation and potential impact.</strong> {e(sections.get("interpretation and potential impact",sections.get("interpretation","")))}</p><p><strong>Limit.</strong> {e(f["evidence_limitations"])} · <strong>Status.</strong> {pill(f["status"])}</p><p><a href="../{e(f["detail_path"])}">Finding source</a></p></article>'
    if not finding_html: finding_html='<p><strong>No evidence yet.</strong> There are no completed interviews or research findings.</p>'
    action_html=''
    for a in d['actions']:
        refs=', '.join(f'<a href="#{e(fid)}">{e(fid)}</a>' for fid in a['finding_ids'].split('|') if fid)
        rationale=md(topic/a['rationale_detail_path']).get('intro','').splitlines()[-1]
        action_html+=f'<article class="card"><h3>{e(a["action_id"])} · {e(a["key_point"])}</h3><p><strong>Proposed solution.</strong> {e(a["proposed_solution"])}</p><p><strong>Rationale and evidence.</strong> This addresses {refs}; the recorded statements and limits appear above. {e(rationale)}</p><div class="grid"><div class="fact"><span class="label">Owner</span>{e(a["owner"])}</div><div class="fact"><span class="label">Priority / due date</span>{e(a["priority"])} · {e(date(a["due_date"]))}</div><div class="fact"><span class="label">Execution status</span>{pill(a["status"])}</div><div class="fact"><span class="label">Approved in demo</span>{e(a["user_confirmed"])}</div></div><p><a href="../{e(a["rationale_detail_path"])}">Action record</a></p></article>'
    if not action_html: action_html='<p>No solution has been adopted or assigned. Review evidence before proposing one.</p>'
    validation_html=''.join(f'<article class="card"><h3>{e(v["validation_id"])} · {e(v["action_id"])}</h3><p><strong>Plan.</strong> {e(v["planned_method"])} on {e(date(v["planned_at"]))}.</p><p><strong>Completed.</strong> {e(date(v["completed_at"]))}. <strong>Recorded result.</strong> {e(v["result"] or "Pending")}</p><p><strong>Next step.</strong> {e(v["next_step"])} · Further follow-up: {e(v["followup_needed"])}.</p><p class="muted">Linked to {e(d["people"][d["sessions"][v["interview_id"]]["participant_id"]]["alias"])} ({e(v["interview_id"])}). One synthetic follow-up does not establish wider impact.</p></article>' for v in d['validations']) or '<p>No follow-up or validation result is recorded.</p>'
    body=f'''<p class="eyebrow">Topic Research Report</p><h1>{e(d['title'])}</h1><p class="lead">{e(plan.get('decision question',''))}</p><nav class="nav"><a href="../topic.html">Topic Workspace</a><a href="../../../dashboard.html">Home Dashboard</a><a href="../research-plan.md">Research plan</a></nav><p>{pill(str(len(done))+' of '+str(len(d['participants']))+' interviews completed')} {pill(str(len(d['actions']))+' recorded actions')}</p>
    <section><h2>Executive Summary</h2>{para(syn.get('executive summary','No evidence yet.'))}</section>
    <section><h2>Research Overview</h2><p><strong>Research question.</strong> {e(plan.get('decision question',''))}</p><p><strong>Method and sample.</strong> {e(plan.get('method and sample rationale',''))}</p><div class="grid"><div class="card"><h3>Completed interviews</h3><ul>{people}</ul></div><div class="card"><h3>Upcoming or unscheduled</h3><ul>{upcoming}</ul></div></div></section>
    <section><h2>Detailed Findings</h2>{finding_html}</section><section><h2>Patterns and differences</h2>{para(syn.get('patterns and differences','No evidence yet.'))}</section>
    <section><h2>Opportunities and priorities</h2>{para(syn.get('next research question','Await interview evidence.'))}</section>
    <section><h2>Proposed solutions and action plan</h2>{action_html}</section><section><h2>Follow-up and validation</h2>{validation_html}</section>
    <section><h2>Research limits and next step</h2>{para(syn.get('limitations',''))}{para(syn.get('next research question',''))}</section>'''
    return page(d['title']+' | Topic Research Report',body)

def main():
    topics=sorted(p for p in (ROOT/'demo').glob('T*-*') if p.is_dir())
    loaded=[(topic,load(topic)) for topic in topics]  # Check all source relationships before writing.
    generated=[]
    for topic,d in loaded:
        generated.append((topic/'reports'/'topic-report.html',topic_report(topic,d)))
        for i in d['interviews']:
            if i['status']=='completed': generated.append((topic/'reports'/'individuals'/(i['participant_id']+'-report.html'),individual(topic,d,i)))
    for path,content in generated: path.write_text(content,encoding='utf-8')
    print(f'Refreshed {len(topics)} Topic reports and {len(generated)-len(topics)} individual reports; source relationships checked.')

if __name__=='__main__':
    try: main()
    except (KeyError,ValueError,OSError) as exc: print(f'Report refresh stopped: {exc}',file=sys.stderr); sys.exit(1)
