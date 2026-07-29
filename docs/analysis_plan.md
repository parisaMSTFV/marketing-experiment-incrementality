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
