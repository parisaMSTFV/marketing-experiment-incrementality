# Interview guide

## What business problem does this project solve?

It separates campaign-attributed activity from activity caused by the campaign.
The randomized control group estimates what would have happened without the offer.
The project then compares incremental contribution with the full cost of contacting
and subsidizing the treatment group.

## Why is before-after comparison insufficient?

Both groups face the same market-wide change. If demand rises during the experiment,
the treatment group's orders may increase even when the campaign has no effect.
The concurrent control group removes that shared movement.

## Why use orders per randomized customer?

It preserves the intent-to-treat design, includes zero-order customers, and maps
directly to incremental order volume. Conversion is also reported, but it ignores
additional orders from repeat purchasers.

## What does CUPED do?

CUPED uses a correlated pre-period metric to remove predictable customer-level
variation from the outcome. It can narrow confidence intervals without changing
the randomized estimand. It cannot fix missing data, assignment errors, or an
invalid control group.

## Why can a statistically positive campaign lose money?

The incentive is paid on treatment-group orders, including orders that would have
happened without treatment. If the margin from incremental orders is smaller than
contact cost plus this subsidy leakage, the campaign destroys value despite
increasing orders.

## How should segment results be used?

They guide the next pre-registered experiment. Four segment comparisons create
multiple-testing risk, so the project reports Holm-adjusted p-values and avoids
claiming that a single synthetic run proves stable heterogeneous effects.

## What would change in production?

Production analysis would add assignment and exposure logs, bot and employee
exclusions defined before launch, missing-event monitoring, delayed conversion
windows, interference checks, cost data reconciliation, novelty-effect monitoring,
and a pre-launch sample-size calculation based on historical variance.
