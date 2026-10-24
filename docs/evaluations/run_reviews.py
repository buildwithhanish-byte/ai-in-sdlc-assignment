from pathlib import Path
import subprocess, json, hashlib, datetime, tempfile, os, sys, time
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'docs/evaluations'
EXE=Path(r'C:\Users\Kumar Hanish\AppData\Roaming\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe')
MODEL='gpt-6-astra'
DISABLE=['apps','shell_tool','unified_exec','browser_use','browser_use_external','computer_use','memories','multi_agent','plugins','remote_plugin','skill_search','hooks','image_generation','view_image','workspace_dependencies']
BASE=[str(EXE),'--no-daemon','-a','on-request','exec','--ignore-user-config','--ephemeral','--skip-git-repo-check','--json','--color','never','-s','read-only','-m',MODEL,'-c','model_reasoning_effort="medium"','-c','project_doc_max_bytes=0','-c','web_search="disabled"','-c','features.skip_host_skill_discovery=true']
for flag in DISABLE: BASE+=['--disable',flag]
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(data): return hashlib.sha256(data).hexdigest()
def run(label,prompt):
    dest=OUT/'raw'/label
    if dest.exists(): raise RuntimeError('Refusing overwrite '+str(dest))
    dest.mkdir(parents=True)
    (dest/'input.txt').write_text(prompt,encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='invoice-review-') as cwd:
        args=BASE+['-C',cwd,'-o',str(dest/'response.txt'),'-']
        meta={'start_utc':now(),'model':MODEL,'reasoning':'medium','command':args,'input_sha256':sha(prompt.encode()),'cwd_initial_files':list(Path(cwd).iterdir()),'status':'running'}
        (dest/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        started=time.monotonic()
        env=os.environ.copy()
        # Do not pass parent thread routing into a fresh CLI reviewer.
        for key in list(env):
            if key.startswith('CODEX_THREAD') or key.startswith('CODEX_INTERNAL'): env.pop(key,None)
        try:
            with (dest/'events.jsonl').open('wb') as stdout, (dest/'stderr.txt').open('wb') as stderr:
                completed=subprocess.run(args,input=prompt.encode(),stdout=stdout,stderr=stderr,cwd=cwd,env=env,timeout=600)
            meta['exit_code']=completed.returncode
        except subprocess.TimeoutExpired:
            meta['exit_code']=None;meta['error']='600 second timeout'
        meta['end_utc']=now();meta['elapsed_seconds']=round(time.monotonic()-started,2)
        events=[]
        for line in (dest/'events.jsonl').read_text(encoding='utf-8',errors='replace').splitlines():
            try: events.append(json.loads(line))
            except ValueError: pass
        meta['event_types']=sorted(set(e.get('type','') for e in events))
        meta['item_types']=sorted(set(e.get('item',{}).get('type','') for e in events if 'item' in e))
        meta['tool_items']=[e for e in events if e.get('item',{}).get('type') in ['command_execution','mcp_tool_call','web_search','file_change']]
        meta['thread_ids']=[e.get('thread_id') for e in events if e.get('type')=='thread.started']
        meta['usage']=[e.get('usage') for e in events if e.get('type')=='turn.completed']
        completed_tools=[e['item'] for e in meta['tool_items'] if e.get('type')=='item.completed']
        def empty_discovery(item):
            if item.get('server')!='codex' or item.get('tool') not in ('list_mcp_resources','list_mcp_resource_templates'): return False
            texts=item.get('result',{}).get('content',[])
            return len(texts)==1 and texts[0].get('text') in ('{"resources":[]}','{"resourceTemplates":[]}')
        meta['only_empty_resource_discovery']=bool(meta['tool_items']) and len(completed_tools)>0 and all(empty_discovery(t) for t in completed_tools) and all(e['item'].get('tool') in ('list_mcp_resources','list_mcp_resource_templates') for e in meta['tool_items'])
        success=meta['exit_code']==0 and (dest/'response.txt').exists() and (dest/'response.txt').read_text(encoding='utf-8').strip() and 'turn.completed' in meta['event_types'] and (not meta['tool_items'] or meta['only_empty_resource_discovery'])
        meta['status']='completed' if success else 'invalid_or_failed'
        meta['cwd_final_files']=[p.name for p in Path(cwd).iterdir()]
        (dest/'run.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        print(label,meta['status'],meta['elapsed_seconds'],flush=True)
        if not success: raise RuntimeError('Stopped on failed/contaminated run: '+label)
if __name__=='__main__':
    if sys.argv[1]=='pilot':
        run('pilot','Reply with exactly: READY')
    elif sys.argv[1]=='all':
        manifest={'started_utc':now(),'model':MODEL,'reasoning':'medium','only_changed_variable':'prompt v1 to v2 in run 4','case_hashes':{},'prompt_hashes':{},'retry_policy':'Stop on execution failure; retain failed attempt; retry only failure, never selective valid outputs.'}
        for i in range(1,13):
            p=ROOT/f'ops/evals/cases/case-{i:02}.diff';manifest['case_hashes'][p.name]=sha(p.read_bytes())
        for v in (1,2): manifest['prompt_hashes'][f'v{v}']=sha((OUT/f'prompt-v{v}.txt').read_bytes())
        manifest['answer_key_sha256']=sha((OUT/'scoring-key.json').read_bytes())
        path=OUT/'execution-manifest.json'
        if path.exists(): raise RuntimeError('Manifest exists')
        path.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        for r in range(1,5):
            v=2 if r==4 else 1
            prompt=(OUT/f'prompt-v{v}.txt').read_text(encoding='utf-8-sig').strip()
            for i in range(1,13):
                diff=(ROOT/f'ops/evals/cases/case-{i:02}.diff').read_text(encoding='utf-8-sig')
                run(f'run-{r}/case-{i:02}',prompt+'\n\n'+diff)



