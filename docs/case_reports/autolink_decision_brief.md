# Upgrade decision brief: autolink -> OLMo-1.7-7B

**Stay put -- do not upgrade this round.** The data proves the new model would improve quality by at most 0.47%, which does not cover the cost of migrating. Zero spend.

## Where you stand
- current system: about **0.8** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **1.8** wrong per 100
- the new model used bare, with no training: about **22.1** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 380 real business questions: the new system fixed 1 and broke 5; everything else identical. Today you get ~0.8 wrong per 100 requests; retrained on the new model, ~1.8. Allowing for sampling error, the true gap is between -2.6% and +0.5%
2. **Disagreement list** -- 6 questions (1.6% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of -0.67% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. zero spend, zero change this round
2. re-run this evaluation at the next model release (~30 GPU-minutes)

## How much to trust this
- every number comes from measured runs on your own 380 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*