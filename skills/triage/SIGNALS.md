# Signals

Where each case-file field comes from, and what to do when the source is not there.

The tools below are the ones this skill was built against: `sentry-cli` and the Sentry Web API, [`pup`](https://github.com/DataDog/pup) for Datadog, `linear` for the tracker, `gh` for GitHub. An equivalent for your stack works the same way. Probe first; a missing tool is a field marked `unknown`, not a stalled triage.

```bash
for t in sentry-cli pup linear gh; do printf '%-12s %s\n' "$t" "$(command -v $t || echo missing)"; done
sentry-cli info
pup auth status
```

## Sentry

`sentry-cli` covers search and bulk state. It does **not** return a stack trace, so the event body comes from the Web API with `SENTRY_AUTH_TOKEN`.

```bash
sentry-cli issues list --org "$ORG" --project "$PROJECT" --query 'is:unresolved' --max-rows 25
sentry-cli events list --org "$ORG" --project "$PROJECT" --show-tags --show-user --max-rows 20
```

The issue id is the last path segment of a Sentry issue URL.

```bash
S="https://sentry.io/api/0"
A=(-sS -H "Authorization: Bearer $SENTRY_AUTH_TOKEN")

curl "${A[@]}" "$S/issues/$ISSUE_ID/"
curl "${A[@]}" "$S/issues/$ISSUE_ID/events/latest/"
curl "${A[@]}" "$S/issues/$ISSUE_ID/tags/release/"
curl "${A[@]}" "$S/organizations/$ORG/issues/?query=is:unresolved&statsPeriod=14d"
```

- `issues/{id}/` gives title, culprit, `firstSeen`, `lastSeen`, `count`, `userCount`, and the 24h/30d `stats` series that decide rate shape.
- `events/latest/` gives the frames, the request, and the tags for one real event.
- `tags/release/` gives the release spread, which is how you tell a fresh regression from a long-standing fault.

Without a token or a CLI, ask for a paste and name exactly what you need: the issue URL, the exception type and message, the in-app frames, first seen, event count, and the affected release.

## Datadog

`pup` is the Datadog API CLI. It authenticates with `pup auth login` or `DD_API_KEY` + `DD_APP_KEY` + `DD_SITE`. In agent mode `--help` returns a JSON schema, so read the schema for a command's flags rather than guessing:

```bash
pup logs query --help
pup agent schema
```

The groups that carry triage evidence:

| Need | Command group |
| --- | --- |
| the same error, server side | `pup error-tracking issues` |
| surrounding logs, and counts without pulling raw logs | `pup logs query`, `pup logs aggregate --compute=count`, `pup logs patterns` |
| the failing request path and its latency | `pup traces search`, `pup traces aggregate` |
| browser-side reproduction and session replay | `pup rum sessions`, `pup rum events`, `pup rum replay` |
| what deployed into the first-seen window | `pup events search`, `pup change-stories list`, `pup cicd pipelines` |
| whether a flag gates the broken path | `pup feature-flags flags`, `pup feature-flags exposure` |
| whether this is already a known incident | `pup incidents list`, `pup monitors search` |

Always pass `--from`; the default window is an hour and it will quietly mislead you. APM durations are nanoseconds. Append `--no-agent` to any command you hand back for a human to run, since agent mode wraps output in an envelope theirs will not have.

A Datadog MCP in the session covers the same ground and is fine to use instead.

## Prior art

```bash
linear issue query --search "<error type or symptom>" --all-teams --json --limit 20
linear issue query --search "<symbol name>" --search-comments --all-teams --json
gh search issues --repo "$REPO" "<error type>" --state all
gh pr list --repo "$REPO" --search "<symbol name>" --state merged --limit 20
```

Search by the domain concept as well as the literal error string. The same defect gets filed under different words each time. If the team records decisions to not fix something somewhere outside the tracker, search that too.

## Regression window

```bash
git log --since="$FIRST_SEEN" --oneline
git log -S'<symbol from the top frame>' --oneline --all
git log --oneline -20 -- "<the failing area>"
```

A commit inside the window that touches the failing path is a candidate, not a conclusion; the `cause` seat has to connect it to the defect.

## Filing

Write the brief to a file first — `--description-file` keeps the markdown intact where `-d` does not.

```bash
linear issue create \
  --title "<one line>" \
  --description-file "$BRIEF" \
  --team "$TEAM" \
  --label bug \
  --priority 2 \
  --state Triage \
  --no-interactive

linear issue link "$ISSUE" "$SENTRY_URL"
```

Linear's priority is 1-4 descending, so P0 is `--priority 1` and P3 is `--priority 4`. Confirm `--state` and `--label` exist in the workspace before relying on them.
