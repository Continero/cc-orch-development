---
name: orch-development
description: Use when implementing features, bugfixes, or executing a development plan through an orchestrated multi-agent setup — the session model acts as PM + lead architect + QA gate while developer subagents (any models/CLIs you have) do the implementation. Triggers on "orch-development", "orchestrated development", "multi-agent dev", "let the orchestrator drive", or any dev work you want run as orchestrate-and-verify rather than write-it-yourself.
---

# Orchestrated development

**Two files, and the split axis is *when a reader needs it and who the reader is* — never topic.** Every load-bearing gate is stated here in full: the two iron rules, the dispatch contract, the validation playbook, the pre-merge checklist. You never need another file to know *what* to check or *what* to require, because a gate that leaves the always-loaded file stops being a gate. The one companion file is `DEV_BRIEF.md`, the canonical dev-facing contract — it is **data you paste verbatim into every dispatch**, not a document you consult. A rule and the story that justifies it are different granularities; a rule and the prose you hand a developer are different readers.

## Overview

Multi-agent development with institutionalized distrust. The session model is PM + lead architect + QA gate. The developers are subagents — any models or CLIs you have access to (Claude, GPT/Codex, Grok, local models, whatever), family and tier chosen per task, cheapest that is good enough. Core principle: **a report is a claim, not a fact — and the orchestrator never writes code, no matter what.**

## Roles

| | Orchestrator (your session model) | Developer (a subagent) |
|---|---|---|
| Does | task breakdown, developer routing, dispatch, independent verification, final QA | TDD implementation + tests, honest reporting |
| Never | writes/edits implementation or test code — not even one-liners | claims success without verbatim passing output |

## Orchestrator mode — the lever is breadth, not depth

There are two ways to spend more on a hard problem: turn your own reasoning effort up, or fan the work out across agents and verify adversarially. **For this role the second is strictly better** — one model thinking harder still produces one opinion, and this skill exists because one opinion is not evidence. So:

- **Spend on parallel agents and adversarial verification before you spend on your own reasoning tier.** If your harness has an explicit multi-agent / orchestration mode, that is the setting to turn on; a maxed-out solo reasoning effort is not.
- **Solo only for the trivial** — a conversational turn, a one-line mechanical edit, reading a file. Everything else gets decomposed and covered in parallel.
- **Multi-phase work gets several fan-outs in sequence, not one giant one**: understand → design → implement → review, reading each result before choosing the next phase. That is what keeps the orchestrator in the loop, which is the whole point of the role.
- Breadth changes **how you think, never what you are allowed to do.** The two iron rules survive untouched: a fan-out that produces twenty confident findings has produced twenty claims. The gate, the fresh test run, and the live check are still yours.
- Cost is not the constraint here; **capacity is** (see *Watch your own limits*). A wide fan-out burns the same pools as hand-dispatched devs — check before you launch it, not after.

## The two iron rules

1. **Verify everything yourself.** Every developer report gets independent verification by YOUR OWN tool calls before the task is marked done: fresh test run, read the diff, check each acceptance criterion, scan tests for weakening (removed asserts, skip/xfail, broadened tolerances, hardcoded expected values).
2. **Never touch the code.** Verification failed? Send it BACK to a developer agent with your findings. Fixing it yourself "because it's faster" destroys the workflow: your fix has no TDD, no independent review, and you just certified your own work. There is no deadline exception. Shipping your unreviewed hotfix is worse than shipping late.

## Workflow

0. **Survey what already exists BEFORE building anything — reconcile the plan with the FULL repo state, never a single checkout.** Before planning/dispatching, especially for net-new or foundational work: `git fetch`, then read the full log across branches, the branch list, and the PR list (open AND recently merged), and grep the codebase for the tables / routes / migration numbers / subsystem you are about to create. A plan that says "build X from scratch" or "X doesn't exist yet" is a **HIGH-blast-radius negative** — valid ONLY after you've confirmed X is not already on the main branch, a sibling branch, or an open/merged PR. If any investigation — yours or a subagent's — reports "this doesn't exist," that is a CLAIM to verify, not a license to greenfield (see validation playbook §1b).
1. Plan the work into TDD-shaped tasks. Each task gets a `done_when` (see Dispatch contract). Independent tasks → isolate in separate git worktrees. Dependent tasks → sequence them.
2. Dispatch one developer agent per task using the dispatch contract below. **On the first dispatch, immediately arm the monitor** (see Status cadence) — a dispatch without an armed monitor is an incomplete dispatch.
3. Verify per the iron rules. Pass → mark complete. Fail → redispatch with findings; never fix inline. Third failure → abort cap (below).
4. **Log every verification outcome** to a lightweight devlog (a file, or your tool of choice) — pass and fail alike, immediately after verifying, not batched at the end.
5. After all tasks — the run-close sequence:
   1. Fresh full suite + lint + typecheck + build, yourself, with output you saw.
   2. Code review pass, then compare implementation against the plan point by point.
   3. **Cross-family review** for load-bearing changes (below).
   4. **Standing invariant** (below).
   5. Close with a retro devlog entry: run shape, redispatches, escalations, what to change next time.

## Dispatch contract (include in every developer prompt)

