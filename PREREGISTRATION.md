# PRE-REGISTRATION

Written and committed **before any closing line value (CLV) or profit and loss (P&L) figure was
computed** on any data. The git commit timestamp of this file is the proof. Nothing here may be
changed after data has been seen (CLAUDE.md s2, s4). Any later addition goes in a new, dated section
below and applies only to data recorded after that commit.

## Hypothesis (from CLAUDE.md s1, unchanged)

Bets taken when the back price is at least 3% above the margin-free sharp reference price beat the
margin-free sharp closing price by an average of at least 2%, after 2% commission.

## Definitions (CLAUDE.md s6, unchanged)

- Margin removal: power method over the three 1X2 prices of one bookmaker snapshot. The proportional
  method is a robustness check only. It must agree in sign with the power method and be within 1 percentage
  point; otherwise this is flagged in the report. It is never used for the verdict.
- `edge = back / fair_t − 1`; a flag needs `edge ≥ 0.03`.
- `eff = 1 + (back − 1) × 0.98`; `CLV = eff / fair_close − 1`.
- One bet per (event, selection): the first qualifying flag only.
- Confidence intervals: cluster bootstrap by event, 10,000 resamples, seed 20261027, two-sided 95%
  percentile interval.
- One-sided p-value for mean CLV > 0: centred cluster bootstrap,
  `p = (1 + #{b: mean*_b − mean ≥ mean}) / (1 + B)`.
- Bonferroni: the bar is `p < 0.05 / N`, where N is the number of distinct variant ids in
  `variants.csv` at the time of the run (the running variant included).

## Phase 1: historical check on football-data.co.uk

### Data and the forced change to the holdout split

The field coverage table (`results/coverage.csv`, made before this file) shows:

- Pinnacle pre-closing and closing prices: ~95–100% of matches in every season 2012-13 to 2024-25, but
  only ~24–49% of matches in 2025-26.
- **Betfair Exchange prices (BFEH/BFED/BFEA and closing BFECH/…): absent before 2024-25.** Present
  for ~97–100% of matches in 2024-25 and ~90–95% in 2025-26.

The usable window (both sharp and exchange prices) is therefore **2024-25 and 2025-26 only**. CLAUDE.md
s8 names exactly these two seasons as the sealed holdout, which would leave no development data. The
most conservative workable split, chosen before any CLV was computed, is:

- **Development: 2024-25.**
- **Sealed holdout: 2025-26** (the most recent complete season). Its Pinnacle coverage is partial, so
  the holdout will be smaller than the development set.
- The 2026-27 season is in progress and excluded.

Only field coverage and row counts were computed on the 2025-26 files before sealing. No prices were
compared and nothing about results was looked at.

### Leagues (fixed)

E1 England Championship, E2 League One, E3 League Two, EC National League, SC1 Scotland Championship,
SC2 Scotland League One, SC3 Scotland League Two, D2 Germany 2. Bundesliga, I2 Italy Serie B,
SP2 Spain Segunda, F2 France Ligue 2. All eleven have full coverage in the window.

### Test (fixed)

- For each match outcome: flag when the Betfair Exchange pre-closing price (BFE*) is ≥ 3% above the
  power-method margin-free Pinnacle pre-closing price (PS*). Both come from the same Friday/Tuesday
  afternoon snapshot, so there is no lookahead. The code enforces this: the decision function refuses any
  column not in `mvt.fd.DECISION_COLS`, and a test checks that scrambling closing prices and results
  does not change the flags.
- CLV is measured against the power-method margin-free Pinnacle closing price (PSC*), after 2% commission.
- BFE prices are treated as gross back prices, and the 2% Matchbook commission is applied to them.
- Exclusions (each counted and reported): missing or invalid Pinnacle pre-closing prices; Pinnacle
  pre-closing or closing overround outside [1.00, 1.12] (data error); missing Betfair pre-closing price for
  the selection; missing date; missing Pinnacle closing prices; missing result.
- Flags with edge > 20% stay in, because a data error cannot be proven from these files. They are counted,
  and the mean without them is also reported.
- **Pass rule** (used for the placebo machinery and reported for real data): mean CLV ≥ +0.02 **and**
  one-sided p < α (α = 0.05 for placebo; 0.05 / N for real data).
- **Spending recommendation rule (CLAUDE.md s8):** recommend paid phases only if **both** the development
  and the holdout mean CLV are above 0. Otherwise recommend stopping.
- Reported for both scopes: number of flags; mean CLV with CI and p; placebo comparison; tables by
  season, league and calendar month; first half versus second half of the period (split at the median flag
  date, because there is only one development season); the monthly trend slope; mean CLV without the best
  league; proportional-method robustness; secondary CLV against the Betfair closing price; flat-stake P&L
  (noisy, secondary).

### Placebo (fixed, run before the real test)

