SUBMISSION NOTE: Supporting files referenced below are bundled in reproduction-evidence.zip. See SUBMISSION.txt for extraction and replay. No evidence was discarded.

Task 4 additional review cases: verified preparation, not an evaluation run

Outcome
-------
Confirmed a check-then-write race in the existing ApprovalService.Approve and
Reject paths. The deterministic source-copy test made two calls pass the
pending-state check before either wrote its decision. Both returned success.
The same strengthened test against the isolated correction returned exactly
one success and one InvalidOperationException, with both scheduling hooks active.

Files to give the reviewer, separately in fresh sessions:
  ../cases/case-11.diff
  ../cases/case-12.diff
Give only the selected diff and the review prompt in ../README.md. Do not give
this directory, expected answers, source snapshots, test logs or the other case.
No reviewer has been invoked and no evaluation results or scores were produced.
The existing results.csv and earlier assignment deliverables were not changed.

Concrete trigger and impact
---------------------------
1. A PendingApproval invoice is returned by the shared in-memory repository.
2. Request A's service checks that it is pending.
3. Request B's different service instance checks the same shared object while
   it is still pending.
4. Both write their decision fields and return normally.

For approve/approve, the same invoice is accepted twice and its one DecidedBy /
DecidedAt pair can be overwritten by the other call. The captured run's final
actor is not a promised ordering. For approve/reject, contradictory decisions
can both return success; a single final status cannot represent both outcomes.
Do not infer duplicate payments, messages, database writes, or external effects:
none of those components exist in this application's current approval path.

Beginner explanation: each person looks at a sign saying "waiting for a
decision". Both look before either changes the sign. Both then say "done".
Locking only the cabinet used to find or save the invoice does not prevent the
two people from making their decisions at the same time.

Code evidence (paths relative to repository root)
------------------------------------------------
- backend/src/InvoiceApp.Domain/ApprovalService.cs: Approve, Reject,
  EnsurePending and Find. State check precedes mutation with no common lock.
- backend/src/InvoiceApp.Api/InMemoryInvoiceRepository.cs: GetById returns the
  stored mutable Invoice itself; GetById and Update lock individual list access.
- backend/src/InvoiceApp.Api/Program.cs: singleton IInvoiceRepository registration,
  request-scoped ApprovalService registration.
- backend/src/InvoiceApp.Domain/Invoice.cs: mutable Status and decision fields.
- backend/tests/InvoiceApp.Tests/ApprovalServiceTests.cs: original seven tests
  exercise sequential behavior, not the demonstrated interleaving.
- backend/tests/InvoiceApp.Tests/FakeInvoiceRepository.cs: also shares the same
  invoice reference; used as required by project conventions.
- backend/src/InvoiceApp.Api/Controllers/ApprovalsController.cs: Approve and
  Reject call the service with the session username through Handle.
- backend/src/InvoiceApp.Api/Controllers/ApiControllerBase.cs: Handle maps a
  normal service return to 200 and InvalidOperationException to 409. This is
  source-based HTTP mapping evidence, not an executed HTTP test result.

What the deterministic test proves
---------------------------------
The source snapshots were copied from the real application before testing.
prepare.py inserts one test-only hook after the first EnsurePending call in
Approve and one in Reject. The hook uses a two-party Barrier. Dedicated threads
and two service instances share one repository. Both checks must finish before
either call can continue to the original writes or the corrected critical section.
The hook adds scheduling, not a new business rule or detached invoice copies.
Both real in-memory and fake repository implementations are exercised.

No sleeps are used. The 15-second barrier timeout is a deadlock watchdog and
throws if reached; it is not used to arrange the schedule or to decide success.
The strengthened test asserts TWO actual hook visits, ONE success, ONE conflict,
and final status/actor matching the successful call. Which contender wins is
not prescribed, but the success/conflict counts are deterministic under this
schedule. No assertion was weakened between the verified original/corrected runs.

This is an instrumented service-level interleaving test, NOT a real HTTP
concurrency/load test. It does not execute routing, authentication, serialization
or network requests, measure how often the race occurs, or establish throughput.
It forces one legal schedule that can occur between existing statements.

