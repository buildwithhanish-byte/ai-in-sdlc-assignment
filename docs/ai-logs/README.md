# AI augmentation evidence

These records describe how AI was used for this assignment and link back to the saved evidence.

- [Structured records](augmentation.jsonl): one JSON object per line, using the requested augmentation fields plus provenance and execution evidence.
- [Validation results](validation.json): record counts, source hashes and checks.
- [Compiler](build_logs.py): rebuilds the records offline from the original summaries and review archive. Run with Python 3 from any directory. It does not run AI sessions or application tests.

## What is covered

| Records | Source | Coverage |
| --- | --- | --- |
| Five task summaries | Existing per-task augmentation summaries | Retrospectively compiled. Actions, outcomes, known human decisions and limitations. Some exact prompts are preserved for Tasks 1 and 2. |
| 48 review interactions | Automatically captured Task 4 inputs, responses, events and run metadata | Actual prompts/diffs, model, timestamps, session IDs, outputs, execution status and source references. |
| One pilot | Automatically captured Task 4 pilot | Unscored setup check, clearly labelled separately from the 48 reviews. |

The existing summaries and raw archives are preserved. These structured records were assembled later; they are not presented as an automatically captured history of every assignment interaction.

## How to read the fields

- `record_origin` distinguishes retrospective summaries from normalization of automatic captures.
- `timestamp` is the original execution time where captured. It is null for summary-only records; their historical date is recorded separately. No precise time was inferred from a date.
- `request_kind` distinguishes a task description from an exact saved prompt. `interactions` includes the exact prompts reproduced in the original summaries where available.
- `model`, `mode`, `skills_used`, `subagents_used` and `mcp_tools_used` are null when the source does not establish them. An empty array indicates a recorded restriction or absence within the stated capture scope; it does not describe every other assignment session.
- Review `mode` is normalized to `agent` from the recorded CLI `exec` invocation. Review skills and multi-agent features were disabled. Some sessions made empty resource-discovery calls; inspect `observed_tool_items` and the original events for those calls.
- `human_decision` records only the human involvement supported by the summaries. Agent-run tests and AI-assisted scoring are not described as independent human verification.
- `status` for automatic captures preserves the original runner status. One review was flagged `invalid_or_failed` by the initial strict discovery check and later included with a documented scoring amendment. The review report and execution protocol explain this; the original status is not overwritten.
- `action_verification` records what was checked. A completed execution does not imply a correct answer or a passing review finding.
- `artifacts` are repository-relative links. `execution_evidence.entries` names files inside the existing review ZIP.

## Limits and integrity

Full original conversations for Tasks 1, 2, 3 and 5 are not included in this package. Their exact model, event-level tool use, skills, sub-agents and session IDs cannot be recovered from summaries alone. These are explicit gaps, not assertions that no such capabilities were used. Original conversation exports can supplement this package later after checking for sensitive information.

Task 4 input hashes use UTF-8 text with LF line endings, matching the original runner's input bytes. Windows CRLF in saved text files is normalized before checking; source archives are unchanged. Validation verifies linkage and structure, not the truth of every conclusion.

No historical commit reference is assigned to an interaction without evidence. The task reports retain their design, source and measurement limitations. This package adds traceability and does not resolve those substantive limits.
