# Campaign decision note

## Decision

**Redesign.**

The randomized comparison estimates 0.032 incremental
orders per treated customer, with a 95% confidence interval from
0.019 to 0.045. The campaign therefore changes
behavior in the synthetic experiment.

At the current contact and incentive costs, estimated net incremental profit is
-259, with a 95% interval from
-13,226 to 12,709.
The interval includes zero, so the fixed rule does not support scale. The main issue is
subsidy leakage: the incentive is paid on treatment-group orders that would have happened
without the campaign as well.

## Fixed economic decision rule

The versioned `economic-rule-v1` rule produces exactly one output:

| Output | Condition after experiment health checks pass |
|---|---|
| Scale | Order-effect lower bound > 0 and net-profit lower bound > 0 |
| Redesign | Order-effect lower bound > 0 and the net-profit interval includes zero |
| Stop | Order-effect lower bound <= 0 or net-profit upper bound <= 0 |

Current rule reason: The order effect is positive, but the profit interval includes zero.

## Break-even evidence

At the base contribution margin, the point break-even incentive cost is
1.98 per treated order,
compared with the current cost of
2.00. The 95% contribution-
effect interval maps to a break-even range from
1.09 to
2.87.

Observed contact and incentive costs are treated as fixed in the interval. The margin
multipliers in `economic_break_even.csv` are deterministic stress scenarios, not forecasts.

## Recommended next test

- Exclude or reduce spend on: Loyal.
- Re-test the offer in: At Risk, Growing, New.
- Keep the randomized holdout and the same primary metric.
- Pre-register any new targeting rule before reading the next experiment outcome.
- Treat segment findings as decision inputs, not proof of permanent causal differences.

All values in this note come from synthetic data and exist only to demonstrate the
decision workflow.