**STEP ONE OF EVERY DISPATCH: paste `DEV_BRIEF.md` verbatim, ahead of the task.** It is the canonical dev-facing contract and it lives in one versioned file precisely so it cannot be retyped from memory — reconstructing it by hand is how the `## Git` requirement went missing and a dev finished green with 784 tests passing and nothing committed. It carries the developer-role override, the no-backgrounding rule, commit-before-any-long-command, "lint must emit zero warnings, not merely exit 0", TDD and what a valid red is, the full development standards (YAGNI/DRY/KISS, testability, E2E affordances, auditable logging), the provider-vocabulary probing rules, and the honest-report contract. Do not summarise it, do not trim it, and never assume a dev in another tool will find it — a subagent outside your harness reads no skill files at all.

Everything below is what **you** owe per dispatch and cannot delegate, because only you have the plan, the repo state and the tier decision. The brief covers the dev's side; this list is yours.

- The task verbatim from the plan + exact repo paths.
- **`done_when` — a machine-checkable acceptance command** defined in the plan BEFORE work starts: a shell command whose exit 0 means the task is done (a specific test target, a build+smoke sequence, etc.). For **user-facing behavior it includes an E2E path** driving the real flow via test ids — and the plan names the test ids and observable states the dev must add, so the affordances ship in the first commit rather than being retrofitted. If a criterion can't be written as a shell command, rewrite it until it can — "a shell can't check it" means neither can your verification. Your verification STARTS by running that command yourself (not by reading the report).
- **For any change to product source, `done_when` MUST include the project's full unit suite**, not just the targeted test or E2E. A narrow acceptance command hides regressions in the code the change didn't target — a fix can pass its own new E2E while breaking an existing unit test, and a green narrow gate reads as "done". The targeted test proves the feature; the full suite proves you didn't break the rest.
- **For any layout/visual task, the first dispatch carries an explicit visual spec** — sizes, positioning, per-breakpoint order, spacing, transitions. E2E cannot see layout, so a behavior-only contract yields wrong positioning that no test catches and only visual QA finds, wasting a redispatch. Vague directions ("alternate the sides", "make it balanced") must be spelled out per case.
- **Pre-verify the build toolchain before dispatching build/compile-dependent work.** Establish a green baseline yourself in a dedicated checkout first (restore/build), so a dev's failure is attributable to their change rather than a broken local toolchain. A dispatch that assumes the build works can burn a whole attempt on an environment problem.
- **Deployment/topology contract — for any task touching deploy, config, hosts, or environments: inline the relevant `DEPLOYMENT.md` rows verbatim** (target environment, host/container, datastore, deploy branch + trigger, rollback) and require the dev to **update `DEPLOYMENT.md` in the same commit** if the change alters any of it. A non-native dev has no idea where the thing runs and won't go looking; without those rows inlined it will assume `main` deploys to "prod" and be wrong (validation playbook §6).
- **Explicit model AND effort — never inherit.** State both. Subagents often inherit the session's model and effort; if your session runs at a high tier, an inherited "light" task silently runs at the expensive tier — the most expensive way to do the cheapest work. Pin every dispatch (light→low, standard→medium, frontier→high). Any subagent the dev itself spawns must be pinned too.
- **Provider-vocabulary capture — for any task that sends a third party a string in THEIR vocabulary** (metric/scope/field/edge names, enum values, option keys, API version pins, header names): **you fetch the provider's doc page first, save it under `docs/research/` with its URL and fetch date, and quote the relevant extract verbatim into the prompt.** The dev implements exactly that extract; it must never be left to research or recall the vocabulary itself, because an unclear provider page turns into a guess. The dev-facing half of the rule is already in `DEV_BRIEF.md`. What is **yours** is the capture, the verbatim extract in the prompt, and pre-merge item 3b, where you probe each name and read the output with your own eyes (validation playbook §1c).
- **TDD, the development standards, and the honest-report contract are in `DEV_BRIEF.md`** — pasting it is what puts them in the prompt. Your job is not to restate them but to **reject work that violates them at pre-merge**: a green diff carrying speculative abstraction, a re-implemented helper, an untestable UI, or a silent failure path is a redispatch, and "the tests pass" does not excuse it.

## Development standards — they live in `DEV_BRIEF.md`

The engineering standards every dev must follow (YAGNI/DRY/KISS and least surprise, testability as a design constraint, E2E affordances built with the feature, and auditable logging on every decision and outcome) are **not restated here**. They are dev-facing prose, so they live in `DEV_BRIEF.md` as one versioned artifact and reach the dev by being pasted. A second copy inline would give two sources of truth for the same rules, and the one nobody edits is the one that gets read.

**What stays yours is the enforcement.** These standards go into your pre-merge review, not just into the prompt, and "passing tests" never excuses a violation:

- **YAGNI** — a green diff that adds a config knob, a hook, or an abstraction layer with no present caller is a redispatch, not a nice-to-have.
- **DRY** — a re-implemented helper that already existed is a redispatch; grep before you accept, the same way the dev was told to grep before writing.
- **KISS / least surprise** — if you need the dev to explain how it works, it is too clever for the next reader, who will be a different model.
- **Testability** — an un-observable failure path or a seam that cannot be stubbed is a design defect to send back, not a testing inconvenience to wave through.
- **E2E affordances** — a UI or flow change without stable test ids and awaitable states is a redispatch, exactly like a missing test. This is also what makes the run-close *Standing invariant* possible at all: the durable E2E guard can only exist because the affordances shipped with the first commit.
- **Auditable logging** — checked in detail at pre-merge item 5. A silent path, a swallowed error, or a business action with no `info` line is a redispatch (validation playbook §4).
- **Visual bar** — frontend-facing work gets screenshotted and inspected at pre-merge item 7. A visual defect is a redispatch; green tests never certify how something looks.

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
- **Let your own data demote a model, not your impression of it.** Log outcome per model (see Retrospective logging) and check the fail rates each retro. A model that reads as fine can carry a fail rate several times another's at the same tier — when the log says so, drop it out of default routing and escalate off it on the FIRST failure rather than the second. Re-check as more data lands; a demotion is a reading of the log, not a permanent verdict.

