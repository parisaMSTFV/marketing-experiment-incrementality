# Experiment analysis plan

This plan is fixed before the synthetic outcomes are analyzed. Its purpose is to
separate decisions made in advance from choices that could be influenced by results.

## Business decision

Decide whether to scale, redesign, or stop a customer marketing campaign. The
campaign sends an offer to the treatment group, while the control group remains
eligible for normal marketing activity but does not receive this offer.

## Design

| Item | Definition |
|---|---|
| Experimental unit | Customer |
| Assignment | Independent 50/50 treatment-control randomization |
| Pre-period | 28 days |
| Experiment period | 28 days |
| Estimand | Intent-to-treat effect among randomized customers |
| Primary metric | Orders per randomized customer during the experiment |
| Variance reduction | CUPED with pre-period orders |
| Confidence level | 95% |
| Planned power | 80% |

The intent-to-treat estimand preserves randomization: every assigned customer stays
in the assigned group whether or not they notice or use the offer.

## Health checks

1. Check sample ratio mismatch against the planned 50/50 allocation.
2. Compare pre-treatment behavior using standardized mean differences.
3. Confirm that outcome and cost fields are complete and logically valid.

An SRM p-value below 0.05 stops causal interpretation until the assignment or data
pipeline is investigated. Balance checks are diagnostics; they are not used to
re-randomize or selectively remove customers after outcomes are known.

## Metrics

- Primary: orders per customer.
- Secondary: purchase conversion, revenue, and contribution before campaign cost.
- Decision metrics: incremental orders, campaign cost, net incremental profit,
  incremental ROI, and cost per incremental order.

The economic decision uses total campaign cost for the treatment group, including
contact cost and incentive cost paid on all treatment-group orders. This captures
subsidy leakage to customers who would have purchased without the campaign.

## Versioned economic decision rule

The implemented `economic-rule-v1` applies one mechanical decision after the required
SRM check passes. Pre-treatment balance remains a diagnostic rather than a gate:

| Output | Fixed condition |
|---|---|
| Scale | The 95% lower bounds for both the order effect and net incremental profit are positive |
| Redesign | The order-effect lower bound is positive, but the net-profit interval includes zero |
| Stop | The order-effect lower bound is not positive, or the net-profit upper bound is not positive |

If experiment health checks fail, the output is Stop pending investigation. This rule
was added after the repository's original synthetic demonstration already existed. It is
fixed in code for this revision and future runs, but is not presented as preregistration
of the original seed-42 result.

The net-profit interval propagates the CUPED confidence interval for incremental
contribution and treats observed contact and incentive costs as fixed. It therefore does
not capture uncertainty in future unit costs, returns, or cost reconciliation.

## Break-even scenarios

The fixed contribution-margin multipliers are 0.80, 0.90, 1.00, 1.10, and 1.20.
For each multiplier, the pipeline calculates the incentive cost per treated-group order
that would make point net incremental profit equal zero. The same transformation is
applied to the contribution-effect confidence bounds. These are deterministic stress
scenarios, not estimated probabilities or forecasts.

## Estimation

The unadjusted estimate is the treatment mean minus the control mean. CUPED subtracts
a control-fitted multiple of the centered pre-period covariate from the outcome:

```text
adjusted outcome = outcome - theta × (pre-period metric - pooled pre-period mean)
```

Both estimates report an unpooled standard error, a two-sided p-value, and a 95%
confidence interval. CUPED is used for precision, not to repair broken randomization.

## Segment analysis

The following segments are defined before outcome analysis:

- New
- Growing
- Loyal
- At Risk

Segment effects use CUPED and Holm-adjusted p-values across the four comparisons.
They remain secondary analyses. A segment that looks promising should be confirmed
in a new randomized test with the targeting rule registered in advance.

## Power

The minimum detectable effect uses a two-sided normal approximation at 5%
significance and 80% power. The project reports MDE curves for both the raw outcome
variance and the CUPED-adjusted variance. In this case study the curve uses variance
from the completed synthetic run to plan a follow-up test. A real pre-launch plan
would use historical or pilot variance instead of future outcomes.

## Causal assumptions and limitations

- Assignment is random and recorded correctly.
- One customer's treatment does not materially change another customer's outcome.
- No experiment-related outcomes are missing differentially by group.
- The experiment period and cost rules are specified before analysis.
- The synthetic generator is simpler than a production marketplace and does not
  validate any expected real-world effect size.
