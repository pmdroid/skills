---
name: triage
description: Triage an incoming bug with an isolated council of agents — verify the claim, find the cause, size the blast radius, check prior art — then return a severity verdict and an agent-ready brief. Use when a Sentry issue or link lands, when a customer reports something broken, or when the user asks how bad a bug is, whether it is real, or whether it is already known.
---

# Triage

A Sentry alert is a **claim**, not a bug. So is a customer report. Triage turns the claim into a **verdict** — disposition, severity, cause, owner, next action — fast enough to be worth doing on every incoming issue.

You are the broker. Seats work in isolation, never see each other, and never see the raw alert. [`council`](../council/SKILL.md) owns the mechanics: same script, same invariants, same handling when an engine comes back empty. Triage adds a fixed panel, seats that read the repository, and a verdict.

```bash
export COUNCIL="${COUNCIL:-$HOME/.agents/skills/council/scripts/council}"
export COUNCIL_SESSION="triage-$(date -u +%Y%m%dT%H%M%SZ)"
```

## Step 1 — Build the case file

The **case file** is the only thing seats ever read. Facts you extracted, in your words, with no alert text, no customer prose, and nothing from another seat.

Fill every field with a value or the literal word `unknown`.

**Error signal** — from Sentry, Datadog, or a paste:

- exception type and message, and whether it was handled
- culprit plus the in-app stack frames, innermost first
- first seen, last seen, event count, distinct users or orgs
- rate shape: spiking, steady, decaying, or one-off
- releases and environments it appears in
- any tag that skews hard toward one org, endpoint, region, or client

**Customer signal** — from the report:

- the symptom in their words, and what they expected instead
- account, plan, and how many of their users are hit
- when it started, and whether it reproduces on demand
- the workaround they found, if any

**Repository** — always:

- repo path, current sha, and the deploy window containing first-seen
- what shipped in that window

[`SIGNALS.md`](SIGNALS.md) has the commands for each source and what to do when a source is missing.

`unknown` is evidence, not a gap to paper over. A customer report that reaches Step 2 with four unknowns is already the `needs-info` disposition; skip the council and go to Step 4.

## Step 2 — Seat the council

Four seats, one blind round, all dispatched together.

| Seat | Its question | Reads repo | Deliverable |
| --- | --- | --- | --- |
| `reproducer` | Is the claim true? | yes | the call chain from entry point to the failing line, or why that line is unreachable from the described input |
| `cause` | Why does it fail? | yes | the chain down to the link a fix should land on, and the change that introduced it if this is a regression |
| `radius` | What else touches this? | yes | other callers of the broken path, whether it corrupts data, whether it fails silently, and the containment option short of a fix |
| `prior-art` | Have we seen this? | no | the matching tracker issue, the PR that already fixed it, the prior decision to not fix it, or nothing |

### Past the proximate cause

The first thing found is the **proximate** cause: a stack trace points at the line that threw, which is where the symptom surfaced, not where it began. A fix there ends the alert and leaves the mechanism running.

Two questions clear a link, in order:

1. Had this link behaved correctly, would the symptom still occur? Yes, and the link is proximate; keep going.
2. Does a fix at this link leave the same class of failure reachable by another path? Yes, and the link is proximate; keep going.

The chain terminates at a link where a different decision — a commit, a contract, a guard someone dropped, a config — would have prevented the symptom. A chain that bottoms out in something nobody could have chosen has not terminated; it has given up.

Stopping at a proximate link on purpose is a legitimate call under a P0, where ending the bleeding beats understanding it. Make the fix change the mechanism rather than quiet the signal — an alert that goes silent while the defect lives is the one outcome triage cannot recover from.

### Choosing engines

Probe before dispatch:

```bash
"$COUNCIL" engines --probe
```

Seats are roles, not models. Fill them by what the seat has to do:

| Seat | What it needs | Why |
| --- | --- | --- |
| `reproducer` | fast, tool-capable | it is tracing a path through a lot of code, not judging it |
| `cause` | the deepest reasoner you have, at its highest effort | the hardest call on the panel gets the deepest seat |
| `radius` | tool-capable, good at wide search | it reads every caller of the broken path |
| `prior-art` | the cheapest healthy engine | CLI queries and matching, no repo — the cheapest seat for the cheapest job |

Council's rule on slugs is unchanged: pass `--model` only when the user named one or probe proved it. Reasoning effort belongs to the engine, not to council — some engines take it inside the model slug, others read it from their own config file, so set it wherever that engine wants it before the run.

The three repo seats need an engine that can run a tool loop, so draw them from `codex`, `cursor`, `claude`, or `opencode`. `grok` is capped at one turn by the council script and can only hold `prior-art`. Swap any seat whose engine comes back unhealthy from the probe, or that returns an empty reply.

Dispatch all four in one message so they run concurrently, backgrounding each with `&` and a single `wait`:

```bash
"$COUNCIL" ask --engine <engine> --session "$COUNCIL_SESSION" \
  --cwd "$REPO" --timeout 600 <<'EOF' &
<seat prompt>
EOF
```

