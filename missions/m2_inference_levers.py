"""M2 — Inference Cost Levers: $/1M-token, batch x cache x cascade (deck §7).

Run: python missions/m2_inference_levers.py
"""
from __future__ import annotations
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
from missions._common import load_csv, num
from finops import pricing

# $/1M tokens (input, output) — illustrative 2026.
MODEL_PRICES = {"small": (0.20, 0.40), "large": (3.00, 15.00)}


def run(verbose: bool = True) -> dict:
    rows = load_csv("token_usage.csv")
    base_cost = opt_cost = 0.0
    reasoning_base_cost = reasoning_opt_cost = 0.0
    reasoning_wh = non_reasoning_wh = 0.0
    reasoning_requests = 0
    total_tokens = 0
    total_input = sum(int(num(r["input_tokens"])) for r in rows)
    total_cached = sum(int(num(r["cached_input_tokens"])) for r in rows)
    avg_cache_reads = 1.0 + (total_cached / total_input if total_input else 0.0)
    cache_enabled = pricing.cache_is_worth_it(avg_cache_reads, write_cost_per_m=0.10)
    from finops import sustainability
    for r in rows:
        inp, out = int(num(r["input_tokens"])), int(num(r["output_tokens"]))
        cached = int(num(r["cached_input_tokens"]))
        is_batch = bool(int(num(r["is_batch"])))
        is_reasoning = bool(int(num(r["is_reasoning"])))
        total_tokens += inp + out
        # BASELINE: naive deployment — everything on the large model, no cache, no batch
        lin, lout = MODEL_PRICES["large"]
        base_cost += pricing.request_cost(inp, out, lin, lout)
        # OPTIMIZED: cascade (route_tier), prompt caching, batch API
        pin, pout = MODEL_PRICES[r["route_tier"]]
        effective_cached = cached if cache_enabled else 0
        opt_cost += pricing.request_cost(inp, out, pin, pout, cached_in=effective_cached, batch=is_batch)
        base_request = pricing.request_cost(inp, out, lin, lout)
        opt_request = pricing.request_cost(inp, out, pin, pout, cached_in=effective_cached, batch=is_batch)
        if is_reasoning:
            reasoning_requests += 1
            reasoning_base_cost += base_request
            reasoning_opt_cost += opt_request
            reasoning_wh += sustainability.wh_per_query(inp + out, is_reasoning=True)
        else:
            non_reasoning_wh += sustainability.wh_per_query(inp + out)

    # Extension 3: cache economics. The gate above is applied to effective_cached,
    # so a workload that does not repay cache writes receives no cache savings.

    # Extension 4: reasoning budget. Measure the current tax and a 10% traffic
    # cap using the mean reasoning request cost/energy as a conservative estimate.
    cap = max(1, int(round(len(rows) * 0.10)))
    excess_reasoning = max(0, reasoning_requests - cap)
    avg_reasoning_cost = reasoning_opt_cost / reasoning_requests if reasoning_requests else 0.0
    avg_reasoning_wh = reasoning_wh / reasoning_requests if reasoning_requests else 0.0
    cap_cost_savings = excess_reasoning * avg_reasoning_cost
    cap_energy_savings = excess_reasoning * avg_reasoning_wh

    base_pm = pricing.dollars_per_million(base_cost, total_tokens)
    opt_pm = pricing.dollars_per_million(opt_cost, total_tokens)
    savings_pct = (1 - opt_cost / base_cost) * 100 if base_cost else 0.0

    if verbose:
        print("== M2 Inference Cost Levers ==")
        print(f"requests={len(rows)}  tokens={total_tokens:,}")
        print(f"baseline  : ${base_cost:,.2f}/day   ${base_pm:.3f}/1M-token")
        print(f"optimized : ${opt_cost:,.2f}/day   ${opt_pm:.3f}/1M-token")
        print(f"savings   : {savings_pct:.1f}%  (cascade + caching + batch)")
        print(f"discount stack (batch + 100% cache): {pricing.discount_stack(batch=True, cache_hit_frac=1.0):.3f} of naive")
        print(f"cache economics: avg_reads={avg_cache_reads:.2f}, enabled={cache_enabled}")
        print(f"reasoning: {reasoning_requests/len(rows):.1%} of requests, ${reasoning_opt_cost:,.2f} optimized cost, {reasoning_wh:,.1f} Wh")
        print(f"reasoning cost share: {reasoning_opt_cost/opt_cost:.1%}; energy multiplier vs non-reasoning: {reasoning_wh/non_reasoning_wh:.1f}x")
        print(f"10% reasoning cap: save ${cap_cost_savings:,.2f}/day and {cap_energy_savings:,.1f} Wh/day")

    return {
        "baseline_daily": round(base_cost, 2), "optimized_daily": round(opt_cost, 2),
        "baseline_per_m": round(base_pm, 3), "optimized_per_m": round(opt_pm, 3),
        "savings_pct": round(savings_pct, 1), "total_tokens": total_tokens,
        "cache_enabled": cache_enabled, "avg_cache_reads": round(avg_cache_reads, 3),
        "reasoning_requests": reasoning_requests,
        "reasoning_fraction": round(reasoning_requests / len(rows), 4) if rows else 0.0,
        "reasoning_cost": round(reasoning_opt_cost, 2),
        "reasoning_cost_pct": round(reasoning_opt_cost / opt_cost * 100, 1) if opt_cost else 0.0,
        "reasoning_wh": round(reasoning_wh, 2), "non_reasoning_wh": round(non_reasoning_wh, 2),
        "reasoning_cap_cost_savings": round(cap_cost_savings, 2),
        "reasoning_cap_wh_savings": round(cap_energy_savings, 2),
    }


if __name__ == "__main__":
    run()
