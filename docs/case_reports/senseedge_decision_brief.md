# Upgrade decision brief: senseedge -> Qwen2.5-1.5B-Instruct

**Spend a little to settle it, then decide.** The current data cannot settle the question. The two systems gave different answers on only 10 real questions -- have a domain expert mark those right/wrong (about an hour of work) and the answer becomes definitive. Stay put meanwhile.

## Where you stand
- current system: about **3.2** wrong per 100 requests
- retrained on the new model (actually trained and measured, not estimated): about **2.8** wrong per 100
- the new model used bare, with no training: about **20.2** wrong per 100 -- your training data is the moat

## What we checked
1. **Quality, head-to-head** -- head-to-head on 400 real business questions: the new system fixed 6 and broke 4; everything else identical. Today you get ~3.2 wrong per 100 requests; retrained on the new model, ~2.8. Allowing for sampling error, the true gap is between -1.3% and +2.3%
2. **Disagreement list** -- 10 questions (2.5% of the set) where the two systems answer differently -- the only items that carry decision information; exported for labeling
3. **Confidence quality** -- the current system's confidence quality holds up (relevant if you route low-confidence cases to humans; not statistically significant here)
4. **Noise tolerance** -- re-tested with typos, casing noise and filler words injected: gap of +0.00% -- no extra robustness from the newer model
5. **Transfer safety** -- model lineage checked: this path does NOT permit moving your existing work as-is (measured: cross-generation transfer can score worse than no system at all) -- any upgrade means retraining

## Next steps
1. hand the exported disagreement list to a domain expert to mark right/wrong (labeling 25 more gives a 27% chance of a definitive answer)
2. re-run this tool after labeling; the verdict will harden into a definite upgrade / stay-put call
3. change nothing in production meanwhile (zero risk)

## How much to trust this
- every number comes from measured runs on your own 400 real business records; nothing is estimated or demo data
- method and thresholds follow the published UpgradeBench (2026) benchmark: 33 replayed upgrade decisions, 0.37% mean decision loss, zero serving regressions
- when the evidence is insufficient, this tool says so and prices the cheapest way to settle it, rather than forcing a verdict

---
*Technical appendix (full statistics, for the engineering team): recommendation.md*