Replies land in `~/.council/runs/$COUNCIL_SESSION/` as `engine-model.md`. Two seats on the same engine therefore need different `--model` slugs, or you cannot tell which seat wrote which file. Read the replies only once every seat is back.

### Seat prompt

```text
You are the <seat> seat on a bug triage council. <the seat's question>

Case file:
<the fields from step 1, verbatim, unknowns included>

Repository: <absolute path>. Read it. Do not modify anything.

Selected findings:
- <claims you chose to share; omit in round 1>

Reply with exactly these sections:
- finding
- evidence (file and symbol names, commits, command output you actually ran)
- what would falsify this
- what you could not determine
- confidence 0-100

Print those five sections to stdout. That print is the entire deliverable.
Do not open a PR, edit a file, or write anywhere outside stdout.
No chain-of-thought.
```

`prior-art` gets no `Repository:` line and instead gets the tools it needs named: the issue tracker's search command, `gh search`, and wherever the team writes down a decision to not fix something.

`cause` gets one more required section, `chain`: each link with the why that connects it to the one above, ending at the link a fix should land on, plus both counterfactual answers for that link.

**What would falsify this** is the section that earns the panel. A seat that cannot name its own falsifier is guessing, and you weight it accordingly.

## Step 3 — Broker

Read all four. You are looking for where seats agree, where they contradict, and what every one of them marked as undetermined.

Two things fire a second round:

- **A contradiction that moves the verdict** — `reproducer` says unreachable while `cause` names a defect, or `radius` finds corruption that changes severity. Ask the narrow question that settles it.
- **Agreement on a cause that has not cleared the counterfactual.** Seats reading one stack trace land on the same shallow link easily, so agreement here is the panel repeating the trace back to you, not four findings converging. Hand the agreed cause to a seat that did not produce it, as a claim to break: name the case where fixing this link leaves the symptom reachable.

Send claims, never transcripts. Stop after round 2 regardless.

## Step 4 — Verdict

Pick exactly one disposition:

- `bug` — real, ours, unfixed.
- `already-fixed` — fixed on main; the events come from an older release. Name the commit and the release that carries it.
- `duplicate` — already filed. Name the issue.
- `not-ours` — third party, client environment, or customer misconfiguration. Name what to tell them.
- `noise` — expected, self-healing, or an alert to mute rather than a bug to fix.
- `needs-info` — the claim cannot be verified from what exists. Name the specific questions, each one answerable in a sentence.

Severity applies to `bug` only:

- **P0** — data loss or corruption, an auth or tenancy boundary crossed, or a core path down for multiple orgs with no workaround.
- **P1** — a core path broken for at least one customer, or a fresh regression from a release still rolling out.
- **P2** — an edge path with a workaround, low and flat volume.
- **P3** — cosmetic, log-only, or a flake that clears itself.

Two rate-shape modifiers, applied after: a spike aligned with a deploy is a regression, so raise a step. A rate flat since a first-seen months ago is not new, so lower a step no matter how large the event count.

Report to the user in the terminal:

```text
VERDICT   <disposition> · <severity if bug> · confidence <0-100>
CAUSE     <the link a fix lands on, or "not established">
DEEPER    <what the fix leaves running, or "nothing left">
REGRESSION <the change that introduced it, or "no">
RADIUS    <who and what else is affected>
OWNER     <app or lib in the repo>
SPLIT     <where seats disagreed, or "none">
UNKNOWN   <what no seat could determine>
NEXT      <the single next action>
```

Then stop and ask whether to file it.

## Step 5 — File

On confirmation, open a tracker issue carrying the brief. `SIGNALS.md` has an example invocation.

The brief is the contract an implementing agent works from, and it may sit for weeks while the code moves under it. So:

- Describe interfaces, types, and behavioral contracts. Name symbols, not file paths, and never line numbers.
- Say what the system should do, not which function to edit.
- Give acceptance criteria that are independently checkable — a criterion nobody can run is not a criterion.
- State what is out of scope, so the fix does not grow.

```markdown
## Agent Brief

**Disposition:** bug · **Severity:** P1 · **Confidence:** 85

**Summary:** one line

**Current behavior:** what happens now, and the call chain that produces it

**Desired behavior:** what should happen, including the edge cases the seats surfaced

**Key interfaces:**
- `SymbolName`: what has to change and why

**Acceptance criteria:**
- [ ] checkable criterion
- [ ] the original signal stops reproducing

**Out of scope:**
- the adjacent thing that is not this issue

**Leaves running:** when the chain stopped at a proximate link, the mechanism this fix does not reach — so the follow-up is filed rather than rediscovered

**Evidence:** signal link, event count, affected releases, the introducing commit
```

For `needs-info`, file the questions instead of the brief, under **What we established** and **What we still need**, so the verified work is not lost when the reporter answers.

## Step 6 — Fix, when it is small and certain

After filing, hand the fix to an implementing agent without asking again, but only when all four hold:

1. Disposition is `bug`.
2. `reproducer` confirmed the path — not "insufficient data".
3. No contradiction survived Step 3, `cause` came back at 80 or above, and its chain cleared the counterfactual.
4. The change stays inside one app or lib, and crosses no public API, migration, or auth boundary.

Any one of them failing ends the run at the filed issue. Say which one failed and why.
