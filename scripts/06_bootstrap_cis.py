"""95% bootstrap confidence intervals for the rewrite effects (flip rate, change in acceptance of wrong code,
mean change in P(Yes)) for each judge."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.common import DATA, RESULTS, load_json

items = load_json(os.path.join(DATA, "items.json"))
md = []
for which in ["A", "B"]:
    S = load_json(os.path.join(DATA, f"scores_{which}.json"))
    rng = np.random.default_rng(0)

    def ci(x):
        x = np.asarray(x, float)
        bs = [x[rng.integers(0, len(x), len(x))].mean() for _ in range(10000)]
        return x.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)

    md += [f"## judge {which}", "", "| rewrite | n | verdict flips | change in acceptance of wrong code | mean change in P(Yes) |", "|---|---|---|---|---|"]
    for t in ["rename", "reformat", "claim_tested", "claim_doubt"]:
        a = np.array([(S[str(i)]["original"], S[str(i)][t], it["gold"]) for i, it in enumerate(items) if t in S[str(i)]])
        fl = ci((a[:, 0] > 0.5) != (a[:, 1] > 0.5))
        w = a[a[:, 2] == 0]
        da = ci((w[:, 1] > 0.5).astype(float) - (w[:, 0] > 0.5).astype(float))
        dp = ci(a[:, 1] - a[:, 0])
        md.append(f"| {t} | {len(a)} | {fl[0]:.3f} ({fl[1]:.3f} to {fl[2]:.3f}) | {da[0]:+.3f} ({da[1]:+.3f} to {da[2]:+.3f}), n={len(w)} | {dp[0]:+.3f} ({dp[1]:+.3f} to {dp[2]:+.3f}) |")
    md.append("")
open(os.path.join(RESULTS, "bootstrap_cis.md"), "w").write("\n".join(md))
print("\n".join(md))
