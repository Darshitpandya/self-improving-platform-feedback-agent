"""Friction correlator — uses Amazon Bedrock to correlate signals with golden path steps.

This is the reasoning layer that makes this an agent, not a script.
Without it, you have signal collection. With it, you have structured
improvement proposals that identify which golden path step is causing
friction and what to do about it.
"""

import json
import os
from pathlib import Path

from models import ImprovementProposal, FrictionSignal

_DRY_RUN_PROPOSALS = [
    ImprovementProposal(
        title="Make logging sidecar optional",
        golden_path_step="logging-sidecar",
        problem="62% of teams (52/84 services) removed the logging sidecar within 7 days of scaffolding. PR comments cite 'too much log noise' and 'conflicts with existing logging setup.'",
        recommendation="Make the logging sidecar opt-in instead of opt-out. Provide a lightweight alternative that integrates with existing logging setups.",
        confidence=0.89,
        estimated_impact="+15-20% template adoption based on removal-rate correlation",
        evidence=[
            FrictionSignal(source="git_removals", detail="52/84 services removed sidecar within 7 days"),
            FrictionSignal(source="pr_comments", detail="14 mentions of 'logging' + 'template' in 90 days"),
            FrictionSignal(source="scorecard_trends", detail="'structured-logging' rule flat at 38% for 30+ days"),
        ],
    ),
    ImprovementProposal(
        title="Reduce CI security scan scope for non-production",
        golden_path_step="security-scan",
        problem="Security scan averages 6.2 minutes. 40% of teams added a skip flag to bypass it.",
        recommendation="Run full security scan on main branch only. Use a lightweight scan (critical CVEs only) for feature branches.",
        confidence=0.76,
        estimated_impact="Reduce CI time by ~5 min for feature branches, remove incentive to skip security",
        evidence=[
            FrictionSignal(source="ci_friction", detail="security-scan step averaging 6.2 min, 40% skip rate"),
            FrictionSignal(source="pr_comments", detail="5 comments mentioning 'CI + slow'"),
        ],
    ),
    ImprovementProposal(
        title="Add database migration helper to scaffold",
        golden_path_step="db-migration",
        problem="No database migration framework in the golden path. Teams build their own, inconsistently.",
        recommendation="Add a lightweight migration helper (e.g., Alembic for Python) as an optional golden path module.",
        confidence=0.72,
        estimated_impact="Reduce onboarding time for data-backed services, standardise migration patterns",
        evidence=[
            FrictionSignal(source="pr_comments", detail="8 comments mentioning 'auth module + workaround' — many related to DB setup"),
            FrictionSignal(source="scorecard_trends", detail="'api-docs-complete' rule flat at 29% — correlated with missing DB docs"),
        ],
    ),
]


def correlate(signals: dict, dry_run: bool = False) -> list[ImprovementProposal]:
    """Correlate friction signals with golden path steps using Amazon Bedrock."""
    if dry_run:
        return _DRY_RUN_PROPOSALS

    return _call_bedrock(signals)


def _call_bedrock(signals: dict) -> list[ImprovementProposal]:
    """Call Amazon Bedrock via Anthropic SDK + Instructor for structured proposals."""
    import anthropic
    import instructor

    region = os.environ.get("AWS_DEFAULT_REGION", "ap-southeast-2")
    model_id = os.environ.get("BEDROCK_MODEL_ID", "au.anthropic.claude-sonnet-4-6")

    golden_path_steps = json.loads((Path("sample-data") / "golden-path-steps.json").read_text())

    bedrock_client = anthropic.AnthropicBedrock(aws_region=region)
    client = instructor.from_anthropic(bedrock_client)

    prompt = (
        "You are a platform engineering feedback agent. Analyse these developer behaviour "
        "signals and generate improvement proposals for the golden path template.\n\n"
        f"Signals:\n{json.dumps(signals, indent=2)}\n\n"
        f"Golden path steps:\n{json.dumps(golden_path_steps, indent=2)}\n\n"
        "For each friction pattern you identify:\n"
        "- Correlate it with a specific golden path step\n"
        "- Explain the problem with data\n"
        "- Provide a specific, actionable recommendation\n"
        "- Assess confidence (0-1) based on signal strength\n"
        "- Only propose if confidence > 0.7\n"
        "- List the evidence signals that support the proposal\n\n"
        "Generate up to 3 proposals, ordered by confidence."
    )

    return client.messages.create(
        model=model_id,
        response_model=list[ImprovementProposal],
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
    )
