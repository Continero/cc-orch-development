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

## Adapt to your own setup

The methodology is model-agnostic; a few things you should tailor:

- [ ] **Which model families/CLIs you have.** The skill names Claude, GPT/Codex, Grok, Gemini, Kimi as *examples* — use whatever subset you've got. Cross-family review just needs two different lineages.
- [ ] **How you dispatch subagents.** The skill assumes you can spawn developer agents and pin their model + effort. Wire this to your tool's mechanism (Task/Agent tool, a headless CLI call, etc.).
- [ ] **Your `done_when` commands.** Per project: the exact shell command (test target, build+smoke) that proves a task is done.
- [ ] **Your CI / E2E gate.** The "standing invariant" step assumes you can add a durable check; point it at your CI and E2E harness.
- [ ] **Your limits.** Rate/budget/context caps differ per plan — the skill tells you to hand off cleanly before hitting them, but the thresholds are yours.
- [ ] **Your devlog.** A plain file works; swap in whatever you already use.

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
