# Big-O growth datasets (formula-derived)

These CSVs are **not invented pedagogical metaphors**. They tabulate idealized operation
counts for standard asymptotic classes with leading coefficient **c = 1**, matching the
assumption stated on Wikimedia Commons
[`Comparison_computational_complexity.svg`](https://commons.wikimedia.org/wiki/File:Comparison_computational_complexity.svg)
(author Cmglee, CC BY-SA 4.0): "assuming a coefficient of 1".

Formulas:
- O(1) = 1
- O(log n) = log2(n)
- O(n) = n
- O(n log n) = n * log2(n)
- O(n²) = n²
- O(2ⁿ) = 2ⁿ (capped where noted)
- O(n!) = n! (capped where noted)

Files:
- `growth_ops_c1_n1_64.csv` — dense n=1..64
- `growth_ops_cheatsheet_sizes.csv` — common teaching sizes

Do not treat overflow/inf rows as measured runtime.
