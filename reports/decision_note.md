# Campaign decision note

## Decision

**Redesign economics.**

The randomized comparison estimates 0.032 incremental
orders per treated customer, with a 95% confidence interval from
0.019 to 0.045. The campaign therefore changes
behavior in the synthetic experiment.

At the current contact and incentive costs, estimated net incremental profit is
-259. The main issue is subsidy leakage:
the incentive is paid on treatment-group orders that would have happened without
the campaign as well.

## Recommended next test

- Exclude or reduce spend on: Loyal.
- Re-test the offer in: At Risk, Growing, New.
- Keep the randomized holdout and the same primary metric.
- Pre-register any new targeting rule before reading the next experiment outcome.
- Treat segment findings as decision inputs, not proof of permanent causal differences.

All values in this note come from synthetic data and exist only to demonstrate the
decision workflow.