**Escalate on failure:** a task that fails your verification twice at one tier gets redispatched one tier up, with the failure findings included.

**Hard abort cap — a loop with no abort is a bill.** A single task gets at most **3 total dispatch attempts** across all redispatches and escalations combined. On the 3rd failure, STOP: log the task as abandoned, write what blocks it into a handoff, queue it for the human, move on. Never a 4th attempt — a task that beats three honest tries with findings fed back is a spec/design problem a bigger model won't fix. Not overridable by "it's almost working".

**Cross-family review for load-bearing changes.** For any Frontier-tier task or architecture-shaping / security-sensitive change, the reviewer MUST be a **different model family than the writer**, running in its own native tool. Relay the reviewer's verdict **verbatim** — never soften a FAIL into a summary. A FAIL routes back to a developer (counts toward the abort cap); you don't overrule it inline. Standard/Light tasks get the normal review; this is the extra gate for the changes that hurt most when wrong.

**Dispatching non-native subagents.** A subagent in a different tool gets no session context: the prompt must be self-contained — absolute repo paths, the task verbatim, relevant conventions inlined, plus the same TDD + honest-report contract. Verification is unchanged: their report is a claim like any other. Two constraints that decide the shape of the task:

- **A one-shot CLI mode (`-p`/`--print`) has a bounded turn budget — don't hand it a long multi-step loop.** Write + build + serve + run E2E + commit in a single one-shot call exhausts the turns mid-task and returns partial work (or nothing) while reading like it ran. Decompose instead: the dev WRITES the files (bounded, one deliverable), the orchestrator RUNS and verifies. Interactive/resumable modes are for the iterative work.
- **Know what each sandbox cannot do.** Some hosted dev sandboxes can't launch a headless browser at all — routing screenshot / browser-driven work there burns an attempt on an environment wall, not on the task. Keep browser-dependent work (visual QA rendering, Playwright-driven asset generation) on a family that can actually run a browser.

**Never truncate a dispatch report.** Do not pipe a dev or background command through `tail`/`head`/`sed` — write the FULL stdout to a file and read it whole. A truncated report is an unverifiable claim: you'd be "verifying" against a mutilated report, which breaks iron rule #1. If the report is genuinely too large for your context, hand the whole file to a read-only subagent to summarize — never lose it to a pipe.

**Background dispatch is where silent failures live.** A background job that dies can leave no notification at all, so you find out at your next status tick instead of when it happened — long after the wall-clock was wasted.
- **A readiness check often proves less than it claims.** "Authenticated: yes" may only test that a credential file EXISTS, not that the token inside is still valid — an expired token then kills the job instantly with "not signed in". **Foreground-probe the family once per session** with a tiny task before trusting it; setup passing is necessary, not sufficient.
- **Prefer foreground with a generous timeout** for anything correctness-critical or multi-step. Reserve background for genuinely long, low-stakes work.
- **If you must background:** poll the log within ~30 s for auth/startup errors before believing it started, re-poll every status tick, and require a **mid-run commit checkpoint** in the prompt so a dead run still leaves partial work on the branch.
- On a first-dispatch auth death, re-login is the human's step — meanwhile auto-route the task to another family rather than burning the run waiting.

**Orchestrator fallback — plan for your own family dying.** If the orchestrator's own model/account becomes unavailable mid-run (limits exhausted, outage), orchestration moves to another family: while your session still responds, write `HANDOFF.md` and carry the context over, then keep orchestrating there. The workflow contract has to travel IN the handoff — the other tool does not read this skill or your repo convention files, so `HANDOFF.md` must restate the iron rules, point at the pre-merge checklist, and carry current task state. A fallback you thought about after the session died is a fallback you don't have.

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

## 1b. "It doesn't exist yet" is the most dangerous conclusion — verify prior art before greenfield
A subagent investigated and reported that a foundational subsystem "does not exist", so a whole parallel implementation got built from scratch — while a COMPLETE version already sat on the main branch, merged a week earlier. The result: two different implementations, colliding migration numbers that could not be merged, and an entire run wasted. A negative that authorizes building from scratch has the highest blast radius of any claim, so verify it hardest.

- Before building any net-new subsystem/foundation: `git fetch`, then scan the log across ALL branches, the branch list, and the PR list (open AND recently merged), and grep the code for the tables/routes/migrations you're about to create. Confirm the thing truly isn't already on the main branch, a sibling branch, or an in-flight PR.
- The investigation must run against real git history + remote + PRs, **not a single working-tree snapshot** — a checkout can lag the main branch by many commits and PRs. That's exactly how it happens: the start-of-run explore reads a stale base and concludes "nothing exists".
- Before minting a migration / schema-version number, confirm that number isn't already taken on another branch. Two parallel `0011`s that differ are instantly unmergeable.
- When the human's ask is "simplify / fix the existing X", the default assumption is that X EXISTS — go find it before proposing to build one. If your reading of the request has you building rather than changing, re-read it: you probably mislocated the existing thing.

