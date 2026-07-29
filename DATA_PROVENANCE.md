# Data provenance

No external, company, customer, or campaign data is used.

`src/marketing_incrementality/simulate.py` creates the full customer-level dataset
from a documented random seed. The generator assigns four synthetic lifecycle
segments, pre-period behavior, random treatment, experiment-period behavior, and
financial outcomes.

The simulation intentionally includes:

- a market-wide increase between the pre-period and experiment period;
- customer-level purchasing propensity shared across both periods;
- different treatment responses by pre-specified segment;
- campaign cost paid on treatment-group activity.

These mechanisms make it possible to demonstrate before-after bias, randomized
incrementality, CUPED, heterogeneous effects, and subsidy leakage without exposing
real information.

Generated customer-level files are ignored by Git. Aggregate tables, metrics, and
figures are committed so the published claims can be audited and reproduced.
