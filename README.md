# Does Free Shipping Pay? · testing Peeba's growth hypotheses

Python companion to the Power BI report *Shipping Pays the Bills* (Peeba, a B2B wholesale marketplace connecting international brands with retailers in Taiwan: 400 orders, Jan – Jul 2023, TWD).
The dashboard found that contribution margin is 19% of GMV but only 0.6% without shipping, and ended with five hypotheses. This notebook tests them with statistics,
works out whether free shipping could pay for itself, and checks whether each idea could be A/B tested at Peeba's volume.

| Question | Method |
|---|---|
| How sure are the headline margins? | Bootstrap (5,000 resamples) confidence intervals |
| H4: is shipping a burden, would free shipping pay? | Spearman correlation, Fisher exact and Mann-Whitney tests on new-retailer reorders, break-even GMV by free-shipping threshold |
| Can it be A/B tested? | Power analysis (statsmodels): sample size and months needed for reorder-rate and order-value tests |
| H1: fee on 0% Direct orders | Fisher exact test, fee simulation across churn scenarios |
| Is the take rate really falling? | Permutation test, overall vs within Marketplace, mix shift |
| H2 / H3 / H5 | Fisher test on incentives; payment-fee simulation; bootstrap median, Spearman and Kruskal-Wallis on late payments |

## Headline results
* CM without shipping is 0.6% of GMV (95% CI −2.1% to +3.3%), with a 32% chance of being negative: shipping is the profit engine.
* Free shipping would need about 30× today's GMV to pay back, and there is no sign that shipping charges stop new retailers from reordering.
* A reorder-rate A/B test would need about 100 months at today's volume; an order-value test about 10 months.
* H1, H2, H3 and H5 are supported. The fall in take rate is mostly mix: Direct orders went from 26% to 47% of GMV.

## Run it
```bash
pip install -r requirements.txt
jupyter notebook "Free Shipping Deep Dive.ipynb"
```
Put the interview workbook (.xlsx with the Raw Data sheet) in the data folder. It is not included: the data belongs to the original interview project.
Every chart is saved to the images folder.

## Files
```
Free Shipping Deep Dive/
├── Free Shipping Deep Dive.ipynb   the analysis, with outputs
├── Free Shipping Deep Dive.html    the same notebook as a static page
├── peebatools.py                   unit economics (same rules as the Power BI model) and bootstrap helper
├── requirements.txt
├── data/                           interview workbook (not included)
├── images/                         key charts as PNG
└── powerbi/
    └── Shipping Pays the Bills Peeba.pbit   companion Power BI report
```