- Each placebo set has the same number of records as the development flags. For each flag, one eligible
  record is drawn at random from the same stratum (league × Betfair price band
  [1, 1.5, 2, 3, 5, 10, ∞) × time-to-start proxy). The time-to-start proxy is the number of days from the
  collection day (Fri for Fri–Mon games, Tue for Tue–Thu) to the match day, because football-data gives no
  collection timestamp.
- Whole records are drawn: price, closing price and result move together. Nothing is shuffled separately.
- 200 sets, seed 7301, nominal α = 0.05. Calibration passes only if the pass rate is ≤ 10% (a) for the
  sets as written and (b) for the same sets with the eligible pool's mean CLV subtracted. Check (b)
  makes the true mean exactly zero, so it also tests the p-value itself. If either fails, the machinery
  is broken: stop and find the bug.

### Sealed holdout files (SHA-256)

| file | sha256 | rows |
|---|---|---|
| sealed/2526_D2.csv | 8bfb275286d7d620c20c7fdb164e4447e114be3de94b8372b7ac3773d71581ef | 306 |
| sealed/2526_E1.csv | 98954c319950f19158624b17a154ef1c56eb7b8d169ef317f28f06d11d0b9a74 | 552 |
| sealed/2526_E2.csv | 4c96eff8a2f20c5e26015af8609c4f90478ff055f58ab6e137cc3445bf4c67ee | 552 |
| sealed/2526_E3.csv | eff4fa15cb18857091d1f0666d0b8a6c61eda7a8374feef8f2d8a38244e0e45d | 552 |
| sealed/2526_EC.csv | 2372229d616a57f9df3d9a401cd942df8e1909ba67017b3793c6aceaf0becf76 | 552 |
| sealed/2526_F2.csv | dcedf4dd66f3e0ac8efb8ccd2e5489882068e5630c041702b15c1d0fe70c6017 | 306 |
| sealed/2526_I2.csv | ed4bcece92bb8b09aa94768bc77d3529fa29339ec70fa7867a9fbc3ca0954731 | 380 |
| sealed/2526_SC1.csv | 75302af065eee1c5c0c7ac3a44054aec4860d3bddcf9b358c4dc9f295058332c | 180 |
| sealed/2526_SC2.csv | 57cc448f55cb427f11f1123fcd551dff3d47a7a73de5a0c147982e15cf15625e | 180 |
| sealed/2526_SC3.csv | 06cc5655e2f72c2e6a9bf4520c1fd82ee9ff5e722cdb3d23293d7980e2173959 | 180 |
| sealed/2526_SP2.csv | 4986060e5c1d55626aef24c4bbeaaea2278b27a0b7696927405705aaa57405de | 462 |

The code refuses to read `data/sealed/` until `python -m mvt.unseal` has run once. That step requires
`results/phase1_dev.json` to be committed and checks these hashes.

Machine-readable settings: `config/phase1.json`.

## Phases 2–4: live recording rules (fixed now, before any recording)

These repeat CLAUDE.md s9 and add the details it leaves open. They are fixed before any live data exists.

- Target leagues (those covered by both Matchbook and the recommended feed, The Odds API): England
  Championship, League One, League Two; Germany 2. Bundesliga; Italy Serie B; Spain Segunda; France
  Ligue 2. Market: full-time match odds (1X2) only.
- Reference: Pinnacle, h2h market, from the feed's `eu` region. `fair_t` uses the power method on the
  most recent Pinnacle snapshot received before t.
- **Flag rules:** `edge_t ≥ 0.03`; at least £20 available at the flagged Matchbook best back price;
  reference snapshot no more than 120 s old at t, by both our receive time and the feed's market
  `last_update`; Matchbook and reference snapshots within 60 s of each other (receive times); t at least
  5 minutes before scheduled start; market not in-play and not suspended.
- `fair_close` = power-method fair price from the last Pinnacle snapshot received before the Matchbook
  market's in-play flag first turns true. If that snapshot is more than 10 minutes before the in-play
  time, the flag is excluded and the exclusion counted.
- Persistence: re-poll the flagged market at +30 s and +60 s. "Persisted" means the best back is at the
  same or a better price with ≥ £20 available.
- Event matching: kick-off within 15 minutes and both team names matched (normalised names plus a
  hand-checked alias table). Unmatched events are logged. Flags with edge > 20% are checked for mapping
  errors and excluded only if an error is proven. Voided or postponed events are excluded and counted.
- Pilot (1 week): counts only, no CLV. Early stop if fewer than 10 qualifying flags, confirmed by one
  more week.
- Confirmation: code and config frozen at a recorded commit. Run ≥ 6 weeks **and** ≥ 300 flags, with a
  maximum of 10 weeks. Single interim look at week 4, for futility only: stop with NO EDGE if the upper 95%
  bound on mean CLV is below 0.
- Pass (CONFIRMED) needs all six gates in CLAUDE.md s9 Phase 5, exactly as written there.
