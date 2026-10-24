from pathlib import Path
import json,csv,html,hashlib,zipfile,datetime
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evaluations'
def readjson(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def h(s): return html.escape(str(s))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    judgments=readjson(OUT/'judgments.json')
    assert len(judgments)==48 and len({(x[0],x[1]) for x in judgments})==48
    key=readjson(OUT/'scoring-key.json')['cases']
    manifest=readjson(OUT/'execution-manifest.json')
    for name,digest in manifest['case_hashes'].items(): assert sha(ROOT/'ops/evals/cases'/name)==digest, name+' changed'
    for name,digest in manifest['prompt_hashes'].items(): assert sha(OUT/f'prompt-{name}.txt')==digest
    assert sha(OUT/'scoring-key.json')==manifest['answer_key_sha256']
    rows=[];details=[];threadids=[];attempts=[];usage={'input_tokens':0,'cached_input_tokens':0,'output_tokens':0,'reasoning_output_tokens':0}
    for r,c,verdict,confidence,summary,notes in sorted(judgments):
        case=f'case-{c:02}';base=OUT/f'raw/run-{r}/{case}'
        meta=readjson(base/'run.json');response=(base/'response.txt').read_text(encoding='utf-8-sig')
        assert meta['exit_code']==0 and 'turn.completed' in meta['event_types'] and response.strip()
        assert meta['model']==manifest['model'] and meta['reasoning']==manifest['reasoning']
        prompt=(OUT/f'prompt-v{2 if r==4 else 1}.txt').read_text(encoding='utf-8-sig').strip()
        diff=(ROOT/f'ops/evals/cases/{case}.diff').read_text(encoding='utf-8-sig')
        assert (base/'input.txt').read_text(encoding='utf-8')==prompt+'\n\n'+diff
        assert hashlib.sha256((prompt+'\n\n'+diff).encode()).hexdigest()==meta['input_sha256']
        threadids+=meta['thread_ids']
        if meta['tool_items']:
            completed=[e['item'] for e in meta['tool_items'] if e['type']=='item.completed']
            assert completed
            for item in completed:
                assert item['server']=='codex' and item['tool'] in ('list_mcp_resources','list_mcp_resource_templates')
                assert item['result']['content'][0]['text'] in ('{"resources":[]}','{"resourceTemplates":[]}')
            attempts.append(f'run {r}, {case}')
        for u in meta.get('usage',[]):
            for name in usage: usage[name]+=u.get(name,0)
        label=key[case]['label'];assert verdict in (('caught','missed') if label=='defective' else ('clean','false_alarm'))
        rows.append(dict(run=r,case=case,model=meta['model'],prompt_version='v2' if r==4 else 'v1',verdict=verdict,finding_summary=summary,confidence_reported=confidence,notes=notes,execution_status='completed; empty discovery only' if meta['tool_items'] else 'completed',raw_output_path=f'raw/run-{r}/{case}/response.txt'))
        details.append(f'<details id="r{r}-{case}"><summary>Run {r} / {case}: {h(verdict)}</summary><p><strong>Scoring:</strong> {h(summary)} {h(notes)}</p><p>Confidence reported: {h(confidence)}</p><pre>{h(response)}</pre></details>')
    assert len(threadids)==48 and len(set(threadids))==48
    with (OUT/'results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    def metrics(selected):
        counts={k:sum(x['verdict']==k for x in selected) for k in ('caught','missed','false_alarm','clean')}
        counts['defective']=counts['caught']+counts['missed'];counts['clean_cases']=counts['false_alarm']+counts['clean'];return counts
    stats={f'run-{r}':metrics([x for x in rows if x['run']==r]) for r in range(1,5)}
    stats['baseline-pooled']=metrics([x for x in rows if x['run']<=3])
    core={f'run-{r}':metrics([x for x in rows if x['run']==r and not key[x['case']].get('context_sensitive')]) for r in range(1,5)}
    def fraction(n,d): return f'{n}/{d} ({100*n/d:.1f}%)'
    def table(data):
        t='<table><tr><th>Run</th><th>Caught / defective</th><th>Missed / defective</th><th>False alarms / clean</th></tr>'
        for name,m in data.items(): t+=f'<tr><td>{h(name)}</td><td>{fraction(m["caught"],m["defective"])}</td><td>{fraction(m["missed"],m["defective"])}</td><td>{fraction(m["false_alarm"],m["clean_cases"])}</td></tr>'
        return t+'</table>'
    comparison=readjson(OUT/'interpretation.json')
    matrix='<table><tr><th>Case</th><th>Expected label</th>'+''.join(f'<th>Run {r}</th>' for r in range(1,5))+'</tr>'
    for c in range(1,13):
        case=f'case-{c:02}';matrix+=f'<tr><td><a href="../../ops/evals/cases/{case}.diff">{case}</a></td><td>{key[case]["label"]}{" *" if key[case].get("context_sensitive") else ""}</td>'
        for r in range(1,5):
            row=next(x for x in rows if x['case']==case and x['run']==r)
            matrix+=f'<td><a href="#r{r}-{case}">{h(row["verdict"])}</a></td>'
        matrix+='</tr>'
    matrix+='</table>'
    archive=OUT/'raw-review-evidence.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted((OUT/'raw').rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(OUT))
    with zipfile.ZipFile(archive) as z: assert z.testzip() is None
    report='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task 4 - Review evaluation</title><style>body{font:16px/1.55 system-ui,sans-serif;max-width:1120px;margin:36px auto;padding:0 24px;color:#172638}h1,h2{line-height:1.25}h2{margin-top:30px}table{border-collapse:collapse;width:100%;margin:14px 0}td,th{padding:9px;border:1px solid #cbd5e1;text-align:left;vertical-align:top}th{background:#edf2f7}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6f8;padding:14px;font:13px/1.5 monospace}details{padding:10px;border-bottom:1px solid #ccd5df}summary{cursor:pointer;font-weight:600}.note{background:#edf4fb;padding:14px}a{color:#185d96}</style></head><body><h1>Task 4: Review evaluation</h1>'''
    report+=f'<p class="note">Completed 48 fresh case reviews: three baseline passes and one changed-prompt pass. Model: {h(manifest["model"])}; reasoning: {h(manifest["reasoning"])}. Prepared and scored with AI assistance. Labels are provisional source-based judgments, not an instructor answer key or an independent human assessment.</p>'
    report+='<h2>What was tested</h2><p>The ten supplied diffs and two additional cases were reviewed separately in fresh Codex sessions. Each reviewer received only its prompt and diff as task input, not the answer key, other outputs or repository files. Standard platform and managed instructions still applied. Runs 1-3 used v1; run 4 used v2. The model, reasoning, cases, order and command flags stayed fixed.</p><p>The added prompt asks for a concrete trigger and incorrect behaviour, and warns against inventing missing surrounding code. The hypothesis was fewer false alarms, with a possible loss of recall. Both prompts were saved before baseline results.</p>'
    report+='<h2>Results</h2>'+table(stats)
    report+='<h2>Did the prompt change help?</h2>'+''.join('<p>'+h(p)+'</p>' for p in comparison['paragraphs'])
    report+='<h2>Case-by-case results</h2>'+matrix+'<p>* Context-sensitive scoring: case 03 assumes the previous rounding policy is required; case 05 assumes no broader Admin restriction; case 07 depends on data fields and logging behaviour; case 09 requires knowledge of login and repository lifetime. A cautious no-finding answer on these cases can be reasonable from the diff alone.</p>'
    report+='<h2>Sensitivity check</h2><p>Excluding cases 03, 05, 07 and 09 leaves five defective and three clean cases per pass. This view was specified before completion, not selected to improve a result.</p>'+table(core)
    report+='<h2>Limits and scoring choices</h2><p>Caught and missed rates use defective cases as their denominator. False alarm rates use clean cases. A finding must explain the real failure; vague advice does not count. Style suggestions are not false alarms. Additional unsupported findings are described in individual scoring notes. Confidence values are the reviewer’s own words, not calibrated probabilities.</p><p>There are only 12 unique cases and three clean examples. The repeated baseline outputs are correlated, so pooled 27 defective reviews and nine clean reviews are not 36 independent examples. Four supplied cases were shown during the workshop, which further limits generalisation. The changed prompt ran once, and fixed run order leaves possible time effects. These results support a small descriptive comparison, not a claim of statistically established improvement.</p>'
    report+='<p>The two added cases come from one repository defect reproduced during this assignment with AI assistance. They are a related buggy/fixed pair, not two past employment incidents. The corrected case is clean within its explicit shared-object in-process contract, not proof of production or distributed safety. It also supplies more context than some original diffs. See the <a href="../../ops/evals/additional-case-evidence/README.txt">reproduction and provenance record</a>.</p>'
    report+=f'<h2>Execution integrity</h2><p>All 48 reviews have distinct session IDs, completed responses, fixed input hashes and zero substantive external context reads. Empty resource-discovery calls occurred in: {h(", ".join(attempts) if attempts else "none")}. These returned no content and are retained in the evidence. Run 1 case 09 initially triggered the runner’s strict tool check; its response was retained and scored without rerunning. Only the validation policy was amended to accept empty discovery. No reviewer settings or inputs changed.</p>'
    report+='<p>Managed approval-policy and PowerShell snapshot warnings are preserved in raw logs. No safeguards were bypassed. The final report records saved outcomes; generating this report did not rerun reviews. The standard model alias was fixed, but an immutable server-side model snapshot cannot be independently verified.</p>'
    report+='<h2>Files and reproduction</h2><ul><li><a href="results.csv">48-row results table</a></li><li><a href="prompt-v1.txt">Baseline prompt</a> and <a href="prompt-v2.txt">changed prompt</a></li><li><a href="scoring-key.json">Frozen provisional scoring key</a> and <a href="judgments.json">per-response adjudication</a></li><li><a href="execution-manifest.json">Input hashes and execution manifest</a>, <a href="execution-protocol.txt">method and amendments</a>, and <a href="verification.json">final integrity checks</a></li><li><a href="raw-review-evidence.zip">Full raw evidence archive</a> (inputs, event streams, responses, metadata and warnings; also contains the unscored setup pilot)</li><li><a href="run_reviews.py">Original runner</a>, <a href="continue_reviews.py">recorded continuation</a>, and <a href="build_report.py">report builder</a></li><li><a href="task-4-ai-augmentation-log.txt">AI augmentation log</a></li></ul><p>Review inputs were sent to a new <code>codex exec --ephemeral</code> process each time. To reproduce, use a separate output copy, preserve the fixed inputs/settings and run <code>python run_reviews.py all</code>. The runner refuses to overwrite existing evidence. Responses may vary. For commands and flags see each archived run.json. The setup follows <a href="https://learn.chatgpt.com/docs/non-interactive-mode">official non-interactive Codex guidance</a>.</p>'
    report+='<h2>All raw final responses and scoring notes</h2><p>Expand an entry to inspect the exact response used for its score.</p>'+''.join(details)+'</body></html>'
    (OUT/'task-4-review-evaluation.html').write_text(report,encoding='utf-8')
    (OUT/'metrics.json').write_text(json.dumps({'primary':stats,'sensitivity':core,'reported_usage':usage},indent=2),encoding='utf-8')
    (OUT/'verification.json').write_text(json.dumps({'verified_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completed_reviews':48,'unique_session_ids':48,'case_and_prompt_hashes_match':True,'frozen_key_hash_matches':True,'empty_resource_discovery_runs':attempts,'substantive_external_context_reads':0,'archive_sha256':sha(archive),'results_sha256':sha(OUT/'results.csv')},indent=2),encoding='utf-8')
    print(json.dumps(stats,indent=2))
if __name__=='__main__': main()
