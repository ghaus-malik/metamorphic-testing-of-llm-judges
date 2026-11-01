"""Metamorphic tests of LLM judges.

Stage 'build' (CPU): pick candidates, apply rewrites, re-run hidden tests, keep only rewrites whose
per-test results are identical to the original.
Stage 'score' (GPU): score originals and rewrites with judge A or B."""
import sys, os, random, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from harness.common import *
from harness.transforms import NEUTRAL, CLAIMS

stage = sys.argv[1]
gen = load_json(os.path.join(DATA, "generations_n16.json"))
ex = load_json(os.path.join(DATA, "exec_n16.json"))
probs = {p["pid"]: p for p in load_problems()}
items_path = os.path.join(DATA, "items.json")


def gold(r):
    return int(bool(r["bits"]) and min(r["bits"]) == 1)


if stage == "build":
    JA = load_json(os.path.join(DATA, "judge_A.json"))
    JB = load_json(os.path.join(DATA, "judge_B.json"))
    rng = random.Random(0)
    items = []
    for pid, cands in gen.items():
        keys = [pid + "::" + h(c["code"]) for c in cands]
        if not all(k in JA and k in JB for k in keys):
            continue
        A = [JA[k]["p_yes"] for k in keys]
        top = int(np.argmax(A))
        others = [i for i in range(16) if cands[i]["code"] != cands[top]["code"]]
        rnd = rng.choice(others) if others else top
        for role, i in [("top_pick_A", top), ("random_sample", rnd)]:
            items.append(dict(pid=pid, role=role, code=cands[i]["code"], gold=gold(ex[keys[i]]),
                              bits=ex[keys[i]]["bits"], variants={}))
    jobs, where = [], []
    for it in items:
        for name, f in {**NEUTRAL, **CLAIMS}.items():
            try:
                v = f(it["code"], probs[it["pid"]]["entry"])
            except Exception:
                v = None
            if v is None or v == it["code"]:
                continue
            jobs.append((v, probs[it["pid"]])); where.append((it, name, v))
    print("items", len(items), "variants to execute", len(jobs), flush=True)
    res = run_many(jobs)
    kept = dropped = 0
    for (it, name, v), r in zip(where, res):
        if r["bits"] == it["bits"]:
            it["variants"][name] = v; kept += 1
        else:
            dropped += 1
    print("variants kept", kept, "dropped (behavior changed or crashed)", dropped)
    for it in items:
        it.pop("bits")
    save_json(items, items_path)

elif stage == "score":
    which = sys.argv[2]
    J = LogitJudge({"A": JUDGE_A, "B": JUDGE_B}[which])
    items = load_json(items_path)
    msgs, where = [], []
    for i, it in enumerate(items):
        task = probs[it["pid"]]["task"]
        msgs.append(judge_messages(task, it["code"])); where.append((i, "original"))
        for name, v in it["variants"].items():
            msgs.append(judge_messages(task, v)); where.append((i, name))
    sp = os.path.join(DATA, f"scores_{which}.json")
    out = load_json(sp) if os.path.exists(sp) else {}
    # the original (unrewritten) code was already scored with the identical prompt by scripts/03_judge.py
    prev = load_json(os.path.join(DATA, f"judge_{which}.json"))
    for i, it in enumerate(items):
        k = it["pid"] + "::" + h(it["code"])
        if k in prev:
            out.setdefault(str(i), {})["original"] = prev[k]["p_yes"]
    todo = [k for k, (i, name) in enumerate(where) if name not in out.get(str(i), {})]
    print("prompts", len(msgs), "remaining", len(todo), flush=True)
    B = 150
    import time
    t = time.time()
    for s in range(0, len(todo), B):
        ks = todo[s:s + B]
        r = J.score([msgs[k] for k in ks])
        for k, v in zip(ks, r):
            i, name = where[k]
            out.setdefault(str(i), {})[name] = v["p_yes"]
        save_json(out, sp)
        print(f"{min(s+B, len(todo))}/{len(todo)} {time.time()-t:.0f}s", flush=True)
