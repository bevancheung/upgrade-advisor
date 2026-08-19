# -*- coding: utf-8 -*-
"""The validated upgrade decision policy (UpgradeBench §6, Table 6).

Pure python, no GPU. Inputs are measurements; output is an Action with the
evidence chain attached. Margins and gate structure follow the paper's
prospectively specified settings: epsilon = 1pp for classification, 2pp for
structured generation; copy is gated on documented short-distance
continuation plus a regression gate; every gate reads a validation (gate)
set that is disjoint from the reporting set.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

EPS_CLASSIFICATION = 0.01
EPS_STRUCTURED = 0.02

# Continuation distance above which copying is not licensed. The paper
# measured retention 0.88-0.99 at 46B tokens and ~0 at 2.9T; the boundary
# between those endpoints is unmeasured, so the default is conservative.
COPY_MAX_CONTINUATION_TOKENS = 100e9


class Action(str, Enum):
    FREEZE = "freeze"
    COPY = "copy"
    REFRESH = "refresh"
    RETRAIN = "retrain"
    INCONCLUSIVE = "inconclusive"   # legacy label; unresolved now maps to
    COLLECT = "collect"             # ...label the disagreement set (cheap
    #                                 evidence with a priced convergence plan)
    WAIT = "wait"                   # ...posterior says the gain is unlikely
    #                                 to clear epsilon; hold until the next
    #                                 release rather than spend on evidence


# Relative-error-reduction gate (theory-review fix #1): near the accuracy
# ceiling, absolute pp compress real gains; a reference that removes >=30%
# of the frozen specialist's errors (with enough error mass to be meaningful)
# also opens the upgrade waterfall.
RER_THRESHOLD = 0.30
RER_MIN_ERRORS = 10
# Fewer frozen errors than this on the gate set means the eval itself no
# longer discriminates (fix #3).
SATURATION_MIN_ERRORS = 20


@dataclass
class Measurements:
    """Everything the policy may consult. Scores in [0,1] on the GATE set.

    Required: freeze_score, adopt_floor. The rest unlock branches:
    reference_score (measured or beta-estimated), copy_score, refresh_score.
    """
    task_kind: str                      # "classification" | "structured"
    freeze_score: float                 # current specialist, gate set
    adopt_floor: float                  # target base zero/few-shot, gate set
    reference_score: Optional[float] = None
    reference_is_estimate: bool = False  # True if beta-projected, not trained
    copy_score: Optional[float] = None
    copy_negative_flip_rate: Optional[float] = None
    refresh_score: Optional[float] = None
    refresh_negative_flip_rate: Optional[float] = None
    inputs_retained: bool = False
    gold_labels_retained: bool = False
    gate_set_size: int = 0
    # genealogy verdict for the (source, target) pair
    shape_compatible: bool = False
    documented_continuation: bool = False
    continuation_tokens: Optional[float] = None
    # power layer (fix #2): freeze-vs-reference disagreement rate on the
    # gate set, when the reference is measured (None for estimates)
    discordant_rate: Optional[float] = None
    # pooled paired evidence (review-2 fix: pool every paired record --
    # val and test -- instead of judging on one fragment): n common items,
    # n01 = frozen wrong & reference right, n10 = frozen right & ref wrong
    paired_n: int = 0
    paired_n01: int = 0
    paired_n10: int = 0
    paired_freeze_errors: int = 0   # frozen-specialist errors on the pool
    # empirical-Bayes layer (review-2): prior over the true gain from the
    # UpgradeBench corpus (per edge kind), and the seed-to-seed training
    # variance folded into the observation noise
    prior_mu: Optional[float] = None       # accuracy scale (0.008 = 0.8pp)
    prior_sd: Optional[float] = None
    sigma_seed: float = 0.0
    # decision-relevant epsilon from volume/costs (falls back to task eps)
    economic_epsilon: Optional[float] = None


@dataclass
class Recommendation:
    action: Action
    epsilon: float
    # epistemic verdict, separated from the operational action (review-2):
    # what the evidence establishes vs what to do about it
    verdict: str = ""   # gain-established | equivalence | unresolved |
    #                     no-reference
    reasons: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    evidence: dict = field(default_factory=dict)


def _eps(task_kind: str) -> float:
    return EPS_CLASSIFICATION if task_kind == "classification" else EPS_STRUCTURED


def recommend(m: Measurements, flip_budget: Optional[float] = None) -> Recommendation:
    eps = _eps(m.task_kind)
    r = Recommendation(action=Action.FREEZE, epsilon=eps)
    r.evidence = {
        "freeze_score": m.freeze_score,
        "adopt_floor": m.adopt_floor,
        "reference_score": m.reference_score,
        "gate_set_size": m.gate_set_size,
    }
    if m.gate_set_size and m.gate_set_size < 500:
        r.warnings.append(
            f"gate set has only {m.gate_set_size} items; gate sampling error "
            "at this size caused the worst episode in the paper's replay -- "
            "treat marginal verdicts as ties")

    # ---- Step 1: opportunity gate ----------------------------------------
    if m.reference_score is None:
        r.verdict = "no-reference"
        r.reasons.append(
            "no reference score (measured or beta-estimated); without an "
            "upgrade-opportunity estimate the default is FREEZE, revisit "
            "after logging one more release")
        return r
    # Pooled paired evidence takes precedence over the gate-fragment point
    # estimate: the decision uses every paired record the episode holds.
    have_pairs = m.paired_n > 0 and not m.reference_is_estimate
    if have_pairs:
        from . import stats as _S
        n, n01, n10 = m.paired_n, m.paired_n01, m.paired_n10
        gain = (n01 - n10) / n
        lo, hi = _S.paired_gain_ci(n, n01, n10)
        r.evidence["paired_evidence"] = {
            "n": n, "reference_fixes": n01, "reference_breaks": n10}
        r.evidence["opportunity_ci_pooled_pp"] = [round(lo * 100, 2),
                                                  round(hi * 100, 2)]
        r.evidence["excluded_gain_above_pp"] = round(hi * 100, 2)
    else:
        gain = m.reference_score - m.freeze_score
        lo = hi = None
    r.evidence["opportunity_pp"] = round(gain * 100, 2)

    # ---- error-scale view (fix #1), pooled when possible ----
    if have_pairs:
        freeze_errors = max(m.paired_freeze_errors, n01)
        err_f = freeze_errors / n
        err_r = (freeze_errors - n01 + n10) / n
    else:
        err_f = 1.0 - m.freeze_score
        err_r = 1.0 - m.reference_score
        freeze_errors = (round(err_f * m.gate_set_size)
                         if m.gate_set_size else None)
    rer = (err_f - err_r) / err_f if err_f > 1e-12 else None
    if rer is not None:
        r.evidence["opportunity_rer"] = round(rer, 3)
    if freeze_errors is not None:
        r.evidence["freeze_errors_on_gate"] = freeze_errors

    # ---- saturation flag (fix #3) ----
    saturated = (freeze_errors is not None
                 and freeze_errors < SATURATION_MIN_ERRORS)
    if saturated:
        r.warnings.append(
            f"EVAL-SATURATED: the frozen specialist makes only "
            f"{freeze_errors} error(s) on the pooled evidence -- any "
            "upgrade comparison rests on that many items. Harvest hard/tail "
            "examples (e.g. production misroutes) before trusting an "
            "upgrade verdict here")

    # ---- error-scale gate (fix #1): now requires the direction to be
    # statistically established on the discordant set, not just a large
    # relative reduction over a handful of errors ----
    rer_opens = (rer is not None and rer >= RER_THRESHOLD and gain > 0
                 and freeze_errors is not None
                 and freeze_errors >= RER_MIN_ERRORS
                 and (not have_pairs or _S.sign_test_p(n01, n10) < 0.05))

    if have_pairs:
        # ---- three-zone equivalence verdict (TOST) on the observed CI:
        # post-hoc MDE was the wrong instrument -- the data's own interval
        # already says what is established, excluded, or unresolved ----
        if lo > eps:
            r.verdict = "gain-established"
            r.reasons.append(
                f"upgrade opportunity established: the pooled paired CI "
                f"[{lo*100:+.1f}, {hi*100:+.1f}]pp lies entirely above "
                f"epsilon ({eps*100:.0f}pp) on n={n} paired records "
                f"({n01} fixes vs {n10} breaks)")
        elif rer_opens:
            r.verdict = "gain-established"
            r.reasons.append(
                f"absolute gain {gain*100:.2f}pp does not clear epsilon on "
                f"its own, but the reference removes {rer:.0%} of the "
                f"frozen specialist's errors ({freeze_errors} errors, "
                f"{n01} fixes vs {n10} breaks, direction established by "
                "exact sign test) -- near the accuracy ceiling the "
                "error-rate scale is the decision-relevant one "
                "(bounded-metric compression), so the upgrade waterfall "
                "opens")
        elif hi < eps:
            r.verdict = "equivalence"
            r.reasons.append(
                f"equivalence established, FREEZE is a verdict not a "
                f"default: the pooled paired CI [{lo*100:+.1f}, "
                f"{hi*100:+.1f}]pp excludes any gain above epsilon "
                f"({eps*100:.0f}pp) -- n={n} paired records, "
                f"{n01} fixes vs {n10} breaks"
                + (" (the two systems agree on every pooled item)"
                   if n01 + n10 == 0 else ""))
            return r
        else:
            pi = (n01 + n10) / n
            n_req = _S.required_n(pi, eps) if pi > 0 else None
            leaning = ("lean-freeze" if gain <= eps / 2 else "lean-upgrade")
            r.verdict = "unresolved"
            r.evidence["leaning"] = leaning
            eps_dec = m.economic_epsilon or eps
            r.evidence["decision_epsilon_pp"] = round(eps_dec * 100, 3)
            post = None
            if m.prior_mu is not None and m.prior_sd:
                pm, ps = _S.posterior_gain(n, n01, n10, m.prior_mu,
                                           m.prior_sd, m.sigma_seed)
                post = _S.gain_probabilities(pm, ps, eps_dec)
                r.evidence["posterior"] = {
                    "post_mu_pp": round(pm * 100, 2),
                    "post_sd_pp": round(ps * 100, 2), **post}
            base_msg = (
                f"the pooled evidence cannot resolve epsilon: CI "
                f"[{lo*100:+.1f}, {hi*100:+.1f}]pp straddles "
                f"{eps*100:.0f}pp (n={n}, {n01} fixes vs {n10} breaks; "
                f"gains above {hi*100:.1f}pp are already excluded; "
                f"leaning: {leaning})")
            if post and post["p_gain_above_eps"] < 0.10:
                r.action = Action.WAIT
                r.reasons.append(
                    base_msg + f". Under the UpgradeBench corpus prior the "
                    f"posterior gives the gain a "
                    f"{post['p_gain_above_eps']:.0%} chance of clearing the "
                    f"decision epsilon ({eps_dec*100:.2f}pp) -- more "
                    "evidence is unlikely to change the call, so hold the "
                    "frozen specialist and revisit at the next release")
                return r
            r.action = Action.COLLECT
            r.reasons.append(
                base_msg
                + (f"; posterior chance the gain clears the decision "
                   f"epsilon: {post['p_gain_above_eps']:.0%}"
                   if post else "")
                + ". Cheapest resolution: label the disagreement set "
                "(`upgrade-advisor probe-disagree` writes it with a priced "
                "convergence plan)"
                + (f"; resolving by i.i.d. sampling would need roughly "
                   f"n={n_req}" if n_req else "")
                + ". Keep serving the frozen specialist while collecting")
            return r
    else:
        if rer_opens and gain <= eps + 1e-9:
            r.verdict = "gain-established"
            r.reasons.append(
                f"absolute gain {gain*100:.2f}pp is within epsilon, but "
                f"the reference removes {rer:.0%} of the frozen "
                f"specialist's errors ({freeze_errors} errors) -- near the "
                "accuracy ceiling the error-rate scale is the "
                "decision-relevant one (bounded-metric compression), so "
                "the upgrade waterfall opens")
        if gain <= eps + 1e-9 and not rer_opens:
            r.verdict = "point-only"
            r.reasons.append(
                f"retraining reference beats the frozen specialist by "
                f"{gain*100:.2f}pp <= epsilon ({eps*100:.0f}pp)"
                + (f" with relative error reduction {rer:.0%} below the "
                   f"{RER_THRESHOLD:.0%} gate" if rer is not None else "")
                + ": upgrading buys nothing measurable on this task")
            if m.reference_is_estimate:
                r.warnings.append(
                    "reference was beta-estimated, not trained; log the "
                    "trained reference when convenient")
            return r
    if not r.verdict:
        r.verdict = "gain-established"
    # From here the waterfall is open. With pooled pairs that means either
    # lo > eps (gain established) or the RER gate passed its sign test --
    # a point estimate above epsilon with a straddling CI does NOT open it
    # (symmetric standard; the old asymmetry let a 2-item flip decide a
    # RETRAIN).

    # ---- Step 2: copy gate (genealogy + distance + regression) -----------
    if m.shape_compatible and m.copy_score is not None:
        licensed = (m.documented_continuation
                    and m.continuation_tokens is not None
                    and m.continuation_tokens <= COPY_MAX_CONTINUATION_TOKENS)
        passes_quality = m.copy_score >= m.reference_score - eps
        passes_flips = (flip_budget is None
                        or m.copy_negative_flip_rate is None
                        or m.copy_negative_flip_rate <= flip_budget)
        r.evidence["copy_score"] = m.copy_score
        r.evidence["copy_licensed_by_genealogy"] = licensed
        if licensed and passes_quality and passes_flips:
            r.action = Action.COPY
            r.reasons.append(
                "target is a documented short continuation "
                f"({m.continuation_tokens/1e9:.0f}B tokens) of the source "
                "weights and the copied adapter passes the quality and "
                "flip gates: copying is near-free here")
            return r
        if not licensed:
            r.reasons.append(
                "copy not licensed: shape compatibility alone does not "
                "license copying (independent-run copies collapsed below "
                "the no-adapter floor in the paper); requires documented "
                f"continuation <= {COPY_MAX_CONTINUATION_TOKENS/1e9:.0f}B tokens")
        elif not passes_quality:
            r.reasons.append(
                f"copy fails the quality gate ({m.copy_score:.4f} vs "
                f"reference {m.reference_score:.4f} - eps)")
        else:
            r.reasons.append(
                f"copy fails the flip gate (NFR {m.copy_negative_flip_rate:.2%} "
                f"> budget {flip_budget:.2%})")

    # ---- Step 3: refresh (annotation-free, input-retaining) --------------
    if m.inputs_retained and m.refresh_score is not None:
        passes_quality = m.refresh_score >= m.reference_score - eps
        passes_flips = (flip_budget is None
                        or m.refresh_negative_flip_rate is None
                        or m.refresh_negative_flip_rate <= flip_budget)
        r.evidence["refresh_score"] = m.refresh_score
        if passes_quality and passes_flips:
            r.action = Action.REFRESH
            r.reasons.append(
                "refresh student passes the gates; saves gold annotation "
                "(paper: retention 0.96-1.05 vs gold retraining). Note: if "
                "you still hold the original gold labels, plain retraining "
                "dominates refresh on compute")
            if m.gold_labels_retained:
                r.warnings.append(
                    "gold labels are retained -- RETRAIN costs less compute "
                    "than teacher-relabel refresh; refresh chosen only if "
                    "annotation-freshness matters to you")
            return r
        r.reasons.append("refresh measured but fails a gate")
    elif m.inputs_retained and m.refresh_score is None:
        r.reasons.append(
            "inputs are retained but no refresh student was trained/measured; "
            "RETRAIN recommended now, or run `upgrade-advisor refresh` first")

    # ---- Step 4: retrain --------------------------------------------------
    r.action = Action.RETRAIN
    r.reasons.append(
        f"upgrade opportunity is {gain*100:.2f}pp > epsilon and no cheaper "
        "path passed its gates: retrain on gold labels with the fixed recipe")
    if m.task_kind == "structured":
        r.warnings.append(
            "structured tasks showed no benefit from small label budgets in "
            "the paper (256 labels bought nothing on text-to-SQL; 95% of the "
            "gain needed >4096) -- budget labels accordingly")
    return r
