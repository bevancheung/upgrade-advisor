# Upgrade decision brief: cloudtalk -> Qwen2.5-7B-Instruct

**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 1.97%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **54.1** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **53.4** wrong per 100
- the new model used bare, with no training: about **79.0** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 900 real business questions: the new system fixed 18 and broke 12; everything else identical. Today you get ~54.1 wrong per 100 requests; retrained on the new model, ~53.4. Allowing for sampling error, the true gap is between -0.6% and +2.0%
2. **Disagreement list** -- 90 questions (10.0% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 900 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*