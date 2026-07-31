# orch-development

A Claude Code skill for running software development as **orchestrate-and-verify** instead of write-it-yourself. Your session model becomes PM + lead architect + QA gate; developer subagents (any models or CLIs you have) do the implementation, and the orchestrator independently verifies every piece before it lands.

## Philosophy

A report is a claim, not a fact — the orchestrator verifies everything with its own tool calls and never writes the code itself. Different model families catch different bugs, so load-bearing work is reviewed across families and nothing grades its own homework. Done is a machine-checkable fact (a green command, a durable CI/E2E gate), never a model's opinion of itself.

## Install

Copy this folder into your skills directory:

```bash
cp -r orch-development ~/.claude/skills/orch-development
```

(Or drop it into a plugin's `skills/` directory.) It activates on phrases like "orch-development", "orchestrated development", "multi-agent dev", or "let the orchestrator drive".

**Two files, and the split matters.** `SKILL.md` is the orchestrator's file — every gate is stated there in full, because a gate that lives in a file you might not open has stopped being a gate. `DEV_BRIEF.md` is the developer's file: the role override, the no-backgrounding rule, TDD, the engineering standards, the honest-report contract. It is **pasted verbatim into every dispatch** rather than consulted, so it stays one versioned artifact — which is also what lets you attribute a change in dev outcomes to a change in what devs were told (`git log --before=<devlog ts> -1 -- DEV_BRIEF.md`). Retyping it from memory is how a `## Git` requirement went missing and a dev finished green with 784 passing tests and nothing committed.

`devlog.py` ships alongside the skill as a working reference implementation of the retrospective log — append one entry per verification, then aggregate before the next run:

```bash
python3 devlog.py add --json '{"kind":"task","model":"…","tier":"standard","attempt":1,"outcome":"pass"}'
python3 devlog.py retro --days 30     # fail rate per model, failure classes, gate escapes, clustered instruction gaps
```

It's plain stdlib Python writing JSONL (`./devlog/devlog.jsonl`, or `$DEVLOG_FILE`). Use it, or point the skill at whatever log you already keep — the discipline matters more than the tool.

## Adapt to your own setup

The methodology is model-agnostic; a few things you should tailor:

- [ ] **Which model families/CLIs you have.** The skill names Claude, GPT/Codex, Grok, Gemini, Kimi as *examples* — use whatever subset you've got. Cross-family review just needs two different lineages.
- [ ] **How you dispatch subagents.** The skill assumes you can spawn developer agents and pin their model + effort. Wire this to your tool's mechanism (Task/Agent tool, a headless CLI call, etc.).
- [ ] **Your `done_when` commands.** Per project: the exact shell command (test target, build+smoke) that proves a task is done.
- [ ] **Your CI / E2E gate.** The "standing invariant" step assumes you can add a durable check; point it at your CI and E2E harness.
- [ ] **Your limits.** Rate/budget/context caps differ per plan — the skill hands off at ~70/80 % of whatever your ceiling is, but the ceiling is yours to know.
- [ ] **Your baton-pass command.** The skill starts a fresh session pointed at `HANDOFF.md` when a limit is near; the exact launch command (and which account/profile it targets) depends on your tool.
- [ ] **Your visual QA loop, at two cadences.** Checklist item 7 wants a *cheap* per-deploy pass (drive the newly shipped flow on the deployed target and look at it) and an *exhaustive* per-release report attached to the `develop` → `main` promotion. Wire both to your browser automation, and set the cheap one at a frequency you can actually meet — a gate nobody meets is worse than none.
- [ ] **Your trunks.** The skill assumes `develop` (verified work auto-merges, no human step) and `main` (release, human gate). Auto-merge into `develop` is licensed **only** where `develop` runs an E2E suite — without it, keep the human gate on both, or build the suite first. Record which trunks a repo has in its `DEPLOYMENT.md`.
- [ ] **A `DEPLOYMENT.md` per deploying repo.** Playbook §6 makes this mandatory: where each environment lives, how it ships, how to roll back. Write it once from what you already know, mark unverified rows as such, and correct it as reality contradicts it. Names of env vars and vault paths only — never a secret value.
- [ ] **Your `DEV_BRIEF.md`.** The version here is deliberately stack-agnostic. Add your own non-negotiables (a package manager, a formatter, a commit convention) — but keep *project-specific* rules in that project's own convention file, or the brief silts up and stops being portable.
- [ ] **Your live-probe path for third-party vocabulary.** Playbook §1c requires the orchestrator to see a provider accept each name before it merges. Work out where you can run that probe with a real credential (ideally inside the deployed environment, so nothing is copied out) and commit it as a script — the next version bump re-runs it instead of re-reasoning about it.
- [ ] **Your devlog.** `devlog.py` works out of the box; swap in whatever you already use.

## Setting up your model families

The skill is model-agnostic, but the cross-family review gate needs at least **two different model lineages**. Here's what each takes to wire into Claude Code:

- **Claude (orchestrator + default devs)** — you already have this. The session model orchestrates; Claude subagents (the Task/Agent tool) are your default developers. Needs a Claude Pro/Max subscription or an Anthropic API key.
- **GPT / Codex** — install the [Codex CLI](https://github.com/openai/codex) and sign in with a ChatGPT/OpenAI account (or an OpenAI API key). To dispatch it from inside Claude Code, add the official Codex plugin:
  ```
  /plugin marketplace add openai/codex-plugin-cc
  /plugin install codex@openai-codex
  /codex:setup
  ```
- **Grok** — install the Grok CLI and sign in with an xAI / SuperGrok account (or an xAI API key), then add a Grok plugin for Claude Code (e.g. a community `grok-cc` plugin) and follow its setup. It becomes a dispatchable subagent like Codex.
- **Gemini** — Google deprecated the standalone Gemini CLI for individual accounts; the supported path is the **Antigravity CLI (`agy`)**, which runs on a Google AI Pro/Ultra login and dispatches headless (`agy -p "…"`). A consumer "Gemini for Workspace" seat does *not* grant CLI coding quota.
- **Kimi (Moonshot)** — a **Kimi subscription** (e.g. the ~$99 "Allegro" tier) *does* power the official **Kimi Code CLI** (`kimi -p "…"`) via `kimi login` (OAuth), or you can point a Claude Code profile at the subscription endpoint. ⚠️ **Never send API keys, passwords, or any credential to Kimi** — the skill enforces this as a hard block.

Notes:
- Each family needs **its own account/subscription or API key**; you authenticate each CLI once (a login flow or a key in env).
- You don't need all of them. **Two different families is enough** for the cross-family gate. With only Claude, everything still works except cross-family review — fall back to a fresh-context, same-family review.
- **Secrets never go into a prompt sent to a hosted third-party family** (hard block for Kimi). Reference secrets by name and let the code read them from the environment at runtime.
- Running **multiple accounts of the same family in parallel** (e.g. several Claude seats to raise throughput) is an advanced optimization and is **out of scope** here — this skill only needs *access* to the families, not account rotation.

## Credit

Distilled from real multi-agent development runs. Share freely — keep or drop this line.
