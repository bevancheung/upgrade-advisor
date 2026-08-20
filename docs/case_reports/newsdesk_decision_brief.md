# Upgrade decision brief: newsdesk -> Qwen2.5-7B-Instruct-1M

**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.76%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **7.8** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **8.2** wrong per 100
- the new model used bare, with no training: about **15.3** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 500 real business questions: the new system fixed 2 and broke 4; everything else identical. Today you get ~7.8 wrong per 100 requests; retrained on the new model, ~8.2. Allowing for sampling error, the true gap is between -1.6% and +0.8%
2. **Disagreement list** -- 7 questions (1.4% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the new system is slightly better at knowing how sure to be (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -0.50% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path permits moving your existing work as-is

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 500 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*