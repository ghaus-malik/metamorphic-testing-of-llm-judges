"""Analysis: verdict flips under rewrites, effect of correctness claims, and routing signals."""
import sys, os, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from harness.common import *
from harness.bon import auroc, boot_ci
from harness.transforms import NEUTRAL, CLAIMS

items = load_json(os.path.join(DATA, "items.json"))
out = {"n_items": len(items)}
md = []
for which, name in [("A", "judge A (Qwen2.5-7B)"), ("B", "judge B (Llama-3.1-8B)")]:
    path = os.path.join(DATA, f"scores_{which}.json")
    if not os.path.exists(path):
        continue
    S = load_json(path)
    res = {"transforms": {}, "routing": {}}
    md.append(f"## {name}\n")
    md.append("| rewrite | n | verdict flips | mean change in P(Yes), correct code | mean change, wrong code | accept rate on wrong code: before -> after |")
    md.append("|---|---|---|---|---|---|")
    for t in list(NEUTRAL) + list(CLAIMS):
        rows = [(S[str(i)]["original"], S[str(i)][t], it["gold"]) for i, it in enumerate(items) if t in S[str(i)]]
        if not rows:
            continue
        a = np.array(rows)
        flips = float(np.mean((a[:, 0] > 0.5) != (a[:, 1] > 0.5)))
        dc = float(np.mean(a[a[:, 2] == 1, 1] - a[a[:, 2] == 1, 0])) if (a[:, 2] == 1).any() else float("nan")
        dw = float(np.mean(a[a[:, 2] == 0, 1] - a[a[:, 2] == 0, 0])) if (a[:, 2] == 0).any() else float("nan")
        w = a[a[:, 2] == 0]
        fa0, fa1 = float(np.mean(w[:, 0] > 0.5)), float(np.mean(w[:, 1] > 0.5))
        res["transforms"][t] = dict(n=len(a), flip_rate=flips, dp_correct=dc, dp_wrong=dw, false_accept_before=fa0,
                                    false_accept_after=fa1, n_wrong=int(len(w)))
        md.append(f"| {t} | {len(a)} | {flips:.3f} | {dc:+.3f} | {dw:+.3f} | {fa0:.3f} -> {fa1:.3f} (n={len(w)}) |")
    md.append("")
    # routing signals
    md.append("Routing: AUROC for finding the judge's own errors (verdict at 0.5 differs from hidden tests), and share of errors caught when the top 20% most suspicious items go to a human.\n")
    md.append("| item set | n | errors | uncertainty AUROC | flip-rate AUROC | score-spread AUROC | uncertainty+flip AUROC | caught@20%: uncertainty | caught@20%: flip+uncertainty |")
    md.append("|---|---|---|---|---|---|---|---|---|")
    for role in ["random_sample", "top_pick_A", "all"]:
        sel = [i for i, it in enumerate(items) if role == "all" or it["role"] == role]
        p = np.array([S[str(i)]["original"] for i in sel])
        g = np.array([items[i]["gold"] for i in sel])
        err = ((p > 0.5).astype(int) != g).astype(int)
        neu = [[S[str(i)][t] for t in NEUTRAL if t in S[str(i)]] for i in sel]
        flip = np.array([np.mean([(v > 0.5) != (p[j] > 0.5) for v in vs]) if vs else 0.0 for j, vs in enumerate(neu)])
        spread = np.array([np.std([p[j]] + vs) for j, vs in enumerate(neu)])
        unc = 1 - 2 * np.abs(p - 0.5)
        comb = unc + flip
        def caught(sig, frac=0.2):
            k = max(1, int(round(frac * len(sig))))
            idx = np.argsort(-sig + 1e-9 * np.random.default_rng(0).random(len(sig)))[:k]
            return float(err[idx].sum() / max(1, err.sum()))
        r = dict(n=len(sel), errors=int(err.sum()), base_error_rate=float(err.mean()),
                 auroc_uncertainty=auroc(unc, err), auroc_flip=auroc(flip, err), auroc_spread=auroc(spread, err),
                 auroc_combined=auroc(comb, err), caught20_unc=caught(unc), caught20_comb=caught(comb),
                 false_accept_share=float(((p > 0.5) & (g == 0)).sum() / max(1, err.sum())))
        res["routing"][role] = r
        md.append(f"| {role} | {r['n']} | {r['errors']} ({r['base_error_rate']:.2f}) | {r['auroc_uncertainty']:.3f} | {r['auroc_flip']:.3f} | "
                  f"{r['auroc_spread']:.3f} | {r['auroc_combined']:.3f} | {r['caught20_unc']:.2f} | {r['caught20_comb']:.2f} |")
    md.append("")
    out[which] = res
with open(os.path.join(RESULTS, "results.json"), "w") as f:
    json.dump(out, f, indent=1)
with open(os.path.join(RESULTS, "tables.md"), "w") as f:
    f.write(f"Items: {len(items)} (one judge-A top pick and one random sample per mixed problem)\n\n" + "\n".join(md))
print("\n".join(md))
