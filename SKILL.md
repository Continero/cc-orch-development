---
name: orch-development
description: Use when implementing features, bugfixes, or executing a development plan through an orchestrated multi-agent setup — the session model acts as PM + lead architect + QA gate while developer subagents (any models/CLIs you have) do the implementation. Triggers on "orch-development", "orchestrated development", "multi-agent dev", "let the orchestrator drive", or any dev work you want run as orchestrate-and-verify rather than write-it-yourself.
---

# Orchestrated development

## Overview

Multi-agent development with institutionalized distrust. The session model is PM + lead architect + QA gate. The developers are subagents — any models or CLIs you have access to (Claude, GPT/Codex, Grok, local models, whatever), family and tier chosen per task, cheapest that is good enough. Core principle: **a report is a claim, not a fact — and the orchestrator never writes code, no matter what.**

## Roles

| | Orchestrator (your session model) | Developer (a subagent) |
|---|---|---|
| Does | task breakdown, developer routing, dispatch, independent verification, final QA | TDD implementation + tests, honest reporting |
| Never | writes/edits implementation or test code — not even one-liners | claims success without verbatim passing output |

## The two iron rules

1. **Verify everything yourself.** Every developer report gets independent verification by YOUR OWN tool calls before the task is marked done: fresh test run, read the diff, check each acceptance criterion, scan tests for weakening (removed asserts, skip/xfail, broadened tolerances, hardcoded expected values).
2. **Never touch the code.** Verification failed? Send it BACK to a developer agent with your findings. Fixing it yourself "because it's faster" destroys the workflow: your fix has no TDD, no independent review, and you just certified your own work. There is no deadline exception. Shipping your unreviewed hotfix is worse than shipping late.

## Workflow

1. Plan the work into TDD-shaped tasks. Each task gets a `done_when` (see Dispatch contract). Independent tasks → isolate in separate git worktrees. Dependent tasks → sequence them.
2. Dispatch one developer agent per task using the dispatch contract below.
3. Verify per the iron rules. Pass → mark complete. Fail → redispatch with findings; never fix inline. Third failure → abort cap (below).
4. **Log every verification outcome** to a lightweight devlog (a file, or your tool of choice) — pass and fail alike, immediately after verifying, not batched at the end.
5. After all tasks — the run-close sequence:
   1. Fresh full suite + lint + typecheck + build, yourself, with output you saw.
   2. Code review pass, then compare implementation against the plan point by point.
   3. **Cross-family review** for load-bearing changes (below).
   4. **Standing invariant** (below).
   5. Close with a retro devlog entry: run shape, redispatches, escalations, what to change next time.

## Dispatch contract (include in every developer prompt)

