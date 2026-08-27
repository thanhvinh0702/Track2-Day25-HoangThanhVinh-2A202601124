"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly",
                 baseline_per_m: float | None = None,
                 optimized_per_m: float | None = None,
                 analysis: list[str] | None = None) -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}  ",
        f"**Baseline spend:** ${baseline_usd:,.0f}  ",
        f"**Optimized spend:** ${optimized_usd:,.0f}  ",
        f"**Projected savings:** ${savings:,.0f}  (**{pct:.0f}%**)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    if baseline_per_m is not None and optimized_per_m is not None:
        lines[5:5] = [
            f"**Inference unit cost:** ${baseline_per_m:.3f} → ${optimized_per_m:.3f} / 1M-token",
            "",
        ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.0f} |")
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Energy per query: {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query: {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cheapest+cleanest region: {sustainability.get('best_region', 'n/a')}",
        ]
        if "reasoning_fraction" in sustainability:
            lines += [
                f"- Cache economics: {sustainability.get('avg_cache_reads', 0):.2f} estimated reads; "
                f"cache enabled: {sustainability.get('cache_enabled', False)}",
                f"- Reasoning traffic: {sustainability['reasoning_fraction']:.1%} of requests; "
                f"${sustainability.get('reasoning_cost', 0):,.2f} optimized cost "
                f"({sustainability.get('reasoning_cost_pct', 0):.1f}% of optimized inference)",
                f"- Reasoning energy multiplier: {sustainability.get('reasoning_energy_multiplier', 0):.1f}x vs non-reasoning traffic",
                f"- 10% reasoning cap estimate: save ${sustainability.get('reasoning_cap_cost_savings', 0):,.2f}/day "
                f"and {sustainability.get('reasoning_cap_wh_savings', 0):,.1f} Wh/day",
            ]
    if analysis:
        lines += ["", "## Recommended actions", ""]
        lines += [f"{i}. {item}" for i, item in enumerate(analysis, 1)]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str) -> str:
    """Write a simple savings bar chart PNG. Returns the path. No-op if matplotlib absent."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, vals, color="#2e548a")
    ax.set_ylabel("Savings (USD / month)")
    ax.set_title("GPU cost savings by FinOps lever")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
