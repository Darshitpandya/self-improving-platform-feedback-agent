# The Self-Improving Platform: Closing the Feedback Loop with Agents

> **"Your developers are already telling you what's wrong — through their behaviour. Build the agent that listens."**

Most platforms improve on a quarterly survey cadence. By the time you learn what's wrong, you've already built the next thing on top of it. This **feedback agent** closes the loop by watching developer behaviour, correlating friction with specific golden path steps using Amazon Bedrock, and surfacing structured improvement proposals as GitHub Issues — weekly, not quarterly.

This is not a survey tool. A survey asks developers what they think. An **agent** observes what they do — which modules they remove, which CI steps they skip, which scorecard rules never improve — and reasons about what the platform should change.

**PlatformCon 2026** — Darshit Pandya | Senior Principal Engineer – Platform @ Serko

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     SIGNAL SOURCES                            │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌───────┐ │
│  │ Git History  │  │ OpenTelemetry│  │ Portal   │  │  PR   │ │
│  │ (post-       │  │ (CI/CD       │  │ Scorecard│  │Review │ │
│  │  scaffold    │  │  pipeline    │  │ Trends   │  │Comments│ │
│  │  removals)   │  │  traces)     │  │          │  │       │ │
│  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  └───┬───┘ │
└─────────┼─────────────────┼────────────────┼────────────┼─────┘
          │                 │                │            │
          ▼                 ▼                ▼            ▼
   ┌──────────────────────────────────────────────────────────┐
   │              FEEDBACK AGENT                               │
   │                                                           │
   │  Collect signals → Correlate with golden path steps       │
   │  (Amazon Bedrock) → Generate typed proposals              │
   │  (Instructor / Pydantic)                                  │
   └──────────────────────────┬────────────────────────────────┘
                              │
                              ▼
   ┌──────────────────────────────────────────────────────────┐
   │              OUTPUT: GitHub Issues                        │
   │                                                           │
   │  Structured improvement proposals                         │
   │  with data, confidence, estimated impact                  │
   │  → Human reviews → Roadmap item (or reject)               │
   └──────────────────────────────────────────────────────────┘
```

### Why an Agent, Not a Survey

| | Quarterly Survey | Feedback Agent |
|---|---|---|
| **Signal source** | What developers say (filtered, delayed) | What developers do (git, CI, code reviews) |
| **Cadence** | Quarterly | Weekly (or on-demand) |
| **Response rate** | 15-25% | 100% — behavioural data is always available |
| **Time to insight** | Months | The next agent run |
| **Output** | Vague themes | Structured proposals tied to specific golden path steps |

**Amazon Bedrock is what makes this an agent.** Without it, you have signal collection. With it, you have an autonomous system that observes developer behaviour, reasons about which golden path step is causing friction, and proposes specific improvements — the four properties of an agent.

---

## Quick Start

### Prerequisites

- Python 3.11+
- GitHub personal access token with `repo` scope
- AWS account with Amazon Bedrock access (Claude Sonnet enabled) — **required for the agent to reason**

### Setup

```bash
git clone https://github.com/Darshitpandya/self-improving-platform-feedback-agent.git
cd self-improving-platform-feedback-agent

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your GITHUB_TOKEN, GITHUB_REPO, and AWS credentials
```

### Run (Full Agent — Bedrock Reasoning)

```bash
python agent/orchestrator.py --analyse --window 90d
```

This is the full agent loop: collect 4 signals → **correlate with golden path steps** (Bedrock) → publish proposals as GitHub Issues. Bedrock analyses the friction patterns, identifies which golden path step is responsible, and generates structured proposals with confidence scores.

### Run (Pipeline Test — Dry-Run, No Bedrock)

```bash
python agent/orchestrator.py --analyse --window 90d --dry-run
```

Dry-run skips Bedrock and uses hardcoded proposals. Use this to **test the pipeline** (signal collection, issue creation) without AWS credentials. Issues are still real.

> ⚠️ **Dry-run is for testing the pipeline, not for production.** Without Bedrock, the agent cannot correlate friction with golden path steps — it becomes a reporter, not an agent.

---

## What This Is

A **blueprint** for the Self-Improving Platform pattern — a working feedback agent you can fork, extend, and adapt.

- ✅ 4 signal collectors (git removals, CI friction, scorecard trends, PR comments)
- ✅ Autonomous agent pipeline: collect → **correlate (Bedrock)** → publish proposals
- ✅ Structured proposals via Instructor/Pydantic (typed, reviewable, not free-text)
- ✅ Real GitHub Issue creation with labels
- ✅ Confidence threshold filtering (only proposals >70%)
- ✅ Dry-run mode for pipeline testing
- ✅ GitHub Actions workflow (scheduled weekly — Monday before Tuesday triage)

## What This Is NOT

This is **not a production deployment**. To use in your production environment, follow the Production Adoption Guide below.

---

## Project Structure

```
agent/
├── orchestrator.py            Orchestrator — coordinates the agent pipeline
├── collectors/
│   ├── git_removals.py        Signal 1: Post-scaffold module removals
│   ├── ci_friction.py         Signal 2: CI pipeline slow steps
│   ├── scorecard_trends.py    Signal 3: Portal scorecard flat rules
│   └── pr_comments.py         Signal 4: PR review friction comments
├── friction_correlator.py     Calls Bedrock — the reasoning layer (AI)
└── proposal_publisher.py      Creates GitHub Issues from proposals
models/
└── __init__.py                Pydantic schemas (FrictionSignal, ImprovementProposal)
sample-data/
├── git-removals.json          Sample: 84 services, 3 removal patterns
├── ci-friction.json           Sample: CI step durations and skip rates
├── scorecard-trends.json      Sample: 4 flat scorecard rules
├── pr-comments.json           Sample: developer friction comments
└── golden-path-steps.json     Golden path step definitions
.github/workflows/
└── run-agent.yml              Scheduled every Monday at 8 AM
```

---

## The Four Signals

| Signal | Source | What It Detects | Example |
|---|---|---|---|
| Post-scaffold removals | Git history | Modules developers remove within 7 days | 62% removed logging sidecar |
| CI pipeline friction | OTel traces | Steps exceeding friction threshold (>5 min) | Security scan: 6.2 min, 40% skip rate |
| Stale scorecard rules | Portal trends | Rules where scores never improve (30+ days) | Test coverage rule flat at 42% |
| PR review friction | GitHub comments | Developer complaints about golden path components | 14 mentions of "logging + template" |

### Signals We Tried and Removed

| Signal | Why It Failed |
|---|---|
| Slack messages | 78% noise — platform keywords mixed with general chatter |
| Ticket descriptions | 65% noise — original friction buried under PM rewrites |

**The best friction signals come from where developers work — git, CI, code reviews. Not from where they talk about work.**

---

## Production Adoption Guide

### Step 1: Replace Collectors with Real API Integrations

Each collector reads from a sample JSON file. In production, replace with real API calls:

| Collector | Replace With |
|---|---|
| `git_removals.py` | GitHub API — compare scaffolded repos at day 0 vs day 7 |
| `ci_friction.py` | OTel/Prometheus API — query CI pipeline step durations |
| `scorecard_trends.py` | Port.io API — query scorecard score trends |
| `pr_comments.py` | GitHub API — search PR review comments for golden path keywords |

**Example — replacing `git_removals.py` for production:**

```python
from github import Github

