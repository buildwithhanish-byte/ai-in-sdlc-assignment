"""Compile traceability records from existing evidence; does not rerun AI or tests."""
from pathlib import Path
import json, zipfile, hashlib, subprocess
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sources = [
 ('diagrams/task-1-ai-augmentation-log.txt', 'diagrams/task-1-index.html', 'Architecture diagrams and executable structural test'),
 ('decisions/task-2-ai-augmentation-log.txt', 'decisions/task-2-decision.html', 'Compare payment-submission options and prepare a decision record'),
 ('policies/task-3-ai-augmentation-log.txt', 'policies/task-3-autonomy-policy.html', 'Prepare an incident-summary autonomy policy'),
 ('evaluations/task-4-ai-augmentation-log.txt', 'evaluations/task-4-review-evaluation.html', 'Prepare, execute and score the review evaluation'),
 ('risk-and-measurement/task-5-ai-augmentation-log.txt', 'risk-and-measurement/task-5-risk-and-measurement.html', 'Audit risk and document available measurements and source gaps')]
required = ['id','timestamp','stage','agent','agent_name','agent_type','ai_tool','model','mode','related_ids','parent_task','context','request','skills_used','subagents_used','mcp_tools_used','tools_used','suggestion','human_decision','action_verification','limitation','status','artifacts']
def base(identity, task):
 return dict(id=identity,timestamp=None,stage=task,agent='agent',agent_name='Codex',agent_type='built-in',ai_tool='OpenAI Codex',model=None,mode=None,related_ids=[],parent_task=task,context='AI in SDLC assignment',request=None,skills_used=None,subagents_used=None,mcp_tools_used=None,tools_used=[],suggestion=None,human_decision=None,action_verification=None,limitation=None,status='partial',artifacts=[])
records=[]
human = {
1:'User confirmed the separate Mermaid-enabled terminal was open and requested continuation. No claim of independent human technical verification.',
2:'User challenged the worker recommendation and asked about month-end incident handling; user requested drafting assistance. Independent authorship is not established.',
3:'User explicitly stated they had read and reviewed the policy and requested the footer update. This is review confirmation, not an executed policy trial.',
4:'User requested completion and a smaller submission package. Review scoring and reproduction checks were AI-assisted; no independent human gold-label validation is established.',
5:'User explicitly elected stated assumptions and available measurements. A later source lookup was declined and was not retried.'}
verifications={1:'Saved command outputs report one architecture test passed, the negative control failed as intended, and eight final solution tests passed.',2:'Design comparison and limitations documented; no provider experiment or implementation test.',3:'Policy prepared and user review confirmed; controls and trial remain proposed.',4:'48 review sessions and input hashes checked; provisional scoring and context limitations disclosed.',5:'Saved API evidence used for calculations; missing production/review data remain unavailable.'}
for n,(summary,report,request) in enumerate(sources,1):
 p=ROOT/'docs'/summary
 text=p.read_text(encoding='utf-8')
 r=base(f'task-{n}-retrospective-summary',f'task-{n}')
 r.update(record_origin='retrospective_summary',historical_date='2026-10-24',timestamp_basis='Summary date only; exact interaction time unavailable.',request=request,request_kind='summary_not_verbatim',source_summary=text,source_evidence=[{'path':'docs/'+summary,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}],human_decision=human[n],action_verification=verifications[n],artifacts=['docs/'+summary,'docs/'+report],status='completed_with_limitations',custom_instructions=[{'path':'AGENTS.md','scope':'Repository conventions reported as consulted; event-by-event application not reconstructed.'}],tools_used=['Repository file inspection'],limitation='Retrospectively compiled from a saved summary. Full prompts, exact model/mode, skill inventory, sub-agent inventory and session timestamps are not established by this source. Null means unknown, not none used.')
 if n==1:
  marker='Rendering instruction supplied to the separate terminal:\n'
  prompt=text.split(marker,1)[1].split('\n\nSubmission wording',1)[0].strip()
  r['interactions']=[{'role':'user_instruction_to_separate_terminal','text':prompt,'provenance':'Exact instruction reproduced in saved summary; terminal transcript not included.'}]
  r['mcp_tools_used']=[{'server':'mermaid','tool':None,'purpose':'Validate and render diagrams in the separate terminal; exact tool invocation unavailable in this summary.'}]
  r['artifacts']+=['backend/tests/InvoiceApp.Tests/DomainArchitectureTests.cs','docs/diagrams/architecture-test-output.txt','docs/diagrams/architecture-negative-control-output.txt','docs/diagrams/task1-full-suite-output.txt']
 if n==2:
  r['interactions']=[]
  for label in ('Actual preference challenge submitted by the user:','Actual failure challenge submitted by the user:'):
   r['interactions'].append({'role':'user','text':text.split(label,1)[1].strip().split('\nOutcome:',1)[0],'provenance':'Exact prompt reproduced in saved summary; full response not preserved here.'})
 if n==4:
  r['model']='gpt-6-astra'
  r['related_ids']=['task-4-run-1-case-01']
 if n==5:
  r['tools_used']+=['Public GitHub API via saved responses','Offline calculations','GitHub connector source recheck (HTTP 403)']
 records.append(r)
