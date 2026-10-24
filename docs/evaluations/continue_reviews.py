from run_reviews import *
# No model/config/input changes; continue after preserved run 1 case 09.
for r in range(1,5):
    v=2 if r==4 else 1
    prompt=(OUT/f'prompt-v{v}.txt').read_text(encoding='utf-8-sig').strip()
    for i in range(1,13):
        if r==1 and i<=9: continue
        diff=(ROOT/f'ops/evals/cases/case-{i:02}.diff').read_text(encoding='utf-8-sig')
        run(f'run-{r}/case-{i:02}',prompt+'\n\n'+diff)
