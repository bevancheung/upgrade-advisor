# Upgrade decision brief: dineco -> Qwen2-7B-Instruct

**Skip this generation.** Combining your data with 193 published measured cases, this upgrade has only a 5% chance of paying off. Not worth further verification spend; stay put and re-evaluate at the next release.

## Where you stand
- current system: about **4.2** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **4.4** wrong per 100
- the new model used bare, with no training: about **19.0** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 360 real business questions: the new system fixed 3 and broke 4; everything else identical. Today you get ~4.2 wrong per 100 requests; retrained on the new model, ~4.4. Allowing for sampling error, the true gap is between -2.0% and +1.4%
2. **Disagreement list** -- 11 questions (3.1% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.00% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## The money question
- combining your data with 193 published measured upgrade cases: roughly **5%** chance this upgrade pays off, 13% chance it regresses

## Next steps
1. spend nothing on upgrading or verifying this round
2. set the next base-model release as the re-evaluation trigger; that evaluation costs ~30 GPU-minutes and zero new labels
3. re-evaluate early if your traffic shifts (new product lines, new phrasing)

## How much to trust this
- every number comes from measured runs on your own 360 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*