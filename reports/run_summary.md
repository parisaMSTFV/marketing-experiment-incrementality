# Reproducible run summary

This report was generated from a fully synthetic randomized experiment with seed
`42`.

## Experiment health

- 60,000 randomized customers
- 30,142 control and 29,858 treatment
- Sample ratio check p-value: 0.246
- Largest absolute standardized pre-treatment difference:
  0.012

## Incremental effect

- Control mean: 0.456 orders per customer
- Unadjusted effect: 0.031 orders per customer
  (6.9% relative lift)
- 95% confidence interval: [0.017, 0.045]
- CUPED effect: 0.032 orders per customer
- CUPED variance reduction: 12.4%

## Economics

- Estimated incremental orders: 955
- Incremental contribution before campaign cost:
  30,328
- Campaign cost: 30,587
- Net incremental profit: -259
- 95% net-profit interval: [-13,226,
  12,709]
- Incremental ROI: -0.8%
- Portfolio recommendation: **Redesign**
- Point break-even incentive cost at the base margin: 1.98 per treated order

The profit interval propagates uncertainty in the CUPED contribution effect while
treating observed campaign costs as fixed. The break-even scenario changes contribution
margin mechanically; it is not a probability model for future margins.

Profitable segment estimates: At Risk, Growing, New.
Segments significant after Holm adjustment: At Risk, Growing, New.

These figures validate the analysis workflow on simulated data. They are not evidence
of real campaign performance.