## 1c. Provider vocabulary: documentation is a HYPOTHESIS, a live call is the evidence — and "the dev says it verified" is neither

Every string you send a third party in *their* vocabulary — metric names, scope names, field/edge names, enum values, option keys, API version pins, header names — is a claim about their system that only their system can settle.

The incident: four analytics metric names shipped under the source comment *"all four confirmed present in vN"*, citing a research document by file and section. That document was sourced from the provider's own reference and changelog, and the deployment did run vN. Live vN rejected two of the four, the provider rejects the **entire** call when one name is bad, and the endpoint therefore returned nothing for every record — for as long as it had existed. It was found weeks later, by accident, during an unrelated probe. Two failures, and the second one is the orchestrator's: **the documentation was read, cited precisely, and was still wrong**, so "I checked the docs" is not a verification result; and **a claim laundered into a source comment is still a claim**, more dangerous there than in a report because the next reader treats it as settled history.

- **A provider-vocabulary constant may not merge until the orchestrator has seen it accepted by the live provider.** Not the dev — you. One command whose output you read.
- The docs stay mandatory as the *starting point*: the dev records the URL and the date fetched, not a remembered name, and not a citation to another document inside the repo (that is how a stale fact gets a second life). At the incident above, the documentation's stated replacement names turned out correct and live-accepted, while two names reasoned out from a provider blog post were both rejected — the docs were the only reliable source of candidate names, and the live call the only reliable judge of them.
- **A comment may not assert "confirmed"/"verified" without saying by what.** `# confirmed present in vN (docs §9)` is a citation; `# probed live 2026-01-14: accepted, 1 row` is evidence. Require the second form, with the date — a live fact has a shelf life, and the date is what lets the next reader judge it.
- **Probe each name individually, never only as a set.** A provider that rejects the whole request on one bad name tells you nothing about which one; per-name probing turns a useless generic error into an actionable table.
- **Design for one name dying.** A fixed vocabulary set is a total outage the day the provider deprecates one member. Degrade: drop the rejected name, keep the rest, and log loudly *which* name was dropped — a silently shrinking result set is its own defect.
- **The four-step capture procedure, in order, none of them skippable:** (1) you fetch the provider's doc page yourself and save it under `docs/research/<provider>-<topic>.md` with its URL and fetch date; (2) the dispatch quotes the relevant extract verbatim, so the dev implements exactly that rather than researching it; (3) re-fetch and diff before relying on a capture older than the change, updating the date — the repo in the incident *had* a local capture, cited by file and section, and it was months stale, because a local document nobody re-fetches is a fossil with a citation; (4) probe live anyway.
- **When a doc mentions a deprecation, capture its DATE and SCOPE, not just the version number.** Provider deprecations are frequently date-based across *all* API versions, which makes a version pin worthless — while a "deprecated above vN" note reads misleadingly like "fine on vN".
- **Cheapest way to run the probe: inside the deployed environment**, where the real credential already lives, so nothing is copied out. Iterate the constant one member at a time and print only name, status, verdict. Commit that as a script, so the next version bump re-runs it instead of re-reasoning about it.
- **The evidence goes INTO THE ISSUE as acceptance criteria:** the documentation with URL, fetch date and the load-bearing sentences quoted verbatim; the live probe table with one request per candidate name, its verdict, the credential/target used and the date, **including the rejected rows**; and `Done when` written as checkable statements over those two tables. Without it, the next dev goes back to the same unclear provider page that produced the bug, and the rejected rows are what stop someone re-proposing a name that does not work.
- **Version bumps are the recurring trigger.** Pinning a provider to a new API version silently re-opens every vocabulary question that version answers differently. A version-pin PR that does not re-probe the vocabulary is incomplete, no matter how green its tests are.
- When a live probe is genuinely impossible (no credential, no test account), say **"unverified against live provider"** in the PR and in the code comment, and hand over the exact probe command. Never let silence imply it was checked.

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
Every rule here is a decision you make BEFORE dispatching, not a check afterwards.

- Every parallel agent gets its **own git worktree**. One issue → one agent → one worktree. Never two agents in one working tree.
- **A sandboxed dev needs a CLONE, not a linked worktree, whenever the repo's `.git` sits outside its writable area.** A linked worktree keeps its index and the common git dir in the ORIGINAL location, so the dev can write files and then cannot commit them (`Operation not permitted` on the index lock — one dev implemented and green-tested half its task, then died there, correctly refusing to continue because its contract said commit before any long command). A clone's `.git` is self-contained inside the sandbox, preserving both isolation and commit capability; land the work afterwards by fetching the branch from the clone. "Its own worktree" is necessary, not sufficient — it must also be one the dev can commit in.
- **Never cancel an in-flight marker on a dead-pid basis unless the recorded pid OWNS the work.** PID liveness is a valid staleness test only when the process that wrote the marker is the process doing the job. A dispatcher that records its own pid and owns its subprocess qualifies; a thin launcher that records a short-lived pid while the task continues inside a shared long-running server process does not — two such records were read as leaked markers and one live job was cancelled, whose redispatch then put two devs in one checkout, the exact violation this section exists to prevent. **When in doubt treat the marker as LIVE and wait**: a wrongly cancelled live job is strictly worse than a stale record.
- The orchestrator NEVER runs builds, `git checkout`, or other state-changing ops in a checkout an agent is using. Use a separate worktree for your own builds/installs too.
- When an agent reports something odd about its environment ("files changing under me", "modified since read"), INVESTIGATE before dismissing — file-lock errors are real signals, not agent confusion.
- A test seen failing ONCE must be explained before merge. Distinguish env-flake (rerun isolates it) from code-flake (nondeterministic logic) — both block merge until understood.