archive=ROOT/'docs/evaluations/raw-review-evidence.zip'
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 for name in sorted(x for x in z.namelist() if x.endswith('/run.json')):
  folder=name.rsplit('/',1)[0]
  meta=json.loads(z.read(name))
  inp=z.read(folder+'/input.txt').decode('utf-8').replace('\r\n','\n').encode('utf-8')
  assert hashlib.sha256(inp).hexdigest()==meta['input_sha256']
  events=[json.loads(line) for line in z.read(folder+'/events.jsonl').decode('utf-8').splitlines() if line.strip()]
  tool_items=meta.get('tool_items',[])
  identity='task-4-'+folder.removeprefix('raw/').replace('/','-')
  r=base(identity,'task-4')
  r.update(timestamp=meta['start_utc'],record_origin='normalized_automatic_capture',agent_name='Codex CLI reviewer',model=meta['model'],mode='agent',mode_basis='Normalized from recorded codex exec command',skills_used=[],subagents_used=[],mcp_tools_used=[],request=inp.decode('utf-8'),request_kind='verbatim_saved_input',suggestion=z.read(folder+'/response.txt').decode('utf-8'),human_decision=None,action_verification='Input hash verified against original run metadata. Review finding correctness is assessed separately in judgments.json; execution completion does not imply a correct review.',limitation='Original capture retained in archive. Managed platform instructions remained active. Any tool calls and warnings are retained below. Human review of this individual response is not established.',status=meta['status'],related_ids=['task-4-retrospective-summary'],artifacts=['docs/evaluations/raw-review-evidence.zip'],execution_evidence={'archive':'docs/evaluations/raw-review-evidence.zip','entries':[name,folder+'/input.txt',folder+'/response.txt',folder+'/events.jsonl',folder+'/stderr.txt'],'session_ids':meta.get('thread_ids',[]),'start_utc':meta['start_utc'],'end_utc':meta.get('end_utc'),'input_sha256':meta['input_sha256'],'exit_code':meta.get('exit_code'),'reasoning':meta.get('reasoning')},tools_used=tool_items,recorded_warnings=[e['item'] for e in events if e.get('item',{}).get('type')=='error'],capture_scope='One unscored pilot' if folder=='raw/pilot' else 'One of 48 scored reviews',capability_note='Skills and multi-agent features disabled in recorded command. Empty resource discovery occurred in some runs; original tool items and metadata remain authoritative.')
  # Preserve discovered tools without inventing server identities or classifying them as approved integrations.
  r['observed_tool_items']=tool_items
  records.append(r)
for r in records:
 assert all(k in r for k in required)
 for p in r['artifacts']: assert (ROOT/p).exists(),p
ids=[r['id'] for r in records]
assert len(ids)==len(set(ids))
assert len(records)==54
out=OUT/'augmentation.jsonl'
out.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
manifest={'record_count':len(records),'retrospective_summary_count':5,'normalized_automatic_capture_count':49,'scored_reviews':48,'unscored_pilot':1,'source_archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'jsonl_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'checks':['JSON parse and required fields','Unique record IDs','49 input hashes match saved metadata','Archive integrity','Artifact paths exist'],'limitation':'Validation checks evidence linkage and structure, not correctness of AI conclusions or independent human oversight.'}
(OUT/'validation.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(manifest,indent=2))