#!/usr/bin/env python3
"""The Self-Improving Platform: Feedback loop agent.

Orchestrator — coordinates the agent pipeline:
  collectors (4 signals) → friction_correlator (Bedrock) → proposal_publisher (GitHub Issues)

Usage:
    python agent/orchestrator.py --analyse --window 90d
    python agent/orchestrator.py --analyse --window 90d --dry-run
"""

import argparse
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.collectors import git_removals, ci_friction, scorecard_trends, pr_comments
from agent.friction_correlator import correlate
from agent.proposal_publisher import publish
from agent.pattern_memory import PatternMemory


def main():
    load_dotenv()

    parser = argparse.ArgumentParser(description="Platform feedback loop agent")
    parser.add_argument("--analyse", action="store_true", required=True, help="Run signal analysis")
    parser.add_argument("--window", default="90d", help="Analysis window (e.g., 90d)")
    parser.add_argument("--data-dir", default="sample-data", help="Path to signal data directory")
    parser.add_argument("--dry-run", action="store_true", help="Use hardcoded proposals instead of Bedrock")
    args = parser.parse_args()

    start = time.time()
    print(f"\n🔄 Platform Feedback Agent")
    print(f"{'─' * 50}")

    # Step 1: Collect signals
    print(f"\nCollecting signals (window: {args.window})...")
    signals = {}

    git_data = git_removals.collect(args.data_dir)
    signals["git_removals"] = git_data
    patterns = len(git_data.get("removal_patterns", []))
    print(f"├── Git removals: {git_data.get('services_analysed', 0)} services analysed, {patterns} removal patterns found")

    ci_data = ci_friction.collect(args.data_dir)
    signals["ci_friction"] = ci_data
    slow = [s for s in ci_data.get("slow_steps", []) if s.get("avg_duration_min", 0) > 5]
    print(f"├── CI friction: {len(slow)} slow steps identified (>5 min)")

    sc_data = scorecard_trends.collect(args.data_dir)
    signals["scorecard_trends"] = sc_data
    flat = len(sc_data.get("flat_rules", []))
    print(f"├── Scorecard trends: {flat} flat rules (30+ days)")

    pr_data = pr_comments.collect(args.data_dir)
    signals["pr_comments"] = pr_data
    mentions = sum(c.get("count", 0) for c in pr_data.get("relevant_comments", []))
    print(f"└── PR comments: {mentions} relevant mentions")

    # Step 2: Check pattern memory
    memory = PatternMemory()
    for pattern in git_data.get("removal_patterns", []):
        summary = f"module:{pattern['module']} removal_rate:{pattern['removal_rate']}"
        if memory.check_regression(summary):
            print(f"  ⚠️  Regression detected: {pattern['module']} was previously resolved but friction recurred")
        memory.store(summary, pattern["module"])

    # Step 3: Correlate with golden path steps
    mode = "dry-run (hardcoded)" if args.dry_run else "Amazon Bedrock"
    print(f"\nCorrelating with golden path steps via {mode}...")
    proposals = correlate(signals, dry_run=args.dry_run)

    # Filter by confidence threshold
    threshold = 0.7
    proposals = [p for p in proposals if p.confidence >= threshold]
    print(f"\nProposals generated: {len(proposals)} (confidence threshold: >{threshold:.0%})")
    for i, p in enumerate(proposals, 1):
        print(f"├── #{i}: {p.title} (confidence: {p.confidence:.0%})")

    if not proposals:
        print("\n✅ No high-confidence proposals. Platform is healthy.")
        return

    # Step 4: Publish as GitHub Issues
    print(f"\nPublishing to GitHub...")
    urls = publish(proposals)

    for url in urls:
        print(f"├── Issue created: {url}")

    elapsed = time.time() - start
    print(f"\n{'─' * 50}")
    print(f"🔄 Analysis complete")
    print(f"   Proposals: {len(proposals)} | Published: {len(urls)} | Elapsed: {elapsed:.0f} seconds")


if __name__ == "__main__":
    main()