## 6. Deployment & production-reality checks
Infrastructure, not application logic, tends to be the single largest failure class once a system is deployed — so treat topology and triage ORDER as first-class:

### `DEPLOYMENT.md` — the deploy + environment map is WRITTEN DOWN, in the repo (mandatory)
**The most repeated infra waste is re-deriving where the system actually runs and how it ships.** Every fresh session, every handoff, every non-native dev starts with zero knowledge of the topology — so it gets rediscovered slowly (grep, SSH, list the containers) or, worse, **assumed from memory and got wrong**: a deploy aimed at the wrong host, a "manual deploy" that was auto-on-push, a branch everyone believed was the prod trunk and wasn't. This is not a recall problem to fix with better memory. It is a **documentation deliverable, and producing it is part of the work.**

**Rule: every repo that deploys anywhere carries a `DEPLOYMENT.md` at its root, and keeping it true is part of every task that touches deploy, config, or topology.** NOT in `HANDOFF.md` (per-run, evaporates), NOT in your tool's memory (per-machine, per-model, invisible to a dev in another tool), NOT in a chat scrollback. In the repo, in git, where a dev of any family can read it.

**What it must answer, per environment (prod / staging / each region or tenant):**
- **Name + who uses it**, and which one is authoritative for real users.
- **Public entrypoint** — the URL/DNS that traffic actually hits, what terminates TLS, where that certificate lives and how it renews.
- **Where it physically runs** — host/instance/cloud resource, which container/service/unit serves it, which port, which reverse-proxy config file.
- **Which datastore that process really targets** — server, database name, and how it's wired (env var vs baked config — see config-precedence below). Spell out region/tenant splits; "the prod DB" is not an answer when there are two.
- **How it ships** — the deploy trunk **branch stated explicitly** (a repo whose prod branch is not `main` is exactly where this goes wrong), the trigger (push-auto-deploy / CI workflow / manual command), the literal command or workflow name, and who may run it.
- **How to roll back** — the actual command, not "revert the commit".
- **Where the logs are** and how to read them remotely, per tier (see §4).
- **Known gotchas** — what already bit here: a leaking container, an undersized database tier, a sibling host that looks like prod but isn't.
- **`last_verified: <date>` on every row.** A topology fact is a claim with a timestamp, exactly like a passing test (see *Standing invariant*). A row nobody re-checked in months is a lead, not a fact.
- **Secrets stay out.** Name the env var, the vault path, the credential's location — never the value. This file is committed, and in a public repo it is world-readable; write it so publishing it costs you nothing.

**When it gets written and updated:**
- **Whenever you map the topology** (next rule): the mapping's OUTPUT is a committed `DEPLOYMENT.md` diff. Discovering it and not writing it down means the next session pays the same cost again. If the file doesn't exist yet in a repo that deploys, **creating it is the first task of the run**.
- **Whenever reality contradicts the file:** fix the file in the SAME commit as the discovery, and update `last_verified`. A stale deploy doc is more dangerous than none, because it gets trusted.
- **Whenever a change alters how or where anything deploys** (new environment, new host, changed branch/trigger, moved datastore, new proxy rule): the PR that changes deployment updates `DEPLOYMENT.md`, or it is a **redispatch** — same as a missing test.
- **Point at it from the repo's convention file** so devs of every family find it, and **inline the relevant rows into any dispatch prompt** that touches deploy/config/infra — a non-native dev will not go looking.

**It is still a claim.** `DEPLOYMENT.md` removes *rediscovery*, not *verification*: before a prod deploy or during incident triage you confirm the live topology yourself (below). The difference is that you're checking a written hypothesis in seconds instead of rebuilding it from nothing, and each check either confirms the doc or corrects it.

- **Map the live topology yourself before any prod deploy OR prod incident triage.** Which host/DNS the traffic actually reaches, which container serves it, and which datastore that process really targets — verified now, not from memory or a handoff document. (A production incident where a single prod host was assumed: the 500s were an expired TLS certificate on a *different* host, and the verification query hit the wrong database, so a 404 looked like a code regression. An emergency revert was wasted and 40 minutes went to a misdiagnosis.)
- **Incident triage STARTS at the infra/TLS layer, not the app layer.** `curl -v` the real endpoint first — certificate expiry, DNS, 502-vs-500, which backend actually answered — before hypothesizing a code regression. A 10-second infra check outranks a 40-minute revert. Don't trust a handoff's or your memory's claim about deploy mechanics either (a "manual deploy" turned out to be auto-on-push); confirm against reality.
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

## Two trunks — the human gatekeeps the release, not the loop

**`develop` is where verified work lands, automatically. `main` is a release decision, and that one is the human's.** The point of the split is that a human waiting to approve every task-level merge is a blocker *inside* the autonomous loop, while a human approving a release is a gatekeeper on the thing that actually matters. Same person, different position: out of the inner loop, on the outer gate.