def collect(org: str, window_days: int = 90) -> dict:
    gh = Github(os.environ["GITHUB_TOKEN"])
    removals = {}
    for repo in gh.get_organization(org).get_repos():
        # Compare files at scaffold commit vs 7 days later
        # Count which golden path modules were removed
        ...
    return {"services_analysed": len(repos), "removal_patterns": removals}
```

### Step 2: Add Your Golden Path Step Definitions

Edit `sample-data/golden-path-steps.json` to match your actual golden path template modules. The agent uses these to correlate friction signals with specific steps.

### Step 3: Configure the Confidence Threshold

Default is 0.7 (70%). Adjust in `orchestrator.py`:

```python
threshold = 0.7  # Only publish proposals above this confidence
```

Start high (0.8) to avoid noise. Lower as you trust the agent's proposals.

### Step 4: Merge Agent Proposals with Your Backlog

Agent proposals are GitHub Issues labelled `agent-proposal`. Treat them like any other backlog item:

- **Same triage process** — review in your weekly planning
- **Same prioritisation** — alongside human-generated items
- **Accept or reject** — the agent learns from your decisions over time
- **Never create a separate "AI backlog"** — that's how proposals get ignored

### Step 5: Evolve from Scheduled to Event-Driven

The blueprint runs weekly (Monday 8 AM). For faster feedback:

```
GitHub webhook (PR merged with golden path changes)
       │
       ▼
Agent triggered immediately
       │
       ▼
Friction detected within hours of a template change
```

### Step 6: Scope Bedrock IAM Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel"],
      "Resource": "arn:aws:bedrock:ap-southeast-2::foundation-model/au.anthropic.claude-sonnet-4-6"
    }
  ]
}
```

### Production Checklist

- [ ] Collectors query real APIs (not sample JSON)
- [ ] Golden path steps match your actual template
- [ ] Confidence threshold tuned (start at 0.8, lower over time)
- [ ] Agent proposals go through same triage as human items
- [ ] Bedrock IAM role scoped to `InvokeModel` only
- [ ] GitHub Actions uses OIDC federation (no stored AWS credentials)
- [ ] Schedule adjusted or evolved to event-driven

---

## License

MIT
