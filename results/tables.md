Items: 200 (one judge-A top pick and one random sample per mixed problem)

## judge A (Qwen2.5-7B)

| rewrite | n | verdict flips | mean change in P(Yes), correct code | mean change, wrong code | accept rate on wrong code: before -> after |
|---|---|---|---|---|---|
| rename | 195 | 0.328 | -0.306 | -0.238 | 0.518 -> 0.250 (n=56) |
| reformat | 128 | 0.055 | -0.005 | -0.024 | 0.459 -> 0.459 (n=37) |
| claim_tested | 199 | 0.080 | +0.064 | +0.077 | 0.492 -> 0.559 (n=59) |
| claim_doubt | 199 | 0.211 | -0.210 | -0.223 | 0.492 -> 0.254 (n=59) |

Routing: AUROC for finding the judge's own errors (verdict at 0.5 differs from hidden tests), and share of errors caught when the top 20% most suspicious items go to a human.

| item set | n | errors | uncertainty AUROC | flip-rate AUROC | score-spread AUROC | uncertainty+flip AUROC | caught@20%: uncertainty | caught@20%: flip+uncertainty |
|---|---|---|---|---|---|---|---|---|
| random_sample | 100 | 26 (0.26) | 0.623 | 0.498 | 0.586 | 0.575 | 0.38 | 0.23 |
| top_pick_A | 100 | 27 (0.27) | 0.672 | 0.536 | 0.593 | 0.616 | 0.37 | 0.30 |
| all | 200 | 53 (0.27) | 0.632 | 0.517 | 0.583 | 0.590 | 0.38 | 0.26 |

## judge B (Llama-3.1-8B)

| rewrite | n | verdict flips | mean change in P(Yes), correct code | mean change, wrong code | accept rate on wrong code: before -> after |
|---|---|---|---|---|---|
| rename | 195 | 0.374 | -0.311 | -0.224 | 0.786 -> 0.464 (n=56) |
| reformat | 128 | 0.062 | -0.015 | -0.023 | 0.757 -> 0.757 (n=37) |
| claim_tested | 199 | 0.080 | +0.101 | +0.115 | 0.763 -> 0.847 (n=59) |
| claim_doubt | 199 | 0.683 | -0.533 | -0.464 | 0.763 -> 0.169 (n=59) |

Routing: AUROC for finding the judge's own errors (verdict at 0.5 differs from hidden tests), and share of errors caught when the top 20% most suspicious items go to a human.

| item set | n | errors | uncertainty AUROC | flip-rate AUROC | score-spread AUROC | uncertainty+flip AUROC | caught@20%: uncertainty | caught@20%: flip+uncertainty |
|---|---|---|---|---|---|---|---|---|
| random_sample | 100 | 34 (0.34) | 0.638 | 0.516 | 0.503 | 0.597 | 0.32 | 0.21 |
| top_pick_A | 100 | 25 (0.25) | 0.594 | 0.442 | 0.411 | 0.518 | 0.24 | 0.16 |
| all | 200 | 59 (0.29) | 0.619 | 0.481 | 0.453 | 0.564 | 0.27 | 0.20 |