- **Task branch → `develop`: you merge it yourself, no approval needed.** The pre-merge checklist still runs in full first — auto-merge removes the *human* step from that merge, never your verification. A `develop` merge is licensed by the checklist passing, not by the checklist being skipped.
- **`develop` → `main`: HUMAN GATE.** Present what accumulated (tasks, PRs, E2E status, anything you left unverified) and wait for explicit approval. Never push to `main` directly, never promote on a red `develop`.
- **The counterweight, and it is not optional: auto-merge into `develop` is licensed ONLY where `develop` actually runs the E2E QA suite.** Without that suite, auto-merge is not faster autonomy — it is just unverified work reaching the trunk sooner. In a repo where the suite does not exist yet, **building it is a prerequisite task**, and until it exists the merge into `develop` keeps the human gate. State this in your plan rather than assuming it.
- **E2E on `develop` is the integration gate that per-task verification structurally cannot be.** Playbook §2 exists because two independently-green PRs merge cleanly with the seam between them dead — a class no per-task check catches by construction, because each side passes in isolation. Auto-merge makes that class *more* likely, and the suite on `develop` is exactly what pays for it.
- **A red `develop` is a priority-one task, not a state you work around.** It blocks promotion, and it blocks it for everyone. Diagnose whether the break is the last merge or the seam between the last two, and route it back to a dev — never fix it inline, never promote past it.
- **Which trunks a repo actually has belongs in its `DEPLOYMENT.md`**, stated explicitly, because a repo whose release trunk is not `main` is exactly where this goes wrong. **Do not trust any written inventory of which repos have adopted this — run the command that produces it.** One session measured "no repo here has a `develop` branch yet" and wrote it into a durable file; a repo created one nineteen minutes later, and the note was false from then on while still reading as fact. **A cross-repo inventory does not belong in a durable file at all; the command that produces it does.**
- Adopting the model in a repo that has not yet: create the branch, wire the E2E workflow as a gate on it, set branch protection, and record all three in that repo's `DEPLOYMENT.md`.
- **A repo whose working tree IS its live deployment is legitimately exempt** and should say so in its `DEPLOYMENT.md` — a second trunk there would mean the live directory sitting on a branch nobody runs.

## Standing invariant before closing
A goal verified once is an assumption with a timestamp. Before the run is "done", the run's load-bearing behavior must be encoded as a durable check (a CI gate or E2E test that runs on every future change), not merely verified once by you now. The one behavior that would silently rot and cost the most is exactly the one that needs a permanent guard. If you can't add the guard this run, say so loudly in the handoff and hand over the exact check to wire.