Correction and limits
---------------------
The isolated correction retains the initial pending check, then locks the
shared invoice object and rechecks PendingApproval inside that lock before
changing Status, actor, time, reason or calling Update. Approve and Reject use
the SAME object's monitor, even across different service instances. The loser
sees the winner's state and throws before it changes metadata. Locking each
service instance separately would not protect separate requests.

The early check is redundant for serialization but retained for minimal source
change and an identical scheduling seam. It is the in-lock recheck and shared
critical section that protect the transition. Both hooks remain outside the
critical section, so both calls still reach the barrier in the corrected run.
verification.json checks identical test/hook SHA-256 hashes and that removing
only the two hook lines from each run's source gives its uninstrumented original
or corrected source exactly.

This correction is deliberately scoped to in-process approve/reject decisions
on the same already-submitted object. It does not prove safety of concurrent
Submit/Delete, arbitrary external mutation, repositories returning copies,
database transactions or multi-process deployments. The neutral contract in
each diff states these boundaries. The clean classification is within that
contract, not a claim that the entire existing application is free of defects.
No target-state database, messaging or payment design was implemented.

Verified results and invalid attempt
-----------------------------------
Authoritative pair:
  runs/original-verified: exit 1; 4 concurrency tests failed. Each had two
    successes, zero conflicts, and two hook visits. Expected successes=1,
    actual successes=2. These are assertion failures, not timeouts/build errors.
  runs/corrected-verified: exit 0; 11 tests passed: the SAME 4 concurrency
    cases plus the 7 copied existing ApprovalServiceTests. Each concurrency
    case had one success, one conflict and two hook visits.

Each run contains output.txt, results.trx, run.json (commands, input hashes,
exit code, UTC time), and the exact service/test/hook source used.
The pre-existing DomainArchitectureTests and recorded assignment test evidence
were not altered or rerun. These 11 tests belong to the isolated fixture.

Preserved history:
  runs/original: initial reproduction; all 4 failed as expected, with the
    barrier active but before the explicit hook-visit assertion was added.
  runs/corrected: INVALID as correction evidence, despite 11 passing tests.
    See INVALID-RUN.txt. Preparation failed and the shell continued with
    uninstrumented original source. That passing run is not counted as a fix.
    The matcher was corrected, hook-visit assertions added, and input/hash
    checks introduced; both authoritative runs then used the identical test.
The earlier interrupted file-creation call left no files. Sandbox process
startup also failed; approved execution outside the sandbox was used. Neither
is described as a test result. Raw failed/invalid attempts have not been erased.

Review-case construction
------------------------
The cases use ordinary diff --git / --- / +++ / @@ unified diff headers matching
the existing format. They are independent review examples against the SAME
synthetic baseline in review-base/. That baseline removes only Approve/Reject
from the captured service, so each case presents its decision bodies as added
code. Full class context and a neutral repository/lifetime contract make each
case readable without supplying repository access. The candidate methods are
the uninstrumented original or verified correction; scheduling hooks, tests,
verdicts and reproduction results are absent from the diffs.

This is review-fixture packaging, not a claim these are historical commits or
patches to apply to the current checkout, which already contains Approve/Reject.
The baseline and candidates are saved separately. build_cases.py first checks
the verified results, instrumentation and unchanged existing files; it refuses
to overwrite already-produced cases. final_checks.py verifies standard patch
applicability and reconstructs both candidate files from their diffs.

Provenance and relationship
---------------------------
This defect was investigated during this assignment with AI assistance. It was
not encountered in the user's previous employment and is not a customer or
production incident. The data and actor names in the test are synthetic.
case-11 and case-12 are a related defective/corrected pair from ONE investigation,
not two independent incidents. Future comparisons must disclose that correlation.
If the marking rubric strictly requires a past-employment incident, this pair
does not meet that provenance requirement; do not relabel it as personal history.
This supplements the earlier preparation log without rewriting it.

See commands.txt for reproduction, expected-answers.txt for the scoring key,
and verification.json / final-checks.json for integrity and patch checks.