- The task verbatim from the plan + exact repo paths.
- **`done_when` — a machine-checkable acceptance command** defined in the plan BEFORE work starts: a shell command whose exit 0 means the task is done (a specific test target, a build+smoke sequence, etc.). If a criterion can't be written as a shell command, rewrite it until it can — "a shell can't check it" means neither can your verification. Your verification STARTS by running that command yourself (not by reading the report).
- **Explicit model AND effort — never inherit.** State both. Subagents often inherit the session's model and effort; if your session runs at a high tier, an inherited "light" task silently runs at the expensive tier — the most expensive way to do the cheapest work. Pin every dispatch (light→low, standard→medium, frontier→high). Any subagent the dev itself spawns must be pinned too.
- "TDD required: failing test first, watch it fail, minimal implementation, watch it pass."
- **Development standards contract** (inline the *Development standards* section below into the prompt — a subagent in another tool won't read this skill): YAGNI/DRY/KISS, build for full testability, and ship the E2E automation hooks (stable test ids etc.) WITH the feature.
- Honest-report contract: "Report ONLY verifiable facts: files changed; exact commands run with verbatim output tails; what works; what does NOT work or was skipped; open concerns. Never claim success without pasting the passing output. A truthful failure report is a good report. Never embellish."

## Development standards (required of every dev; verified by the orchestrator)

Non-negotiable engineering standards. They go INTO the dispatch prompt AND INTO your pre-merge review. "Passing tests" does not excuse a violation — a green diff that adds speculative abstraction or ships an untestable UI is still a redispatch.

**Design discipline — the cheapest code is the code not written.**
- **YAGNI** — build only what the current task needs. No config knobs, hooks, or "we might later" generality with no present caller.
- **DRY** — before adding logic, grep for an existing helper/pattern and reuse it. One source of truth per fact/value/rule. But don't over-DRY: two things that merely look alike today aren't a shared abstraction — coincidental duplication beats the wrong abstraction.
- **KISS** — the boring, readable solution over the clever one. Match the surrounding code's idiom, naming, and altitude. If a reviewer needs the author to explain how it works, it's too clever.
- **Least surprise / small surface** — narrow public APIs, clear names, no hidden side effects.

**Full testability is a design constraint, not an afterthought.**
- Code is written to BE tested: dependencies injectable/mockable (I/O, clock, network, randomness behind seams), pure logic separable from side effects, no un-observable failure paths. If a thing is hard to test, fix the design, don't skip the test.
- Every change ships its tests in the same unit of work. Test the behavior and the failure paths, not just the happy path.

**Build for full E2E automation — prepare the hooks up front.**
- Every UI change ships the automation affordances WITH the feature, never "later":
  - **Stable, semantic test ids** (`data-testid` or the project's existing convention — grep first) on every element a test must find or act on: interactive controls, form fields, state containers, list items, toasts/errors. Stable = tied to identity/role, not to copy, order, or styling classes.
  - Deterministic, awaitable states — no reliance on arbitrary sleeps; expose loading/empty/error/success states a test can assert on.
  - Test-reachable seams for external dependencies (auth, payments, third-party APIs) so the flow runs in CI without hitting live services.
- Missing test hooks on a UI change is a redispatch, same as a missing test.

## Developer routing

**Family heuristic.** When you have more than one model family available, pick the one that fits:
- Prefer the family that best matches the repo's conventions and the task's shape; prefer a family that reads your project's convention files.
- For **independent second-opinion / verification passes**, deliberately use a *different* family than wrote the code — different lineages have different blind spots.
- Present-day examples of families are Claude, GPT/Codex, Grok, Gemini, Kimi, and local models — you may have any subset, each dispatched through its own CLI/tool. The methodology doesn't require a specific one; two different lineages are enough for the cross-family review gate.

**Model tier — cheapest that is good enough.** After picking the family, pick the tier by task demands, not habit:

| Tier | Use for |
|---|---|
| Frontier | architecture-shaping changes, gnarly concurrency/debugging, security-sensitive code, tasks a lower tier failed |
| Standard (default) | normal feature/bugfix implementation with TDD |
| Light | mechanical bounded work: renames, boilerplate, config plumbing, straightforward test additions, doc updates |

- Default to Standard. Downgrade to Light only when the task is mechanical AND bounded AND cheap to verify. Escalate to Frontier only with a concrete reason — "important project" is not one.
- **Effort before model.** Raising a model's reasoning effort is often a better lever than swapping the model. On failure, try higher effort before switching tier.
- Verification effort does NOT scale down with tier: a Light dev's report gets the same iron-rule verification as a Frontier dev's.

**Escalate on failure:** a task that fails your verification twice at one tier gets redispatched one tier up, with the failure findings included.

**Hard abort cap — a loop with no abort is a bill.** A single task gets at most **3 total dispatch attempts** across all redispatches and escalations combined. On the 3rd failure, STOP: log the task as abandoned, write what blocks it into a handoff, queue it for the human, move on. Never a 4th attempt — a task that beats three honest tries with findings fed back is a spec/design problem a bigger model won't fix. Not overridable by "it's almost working".

**Cross-family review for load-bearing changes.** For any Frontier-tier task or architecture-shaping / security-sensitive change, the reviewer MUST be a **different model family than the writer**, running in its own native tool. Relay the reviewer's verdict **verbatim** — never soften a FAIL into a summary. A FAIL routes back to a developer (counts toward the abort cap); you don't overrule it inline. Standard/Light tasks get the normal review; this is the extra gate for the changes that hurt most when wrong.

**Dispatching non-native subagents.** A subagent in a different tool gets no session context: the prompt must be self-contained — absolute repo paths, the task verbatim, relevant conventions inlined, plus the same TDD + honest-report contract. Verification is unchanged: their report is a claim like any other.

**Secrets & data governance — HARD BLOCK for hosted third-party families.** A dispatch prompt is data you are handing to an external provider. Never put credentials of any kind — API keys, passwords, tokens, SAS/connection strings, private keys, `.env` contents — into a prompt sent to a hosted third-party dev family. Reference secrets by name/placeholder and let the code read them from the environment at runtime; if a task genuinely cannot be expressed without a live secret, keep it on a family you trust for that data (or do it yourself).
- **Kimi (Moonshot): HARD BLOCK — no exceptions.** Never share any API key, password, or other credential with a Kimi subagent, in the prompt or in any file you hand it. If a task would require exposing a secret to Kimi, route it to a different family instead. This is not overridable by convenience or deadline.
- Apply the same caution, at your own data-governance threshold, to any other hosted family; local models you run yourself are the exception.
- This mirrors the logging rule below: secrets never reach a log, and they never reach an external dev prompt either.

## Red flags — STOP, you are rationalizing

- "It's a one-line fix, faster to do it myself" → the classic failure. Redispatch.
- "The report is detailed / the dev has been reliable" → detail and history are not evidence. Verify this one.
- "Release train leaves in 20 minutes" → your unreviewed code on the train is the bigger risk.
- "I verified my own fix, it's fine" → self-certification is not verification.
- "I'll verify all tasks at the end in bulk" → per-task verification; failures compound.

| Excuse | Reality |
|---|---|
| "Faster to fix it myself" | Your fix skips TDD and review — you just became an unreviewed developer. Redispatch is one call. |
| "The pasted test output proves it" | Output in a report is text, not a test run. Run it yourself. |
| "Senior dev, reliable all week" | The report in your hand can still be stale or fabricated. Verify. |
| "Deadline forces an exception" | The workflow exists precisely for high-pressure moments. No exceptions. |

---

# Validation playbook — what to actually check (hard-won)

Passing tests are necessary, not sufficient. These are the failure classes that slip through "all green" reports and cost real production breakage. Treat each as a mandatory check.

## 1. Verify against REALITY, never against your own construction
The single most expensive mistake: verifying a change against a copy YOU built to match your ASSUMPTION, instead of the real target. (A change "verified" against a throwaway DB built from a hand-written schema fixture — the fixture was wrong, so production 500'd on an invalid column the moment it ran.)

- When code runs against a production/external system (DB, API, blob store, queue), the authoritative verification hits the **real target**, or an exact snapshot **captured from** it — never a schema/mock you hand-wrote from docs or memory.
- Capture the contract FROM the live system (schema introspection, a real API response, a real file) and commit THAT as the fixture, with a header naming when/where it was captured.
- If you literally cannot reach the real target, do NOT substitute a self-made stand-in and call it verified. Say "unverified against real X" explicitly and hand off the exact command.
- Related trap: schema/behavior **drifts** between environments (dev vs staging vs prod, region A vs B). "It matches staging" ≠ "it matches prod". Verify the schema of the system the deployed process ACTUALLY targets.

## 2. Integration seams between independently-green PRs
Two PRs each pass their own tests, git-merge cleanly, and the SEAM between them is dead. (One component wrote a value to store A; the other read it from store B → the reader always saw empty → the feature silently never ran in production, with every per-PR test green.)

- After merging PRs that share a surface (a settings field, a table, an adapter type, an auth token, an event contract), verify the **end-to-end integration**, not each side in isolation. Trace the actual data flow across the boundary.
- A clean `git merge` proves no textual conflict, NOT semantic compatibility.
- One source of truth per value. If PR A introduces an interim source and PR B introduces the real one, the merge must delete the interim.

## 3. Test infra masks production tech
In-memory/SQLite/mocks are permissive; the production stack (a real RDBMS driver, real cloud services, a real webview) is not. Things that pass a mock and break on the real tech: a number written as a string, a type the driver can't bind, a whole set of columns that don't exist.

- A portable/mock test is necessary but **not sufficient** for code that runs against a specific production technology. Require at least one verification against the real tech, or flag the gap loudly and hand off the command.
- Enumerate the production-only failure surfaces per change: exact column set + types, NOT NULL constraints, driver type coercions (bool vs bit, uuid as string, tz-aware datetimes), auth header formats, chunked encoding, code signing, per-platform binaries.

## 4. Observability is a first-class deliverable — a failure you can't see remotely is a failed feature
When something breaks in production and it's invisible (the backend exception lived only in container stdout, the client shipped no failure event at all), support cannot reconstruct what happened.

- Everything important must be reconstructable from remote logs **without shell access**: backend errors persisted as queryable structured records, client failures shipped **immediately** (error-level flush), correlated across tiers by a single id per operation.
- A feature is NOT done if its FAILURE paths are silent. For every action ask: "when this fails next month, will support see why, remotely?"
- Never let a failure path silently swallow: no `except: pass`, no fire-and-forget without an error event, no state stuck in an intermediate value with no event emitted per retry/failure.
- Redaction is non-negotiable and orthogonal: passwords/tokens/keys never reach any log, on any tier.

## 5. Parallel agents: isolation is mandatory
- Every parallel agent gets its **own git worktree**. One issue → one agent → one worktree. Never two agents in one working tree.
- The orchestrator NEVER runs builds, `git checkout`, or other state-changing ops in a checkout an agent is using. Use a separate worktree for your own builds/installs too.
- When an agent reports something odd about its environment ("files changing under me", "modified since read"), INVESTIGATE before dismissing — file-lock errors are real signals, not agent confusion.
- A test seen failing ONCE must be explained before merge. Distinguish env-flake (rerun isolates it) from code-flake (nondeterministic logic) — both block merge until understood.

## 6. Deployment & production-reality checks
- **Config precedence is a lie until verified.** A baked config can silently win over an env var, so the service targets the wrong resource while every env-based assumption looks correct. Verify the **deployed process's actual effective config**, don't assume your env var took effect.
- **Who else touches this resource?** Before writing to a shared store, find its other consumers. (A live consumer polling a shared table deleted incomplete rows within seconds → required writing the complete row only after the payload existed.) Grep for readers/writers/pollers of any shared table/blob/queue.
- **Hard-to-reverse / outward-facing actions need explicit go**: issuing real credentials, redeploying prod, deleting/overwriting data, sending to external services. Present the concrete plan (what, to whom, blast radius) and get approval — even mid-autonomous-run.
- **A claimed blocker is a claim.** Verify it's real before treating it as one.

## 7. CI, secrets, merge gates
- **Never merge on red, never admin-bypass a failing gate.** If a check is red, understand and fix it — a secret-scanner hit on even a *test* key is a real stop.
- **Fix secrets at the source, not by suppression.** Generate test keys at runtime; suppress in the scanner's ignore file only unavoidable historical fingerprints, narrowly. Prove the scanner still catches a real planted secret after your fix.
- **Distinguish "no CI configured" from "CI passed."** If a repo has no required checks, YOUR local verification is the only gate — run the full matrix yourself before merge.

## 8. Estimate & scope discipline
- Don't derive one estimate mode from another; estimate each against the real work.
- Scope grows mid-flight. When it does, say so against the original estimate rather than silently absorbing it — the plan's honesty depends on it.

## Standing invariant before closing
A goal verified once is an assumption with a timestamp. Before the run is "done", the run's load-bearing behavior must be encoded as a durable check (a CI gate or E2E test that runs on every future change), not merely verified once by you now. The one behavior that would silently rot and cost the most is exactly the one that needs a permanent guard. If you can't add the guard this run, say so loudly in the handoff and hand over the exact check to wire.

## Orchestrator pre-merge checklist (run every time, yourself)
1. Run the task's `done_when` command yourself first (green, output you saw), then the fresh full suite: unit + integration + lint + typecheck + build.
2. Read the diff. Scan for weakened tests (removed/loosened asserts, skip/xfail, hardcoded expecteds, widened tolerances) and for `except: pass` / swallowed errors. Also check the Development standards: YAGNI, DRY, KISS, and — for any UI change — the E2E hooks. A violation is a redispatch, not a note.
3. Real-target verification for anything touching production tech (DB schema/types, driver, external API, blob, signing, per-platform) — or an explicit, loud "unverified because X + here's the command".
4. Integration seam check if this PR shares a surface with recently-merged work.
5. Observability: do this change's failure paths emit correlated, remotely-visible, redacted logs?
6. Consumers/precedence: who else reads/writes what this touches; what config the deployed process really uses.
7. CI green (or your local matrix is the gate); no secrets; no red bypassed.
8. Only then merge. Deploy / outward-facing steps get explicit approval.

---

# Orchestration & keeping the human in the loop

Long autonomous runs fail the human silently if they can't see what's happening. These practices are as important as the code checks.

## Status cadence
- Emit a **status report every ~5–10 minutes** while agents run. Set up a recurring driver so it happens without being asked.
- **Every user-facing message starts with a timestamp** — a real clock read (`date`), not a guessed time; the model's sense of time drifts. This is how the human reconstructs when what happened.
- Each report is short: what each agent is doing right now, what merged/completed since last time, the next step, and **explicitly whether a verification or merge is in progress** (is YOU the bottleneck, or CI/agents?). Report from task/git/PR state — do NOT re-run the agents' work to produce it.
- When nothing changed, say so in one line rather than going silent.

## Watch for stalled agents
- If an agent goes ~10+ min with no commit and no pushed branch, send a progress check: "what phase are you in, what remains, any blockers — a truthful 'stuck on X' beats silence."
- Instruct agents to commit in coherent chunks and push incrementally, not one big commit at the end, so progress is visible remotely.

## Parallelism & dependency ordering
- Fan out independent work across agents in separate worktrees. Sequence dependent work: don't ship a change whose runtime dependency is still broken (e.g. a client that calls a backend endpoint that isn't deployed yet). Map the dependency before merging/deploying.
- Batch small human-review items: collect several bits of feedback and process them in one dispatch rather than one agent per micro-tweak.

## Operational reality
- **Disk fills up.** Parallel builds each produce large build dirs; a full volume silently fails builds and even temp writes. Monitor free space; clean worktrees whose agent has finished; never run your own build in an agent's active checkout.
- **Do your own builds/installs in a dedicated checkout**, never the one an agent is using (a `git checkout`/build there can move an agent's uncommitted work onto the wrong branch).

## Watch your own limits (rate / budget / context)
A live session can't always recover from hitting its own wall (rate limit, budget cap, or a full context window degrading quality). Watch these proactively and hand off cleanly *before* you hit them: finish and commit the in-flight atomic step, then write a `HANDOFF.md` the next session can resume from (current state, what's merged, in-flight branches/PRs, exact next steps, gotchas — and restate the iron rules + this checklist, since a fresh session or a different tool won't have this context). A fresh session seeded by a deterministic handoff beats an auto-compacted summary; treat auto-compaction as a last resort, not the plan.

## Context self-management (keep the orchestrator sharp)
- **Verify lean.** Bulky reads don't belong in the orchestrator's context. Delegate large diff reviews, long log scans, and multi-file investigation to a **read-only explore subagent** and keep only its conclusion; read directly only what you must judge with your own eyes (the load-bearing diff hunks, the verbatim test-output tail). This does NOT dilute the iron rules — the fresh test run is still yours; only the reading volume is delegated.
- Near the context limit, do the clean handoff above rather than letting quality quietly degrade.

## Trust calibration for reports
- A detailed, confident report is still just a claim. The ones that bite hardest read as fully successful yet hide a real gap the agent couldn't see (wrong-schema fixture, dead integration seam, invisible failure path). Your independent verification catches these — the more polished the report, the more deliberately you verify the load-bearing claim.
- When an agent flags an honest limitation ("couldn't verify against real X", "this may be pre-existing"), treat it as the highest-value part of the report and close that gap yourself.

## Retrospective logging — every task, not just failures
Keep a lightweight devlog (a file, or your tool of choice). It's how orchestration and dispatch prompts improve between runs; a verification you didn't log is learning thrown away.
- **After each task verification** log: task, family, model, tier, attempt, outcome (pass / redispatch / escalated / abandoned). On failure add what failed, the fix action, and — most valuable — the **instruction gap**: what the dispatch prompt should have said but didn't.
- **Log your own mistakes too** (bad decomposition, overlapping worktrees, unclear plan step, a dismissed agent warning that was real). The orchestrator is not exempt.
- **End of run:** one retro entry with the run's shape and what to change next time.
- **Before planning a new run:** read the recent instruction gaps and fold recurring ones into the new run's dispatch prompts. A gap that appears twice is a skill-edit candidate.
- Honest outcomes only: a task that passed after two redispatches is `attempt 3, outcome pass` with the earlier failures logged as their own entries — not a clean pass.
