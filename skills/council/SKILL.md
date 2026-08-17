---
name: council
description: Isolated multi-agent planning. Planners never share context; you broker information and synthesize. Use when the user wants a council, independent second opinions, multi-model planning, or an A-vs-B decision.
---

# Council

You are the orchestrator. Independent planners never see each other. You are the only one who reads every reply and decides what each planner learns next.

Do not simulate a council in one transcript. Run the helper.

## Skill path

Set once, then use `"$COUNCIL"`:

```bash
export COUNCIL="${COUNCIL:-$HOME/.agents/skills/council/scripts/council}"
```

Claude Code: `$HOME/.claude/skills/council/scripts/council`.
This checkout: `skills/council/scripts/council`.

## Default panel

| Seat | Engine | Model | Job |
|---|---|---|---|
| builder | `codex` | `gpt-5.6-sol` | Practical implementation and feasibility |
| critic | `cursor` | `kimi-k3-max` | Risks, assumptions, alternatives, failure modes |

Swap engines freely (`claude`, `opencode`, or `--bin`). Roles are seats, not models. More than two planners is fine. `--model` overrides the engine default.

## Run

Prompt on stdin. One process, one planner, no shared state.

```bash
"$COUNCIL" ask --engine codex <<'EOF'
<isolated builder prompt>
EOF

"$COUNCIL" ask --engine cursor <<'EOF'
<isolated critic prompt>
EOF
```

Run the first round in parallel. Wait for both before reading either.

## Planner prompt

Give every planner this shape. Do not include another planner's output.

```text
You are <name>. <role>

Objective:
<user objective>

Constraints:
- ...

Repository: <cwd only if relevant; do not dump the tree>

Selected insights:
- <only claims you chose to share; omit this section in round 1>

Questions:
- <your follow-ups; omit in round 1>

Reply with:
- recommendation
- assumptions
- risks
- alternatives
- open questions
- confidence 0-100

No chain-of-thought. No hidden reasoning.
```

## Invariants

1. Planner A cannot see planner B's reply.
2. Planner B cannot see planner A's reply.
3. Planners never see your notes or the full council state.
4. Everything that moves between planners goes through you.
5. You decide the exact prompt each planner gets.
6. Round 1 is blind: same objective, no selected insights, no questions.

Share **claims, questions, observations** — not transcripts. Never forward `Planner A said: "..."`.

## Loop

1. Blind round: all planners, identical objective, nothing from each other.
2. Compare: agreement, disagreement, missing information.
3. If needed, share selected insights and/or ask a follow-up. Still isolated.
4. Stop after 3 planner rounds, or sooner when you can decide.
5. Synthesize. Return only the synthesis unless the user asked for verbose.

## Synthesis

```text
Decision
========
<recommended approach>

Why
===
<key reasoning>

Agreement
=========
<where planners agreed>

Disagreements
=============
<important disagreements>

Risks
=====
<remaining risks>

Alternatives
============
<important alternatives>

Confidence
==========
<0-100>

Next Steps
==========
<concrete implementation steps>
```
