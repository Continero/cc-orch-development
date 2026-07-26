#!/usr/bin/env python3
"""Development retrospective log for the orch-development workflow.

Append one structured entry after each task verification; aggregate them before
planning the next run. A verification you didn't log is learning thrown away.

Usage:
  devlog.py add --json '{"kind":"task", ...}'     # append one entry (ts/repo auto-filled)
  devlog.py add < entry.json                       # same, JSON on stdin
  devlog.py retro [--days 30] [--repo <name>]      # aggregate report
  devlog.py tail [-n 20]                           # last N entries, one line each

Log file: ./devlog/devlog.jsonl next to this script, or $DEVLOG_FILE.

Entry schema (flat JSON, unknown keys allowed and kept):
  kind: task | run_retro | orchestration_issue
  task: short description of the dispatched task           (kind=task)
  family: which model family ran it       model: the model id      tier: frontier|standard|light
  exec: how it was dispatched (agent | headless | cli)     attempt: 1..n
  outcome: pass | redispatch | escalated | abandoned
  failure_class: wrong-target-verification | integration-seam | test-infra-mask |
                 observability-gap | isolation-violation | weakened-tests | incomplete |
                 dishonest-report | visual-defect | infra | env-flake | other
  infra_vs_code: for failure_class=infra, the sub-cause
                 (topology | tls | config-precedence | toolchain | disk)
  caught_by: done_when | checklist-<n> | cross-family-review | visual-qa |
             standing-invariant | escaped        <- 'escaped' is a gate gap, not just a task fail
  detection_latency: at-dispatch | at-tick | at-merge | escaped-to-prod
  what_failed: what verification caught       fix_action: redispatch | tier_up | prompt_fix | human
  instruction_gap: what the dispatch prompt should have said but did not
  notes: anything else worth remembering
"""
import json
import os
import subprocess
import sys
import time
from collections import Counter

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "devlog")
LOG_FILE = os.environ.get("DEVLOG_FILE") or os.path.join(LOG_DIR, "devlog.jsonl")


def detect_repo():
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return os.path.basename(r.stdout.strip())
    except OSError:
        pass
    return os.path.basename(os.getcwd())


def cmd_add(argv):
    if "--json" in argv:
        raw = argv[argv.index("--json") + 1]
    else:
        raw = sys.stdin.read()
    entry = json.loads(raw)
    entry.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
    entry.setdefault("repo", detect_repo())
    entry.setdefault("kind", "task")
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"logged: {entry.get('kind')} / {entry.get('outcome', '-')} / {entry.get('repo')}")


def load(days=None, repo=None):
    if not os.path.exists(LOG_FILE):
        return []
    cutoff = time.time() - days * 86400 if days else None
    out = []
    with open(LOG_FILE) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            if repo and e.get("repo") != repo:
                continue
            if cutoff:
                try:
                    ets = time.mktime(time.strptime(e.get("ts", "")[:19], "%Y-%m-%dT%H:%M:%S"))
                    if ets < cutoff:
                        continue
                except ValueError:
                    pass
            out.append(e)
    return out


def arg_val(argv, flag, default=None, cast=str):
    if flag in argv:
        return cast(argv[argv.index(flag) + 1])
    return default


def cmd_retro(argv):
    days = arg_val(argv, "--days", None, int)
    repo = arg_val(argv, "--repo")
    entries = load(days, repo)
    tasks = [e for e in entries if e.get("kind") == "task"]
    if not entries:
        print("no entries" + (f" in last {days}d" if days else ""))
        return

    scope = f"last {days}d" if days else "all time"
    if repo:
        scope += f", repo={repo}"
    print(f"# Retro ({scope}): {len(tasks)} task entries, {len(entries) - len(tasks)} other\n")

    def dist(label, key, source=None):
        src = tasks if source is None else source
        c = Counter(e.get(key) or "?" for e in src)
        if c and list(c) != ["?"]:
            print(f"{label}: " + "  ".join(f"{k}={v}" for k, v in c.most_common()))

    dist("Outcomes", "outcome")
    dist("By model", "model")
    dist("By tier", "tier")
    dist("By family", "family")

    fails = [e for e in tasks if e.get("outcome") != "pass"]
    if tasks:
        by_model_fail = Counter(e.get("model") or "?" for e in fails)
        by_model_all = Counter(e.get("model") or "?" for e in tasks)
        rates = {m: f"{by_model_fail.get(m, 0)}/{n}" for m, n in by_model_all.items()}
        print("Fail rate per model: " + "  ".join(f"{m}={r}" for m, r in rates.items()))

    fc = Counter(e.get("failure_class") for e in fails if e.get("failure_class"))
    if fc:
        print("\nFailure classes: " + "  ".join(f"{k}={v}" for k, v in fc.most_common()))

    # infra is usually the largest class, so it needs its sub-cause broken out
    infra = [e for e in fails if e.get("failure_class") == "infra"]
    if infra:
        dist("Infra sub-causes", "infra_vs_code", infra)

    # which gate stopped it; 'escaped' means a gate gap to fix, not just a failed task
    dist("Caught by", "caught_by", fails)
    dist("Detection latency", "detection_latency", fails)
    escaped = [e for e in fails
               if e.get("caught_by") == "escaped" or e.get("detection_latency") == "escaped-to-prod"]
    if escaped:
        print(f"\n!! {len(escaped)} escape(s) — each is a GATE GAP, fix the gate not just the task:")
        for e in escaped[-5:]:
            print(f"  - [{e.get('ts', '')[:10]}] {e.get('what_failed') or e.get('task')}")

    gaps = [(e.get("ts", "")[:10], e.get("model", "?"), e["instruction_gap"])
            for e in entries if e.get("instruction_gap")]
    if gaps:
        print("\nInstruction gaps (feed these back into dispatch prompts):")
        for ts, m, g in gaps[-15:]:
            print(f"  - [{ts} {m}] {g}")

    issues = [e for e in entries if e.get("kind") == "orchestration_issue"]
    if issues:
        print("\nOrchestration issues:")
        for e in issues[-10:]:
            print(f"  - [{e.get('ts', '')[:10]}] {e.get('notes') or e.get('what_failed')}")

    retros = [e for e in entries if e.get("kind") == "run_retro"]
    if retros:
        print("\nRun retros:")
        for e in retros[-5:]:
            print(f"  - [{e.get('ts', '')[:10]} {e.get('repo')}] {e.get('notes')}")


def cmd_tail(argv):
    n = arg_val(argv, "-n", 20, int)
    for e in load()[-n:]:
        bits = [e.get("ts", "")[:16], e.get("repo", "?"), e.get("kind", "?"),
                e.get("model") or "", e.get("outcome") or "",
                (e.get("task") or e.get("notes") or "")[:80]]
        print("  ".join(b for b in bits if b))


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("add", "retro", "tail"):
        print(__doc__)
        sys.exit(1)
    {"add": cmd_add, "retro": cmd_retro, "tail": cmd_tail}[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
