from pathlib import Path
from datetime import datetime
import csv,collections,statistics,json,hashlib,html
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'docs/risk-and-measurement'
source=ROOT/'ops/pipeline/run-timings.csv'
rows=list(csv.DictReader(source.open(encoding='utf-8-sig')))
totals=collections.defaultdict(float);conclusions={}
for row in rows:
    number=int(row['run_number']);totals[number]+=float(row['duration_seconds'])
    if number in conclusions:assert conclusions[number]==row['conclusion']
    conclusions[number]=row['conclusion']
interval=(datetime.fromisoformat('2026-01-14T09:58:00+00:00')-datetime.fromisoformat('2026-01-13T17:22:08+00:00')).total_seconds()
with (OUT/'scenario-run-totals.csv').open('w',newline='',encoding='utf-8') as f:
    writer=csv.writer(f);writer.writerow(['run_number','sum_recorded_step_seconds','conclusion'])
    for n in sorted(totals):writer.writerow([n,totals[n],conclusions[n]])
result={'classification':'Computed from invented scenario evidence; not observed live production','pipeline_source':'ops/pipeline/run-timings.csv','pipeline_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'run_count':len(totals),'recorded_step_rows':len(rows),'median_sum_recorded_step_seconds':statistics.median(totals.values()),'failed_runs':sum(v=='failure' for v in conclusions.values()),'release_author_to_deploy_seconds':interval,'release_sample_size':1,'release_start_source':'ops/incidents/INC-2041/deploy-diff.patch: Date header','release_end_source':'ops/incidents/INC-2041/alert.md: release at 09:58Z on 14 January 2026','limitations':['Patch Date is an author timestamp, not independently verified commit/merge time.','The sample was selected as an incident; it is not representative of release performance.','Summed steps omit queue time and any gaps; failed runs may stop early.','CI failure counts are not production change-failure rate.','No review timestamps or complete deployment denominator are available.']}
(OUT/'scenario-measurements.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
section=f'''<h2>Additional calculations from the supplied scenario</h2><p>These values are calculated from the assignment's evidence packs. Their figures are explicitly invented for the exercise; they are not live production measurements.</p><table><tr><th>Observation</th><th>Computed value</th><th>Limit</th></tr><tr><td>Release 2.14.0 author-to-deployment interval</td><td>16 hours, 35 minutes, 52 seconds; one release</td><td>From the patch's Date header (13 January 17:22:08Z) to the alert's stated deployment time (14 January 09:58Z). This is an author-time proxy, not verified commit-to-production lead time. The incident-selected release is not a representative baseline.</td></tr><tr><td>Median summed CI step durations</td><td>{statistics.median(totals.values()):g} seconds (31 minutes, 15.5 seconds); 20 runs</td><td>Calculated by grouping the 378 supplied step rows by run number, summing duration_seconds, then taking the median. Includes failed/shortened runs; not wall-clock duration or review turnaround.</td></tr></table><p>The dataset has 18 successful and 2 failed runs, but 2/20 is a scenario CI failure fraction, not production change-failure rate. Raw totals and assumptions are in <a href="scenario-run-totals.csv">scenario run totals</a> and <a href="scenario-measurements.json">scenario calculation details</a>. Reproduce with <code>python docs/risk-and-measurement/calculate_scenario.py</code>, then rebuild the main report.</p>'''
(OUT/'scenario-section.html').write_text(section,encoding='utf-8')
print(json.dumps(result,indent=2))