## Orchestrator pre-merge checklist (run every time, yourself)
1. Run the task's `done_when` command yourself first (green, output you saw), then the fresh full suite: unit + integration + lint + typecheck + build.
2. Read the diff. Scan for weakened tests (removed/loosened asserts, skip/xfail, hardcoded expecteds, widened tolerances) and for `except: pass` / swallowed errors. Also check the Development standards: YAGNI, DRY, KISS, for any UI change the E2E hooks (test ids + awaitable states), and auditable logging on every decision/outcome (levels + redaction, checked at item 5). A violation is a redispatch, not a note.
3. Real-target verification for anything touching production tech (DB schema/types, driver, external API, blob, signing, per-platform) — or an explicit, loud "unverified because X + here's the command".
3b. **Provider vocabulary probed live by YOU, per name (validation playbook §1c).** If the diff adds or changes any string sent to a third party in their vocabulary — metric/scope/field/edge names, enum values, option keys, an API version pin — you run the probe yourself and read the output, one name at a time. A doc citation in the diff is not evidence; neither is the dev's word "confirmed". A version-pin change re-opens every vocabulary question that version answers differently, so it re-probes too. If it truly cannot be probed, the PR says `unverified against live provider` out loud — silence there is how an endpoint that returned nothing for every record shipped and survived for weeks.
4. Integration seam check if this PR shares a surface with recently-merged work.
5. **Auditable logging (full, not just failures):** can you reconstruct *everything this change does* from the logs alone — every decision + outcome, at the right level (debug/info/error), with the data (ids, correlation id) that makes events meaningful, secrets redacted? A silent path, a swallowed error, or a business action with no `info` audit line is a redispatch (see Development standards → auditable logging + validation playbook §4).
6. Consumers/precedence: who else reads/writes what this touches; what config the deployed process really uses. **For a change to the FORMAT of a shared state file, the seam is not only "who reads this" but "who is mid-flight with the PREVIOUS version"** — a running process holds the old code in memory and will write through it on exit. A grep that correctly finds a single reader is still not enough: if another run is in flight, its old-code cleanup path computes on the old shape (`max(value - 1, 0)` against what is now a list → `TypeError` on exit, after the work is done). Check for live consumer processes before migrating a shared format, and wait for in-flight holders to drain.
6b. **`DEPLOYMENT.md` current?** If the change touches deploy, config, hosts, environments, or the deploy branch/trigger, the PR updates `DEPLOYMENT.md` in the same commit (with `last_verified`) — a stale deploy doc is worse than none because it gets trusted. If the repo deploys somewhere and the file doesn't exist yet, it gets created before this run closes (validation playbook §6). Anything you had to rediscover about the topology during this task goes into the file, not just into your answer to the human.
7. **Visual QA for ANY user-visible UI change.** Green tests and a green build do NOT verify how a page looks — a wrong text color in light mode and broken paragraph spacing can ship straight past a fully green gate. If the change is frontend-facing you MUST screenshot the affected screens/components and look at them yourself. Screenshot every affected page in BOTH color themes (light AND dark — trigger the app's real theme mechanism: its toggle / storage flag / root class, not just an emulated OS preference) at desktop AND mobile viewports, then actually read the image files. Check UI, UX and functionality:
   - **No overflowing or overlapping elements** — nothing spills out of its container or off-screen, no element sitting on top of another.
   - **No clipped or truncated text** — no cut-off words, no ellipsis where the box was simply too small, no text hidden behind another element.
   - **No characters glued to a component edge** — glyphs must not touch the end of a button/card/input; real padding on every side.
   - Text readable in both themes (no light-on-light, no dark-on-dark); spacing and typography sane; images render; layout intact at every viewport.
   - UX sane: interactive elements reachable and obviously interactive, focus/hover/active states present, nothing important below an unexpected fold.

   A visual defect is a **redispatch**, exactly like a failing test — "green tests" never certify how it looks. If the project has themes, at least one E2E should assert computed text color/contrast in the non-default theme so a regression is caught without eyes.

   **Two QA cadences, and the difference between them is measured, not preferred.**
   - **Per deploy — the narrow gate.** After EVERY deploy of a user-facing app, drive each newly shipped flow *on the deployed target* and SEE it before any "deployed / done" report. A feature deployed AFTER the round's screenshots were taken can ship broken; that has happened.
   - **Per release — the full report.** The exhaustive pass (drive the real flows with every action, input and selector logged; sweep the changed screens for broken UI across viewports and both themes; emit one self-contained report) belongs at the release gate, and its report is what you **attach to the `develop` → `main` promotion** — that is where a human already stands, so that is where the judgement half belongs.
   - **Why split them at all:** requiring the full pass per deploy was measured as undeliverable. On one autonomous night with ~10 successful deploys, visual QA appears twice in the log and the narrow per-deploy gate appears zero times. **A gate nobody can meet at the required rate is not a gate — it is a rule that gets skipped, which is worse than none, because it manufactures confidence.** Set the cheap gate at the frequency it can actually run, and put the expensive one where a human is already looking.
8. CI green (or your local matrix is the gate); no secrets; no red bypassed.
9. Only then merge — into **`develop`**, and you do not need a human for it (see *Two trunks* above). Promotion `develop` → `main`, and any deploy or outward-facing step, gets explicit approval.

---

# Orchestration & keeping the human in the loop

Long autonomous runs fail the human silently if they can't see what's happening. These practices are as important as the code checks.

## Status cadence
- **ARM THE MONITOR ON THE FIRST DISPATCH — automatically, no exceptions.** The moment ANY dev work is dispatched, arm a recurring driver (whatever your tool offers: a cron/scheduled entry, a self-scheduling loop) BEFORE you do anything else. This is part of dispatching, not an optional follow-up — **a dispatch without an armed monitor is an incomplete dispatch**, and that's how a run goes quiet for half an hour. Disarm it only when the run is fully done (all tasks verified and closed) or the human stops it.
- **DISARMING IS A CHECK, NOT A CLOSING GESTURE — and this rule existed and was still broken twice in one night.** Both sessions deleted their own monitoring driver as part of "closing" a run that was not finished; one of them then slept 2 h 43 min with a non-empty queue, because it had just removed the only thing that would have woken it. Exhortation clearly does not work here, so make it answerable instead: **before you disarm, write out what is left — every unverified task, every open decision waiting on the human, every gated step. If that list is not empty, you are not closing the run and the monitor stays armed.** A monitor you disarmed while work remained does not degrade the run gracefully; it ends it silently, and you will not notice, by construction.
- **A near reset is a reason to CONTINUE, not to stop.** One session stopped at 69 % of its rate window with the reset 50 minutes away. Waiting out a reset with an armed monitor costs 50 minutes; stopping costs the whole queue.
- **Each tick actively checks the work is alive, THEN reports.** Two halves, both mandatory: (1) verify each in-flight dev is really progressing — a pushed commit, branch movement, a live transcript timestamp, the background job still running — never just assume; a dev with no progress for ~10+ min gets a progress-check ping (below). (2) Emit the status report. A tick that reports without checking liveness (or checks without reporting) is incomplete — the whole point is catching a dev that died silently.
- Emit a **status report every ~5–10 minutes** while agents run. This happens without being asked, because the monitor was armed on dispatch.
- **Every tick also re-checks your own limits** (rate/budget and context fill) and acts on them per *Watch your own limits* — that's how the handoff stays proactive instead of hitting a wall. Surface the number in the report once it crosses ~70 %. A tick that skips this check is incomplete.
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
- **Two documents, two lifetimes — don't confuse them.** `HANDOFF.md` is **per-run and disposable**: current state, in-flight branches/PRs, next steps, deleted or rewritten when the run closes. `DEPLOYMENT.md` is **permanent repo knowledge**: where each environment lives and how it ships (playbook §6), committed, surviving every session, handoff and model switch. Facts about the deployed system belong in `DEPLOYMENT.md`, never only in a handoff — a handoff-only topology fact is lost by design, and that loss is exactly what makes the next session deploy to the wrong host.

## Watch your own limits (rate / budget / context)
A live session usually **cannot recover from hitting its own wall** — and often cannot even change the thing that's exhausted, because the account/model is bound when the process starts. So both limits are managed *proactively, by threshold*, not when they bite:

- **~70 % (watch):** keep `HANDOFF.md` current after every commit so a switch is always one command away. Stop opening new open-ended reads. Confirm no dev work is landing on the resource you're running low on.
- **~80 % (act):** finish and COMMIT the in-flight atomic step to a clean state, update `HANDOFF.md`, then hand off (below). **Do not start another verify/dispatch cycle past this point** — you may not get to finish it, and a half-verified task is worse than an unstarted one.

`HANDOFF.md` carries: current state, what's merged, in-flight branches/PRs, exact next steps, gotchas — **and a restatement of the iron rules plus a pointer to the pre-merge checklist**, since a fresh session or a different tool won't have this context.

**Why not just let auto-compaction happen?** Because it's the worst of the available shrink paths: it fires at an uncontrolled moment (often mid-task), its summary is a lottery while `HANDOFF.md` is deterministic, and model quality measurably degrades as the window fills — and high-quality verification is the orchestrator's entire job. Treat auto-compaction as a safety net, never the plan. **If it fires anyway, re-read `HANDOFF.md` and the iron rules before doing anything else** — compaction silently drops workflow nuance, and the first thing to go is usually the discipline that keeps you from writing code yourself.

### Baton-pass (handing the run to a fresh session)
When the trigger hits, the switch is: **start a FRESH session pointed at `HANDOFF.md`** — a running session generally can't hot-swap its own account or model. Do it while you still have turns left, not after the wall.

- Whatever your tool's mechanism for launching a session on a different account/profile is, invoke it with the repo and an **absolute** path to `HANDOFF.md` (the working directory and the handoff file may live in sibling directories).
- **Don't launch the successor inside the current session's own shell.** An interactive session started as a child of the one being replaced hangs and times out. It needs its own terminal.
- Expect autonomy guardrails: a safety classifier may block a session from spawning another session, since "agent creates agent" is exactly what such guards exist to stop. If it's blocked, degrade gracefully — surface ONE line with the exact command for the human to run in a new terminal. And note the deliberate meta-guard: an agent generally cannot grant itself the exception either, because editing the guard's own config is guarded too. That carve-out is the human's call, once.
- Same mechanism covers both triggers (limit and context), and the same handoff covers a fallback to a different model family (see Orchestrator fallback).

## Context self-management (keep the orchestrator sharp)
- **Verify lean.** Bulky reads don't belong in the orchestrator's context. Delegate large diff reviews, long log scans, and multi-file investigation to a **read-only explore subagent** and keep only its conclusion; read directly only what you must judge with your own eyes (the load-bearing diff hunks, the verbatim test-output tail). This does NOT dilute the iron rules — the fresh test run is still yours; only the reading volume is delegated.
- A run that's "still going at a nearly full window" is already a degraded run. Apply the 70/80 % thresholds above to context exactly as you do to rate limits.

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

**Log these signals too — they're the ones whose absence costs you most:**
- **`detection_latency`** — how the failure was caught and how late. A silently dead background job found ~28 minutes after the fact, at a status tick, is a very different problem from one caught at dispatch. Record whether it was caught at dispatch, at a tick, at merge, or escaped to production. This is the only way to tell whether your monitor cadence and liveness checks actually work.
- **`caught_by`** — which gate stopped it: `done_when` | a specific pre-merge checklist item | cross-family review | visual QA | standing invariant | escaped. An escape is a **gate gap to fix**, not just a task that failed.
- **`infra_vs_code`** — tag infra failures with the sub-cause (topology / TLS / config-precedence / toolchain / disk). Infra is usually the biggest class, and a generic "infra" bucket teaches you nothing; the sub-causes each have their own fix.
- **Per-run family/tier fail-rate deltas**, so the routing heuristic self-corrects from data instead of memory. This is exactly how a model gets demoted out of default routing (see Developer routing).
- **Project-specific gaps do NOT belong in this skill.** A gap tied to one repo's stack (a framework's routing quirk, a test-runner env setting, that project's QA credentials) belongs in THAT repo's convention file. Only cross-project, workflow-level gaps become skill edits — otherwise the methodology silts up with one project's trivia and stops being portable.

## Keeping this skill honest (the expiry rule)

A file of war stories grows and is never cut, and a reference nobody can finish reading is a reference nobody reads. So the promotion pass and the pruning pass are the **same pass** — when you fold a recurring `instruction_gap` into a rule, prune at the same time:

- **An incident whose failure class has not recurred in twelve months gets compressed to one sentence**, with the devlog as its record. `devlog.py retro` plus a date is always a better archive than prose here.
- **Two incidents that share a rule get merged into one.** Repetition does not strengthen a rule; it dilutes the one thing the reader will remember.
- **An incident that never produced a rule does not belong here at all** — it belongs in the devlog. Stories exist to justify rules, not to remember everything.
- **A gate never leaves the always-loaded file.** Move stories, procedures and worked examples out when they get heavy; a rule you have to open another file to read has stopped being a gate.
- **Numbers fossilise — do not write measured rates into this file.** A per-model fail rate written down was materially wrong within five days (one model stated at ~11 % measured 22 % on the next retro, within four points of the model it had been promoted over). A stale routing fact is worse than none, because every dispatch trusts it silently. Recompute from the devlog each retro and route on what you measure. Same for cross-repo inventories: keep the command, not its output.
