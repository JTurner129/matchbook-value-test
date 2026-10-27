# PROGRESS (working log)

A fresh session can resume from this file alone. Standing instructions: CLAUDE.md.

## Where we are

- Phase 0a, 0b and Phase 1: **done**. The holdout has been unsealed once and analysed. No more Phase 1 runs.
- **Status: BLOCKED.** The owner has been asked once (REPORT.md "Owner action needed"). Wait for the reply.
- Next: see "Next steps" at the bottom.

## Log

### 2026-10-27

**Setup.** The repository was empty. I added CLAUDE.md (from the owner's upload), the code
skeleton (`mvt/`), tests and `.gitignore`. Raw data is kept out of git; `data/MANIFEST.csv` is committed.

**football-data.co.uk notes file** (https://www.football-data.co.uk/notes.txt, fetched 2026-10-27).
Relevant lines, quoted:
- "PSH and PH = Pinnacle home win odds", "PSD and PD = Pinnacle draw odds", "PSA and PA = Pinnacle away win odds"
- "BFEH = Betfair Exchange home win odds", "BFED = Betfair Exchange draw odds", "BFEA = Betfair Exchange away win odds"
- "These are for pre-closing odds. For the closing odds, as below but with an additional "C" character
  following the bookmaker abbreviation/Max/Avg (e.g. B365CH = closing Bet365 home win odds)."
- "Betting odds for weekend games are collected Friday afternoons, and on Tuesday afternoons for midweek games."

So: PSH/PSD/PSA and BFEH/BFED/BFEA are the same pre-closing snapshot (Friday or Tuesday afternoon).
PSCH/… and BFECH/… are closing prices. The notes do not say whether the BFE price is the best back
price or a last-traded price, or whether it is net of Betfair commission. **Conservative reading:**
treat BFE as a gross back price (no commission taken off) and apply the 2% Matchbook commission to it,
as CLAUDE.md s8 requires. This is recorded as a limitation in REPORT.md.

**Licence lines quoted for each data source** (CLAUDE.md s2):
- football-data.co.uk (https://www.football-data.co.uk/data.php): "it's all FREE , however its use is
  intended for private individuals only, NOT commerical or data training products using automated
  bots/scrapers/AI." Our use is a private individual's non-commercial research. The files are the site's
  own CSV download links, fetched politely (one file every ~4 s, about 150 files in total). It is not
  a commercial product or a training-data product. I read this as inside the intended use, but the
  wording about automated bots is ambiguous, so it is flagged in REPORT.md for the owner. To be honest
  about the order of events: I started the download before reading this line on data.php.
- Matchbook API (https://developers.matchbook.com/docs/faq.md): "Typically, customers use the API to
  connect automatic trading bots to the exchange, but it is also used to connect to third party websites
  to deliver live pricing and other market event information." Fair Usage Policy 3.5(d) forbids using
  the API "for purposes of monitoring the availability, performance, or functionality of any of
  Matchbooks' products and services or for any other benchmarking or competitive purposes". A research
  recorder that measures how stale Matchbook prices are could arguably fall under this, so I added an
  owner item: email api@matchbook.com for written OK (the policy invites this in s2.1).
- The Odds API (https://the-odds-api.com/terms-and-conditions.html): "Permitted uses include, but are not
  limited to: Storing our data and retaining it indefinitely … Using our data in research papers and
  analytical dashboards … Calculating and displaying values you derive from our data". It forbids only
  resale/redistribution as a raw feed. Not bought; awaiting owner yes.

**Matchbook feasibility probes** (5 unauthenticated GETs in total, 2026-10-27 ~21:20 UTC):
- `GET https://api.matchbook.com/edge/rest/events?sport-ids=15&include-prices=true&exchange-type=back-lay…`
  works **without login**. The default exchange-type for our region is "binary" (win/lose sides), so the
  recorder must pass `exchange-type=back-lay`.
- Liquidity snapshot saved to `docs/evidence/matchbook_liquidity_snapshot_2026-10-27T2123Z.csv`.
  Median of the smallest best-back amount across the three 1X2 outcomes: Championship £3, League 1 £2,
  League 2 £8, National League £2, Serie B £4, Ligue 2 £16, 2.Bundesliga £24 (2 games only). These games
  were mostly 1–4 days from kick-off; liquidity normally grows near kick-off. Still, £20 at the best back
  price looks uncommon in these leagues.

**Conservative choices so far**
- Candidate leagues fetched: E1, E2, E3, EC, SC1, SC2, SC3, D2, I2, SP2, F2 (second tier and lower that
  football-data publishes in full format). Final list fixed in PREREGISTRATION.md after the coverage table.
- Seasons fetched: 2012-13 to 2025-26. 2026-27 is in progress and excluded, as CLAUDE.md requires.
- Holdout seasons 2024-25 and 2025-26 are fetched in the same pass, as s7 requires. For those seasons,
  only field coverage and row counts were computed before sealing. No prices were compared and no CLV was computed.
- Expected rows per league-season = teams × (teams − 1), × 2 for Scottish leagues (they play four times).
- p-value: one-sided, from the centred cluster bootstrap (10,000 resamples, fixed seed). The smallest
  reportable p is about 1e-4.

**Download and coverage (21:20–21:33 UTC).** 154 files (11 leagues × 2012-13..2025-26) were fetched and
verified in `data/MANIFEST.csv`. 142 matched the expected row count exactly. The 12 that did not are all
explained: COVID-curtailed 2019-20 seasons (E2, E3, EC, F2, SC1–3) and 2020-21 (EC, SC1–3); E2 2019-20
had 23 teams (Bury expelled); F2 2023-24 has one match missing (−1). None are in the analysis window.
Coverage (`results/coverage.csv`): **Betfair Exchange columns exist only from 2024-25.** Pinnacle covers
only ~24–49% of 2025-26 matches.

**Forced deviation (before any CLV).** CLAUDE.md s8 names 2024-25 and 2025-26 as the sealed holdout, but
those are the only seasons with exchange prices. Conservative choice: development = 2024-25, sealed
holdout = 2025-26. Reason: it keeps an untouched holdout and still allows a development result. Recorded
in PREREGISTRATION.md (commit 4105a4b, 21:33:56 UTC). With only one development season, fading is checked
by month and by a first/second-half split at the median flag date.

**Placebo calibration.** First run: check (b) rejected 100% → the machinery was broken. I found the bug:
centring on the pool mean instead of the stratum mean (3-point bias). Fixed and re-run: (a) 0.0%,
(b) 3.0%. Passed. Recorded as an addendum in PREREGISTRATION.md before the development run.

**Phase 1 results.** V0001 development: 300 flags, mean CLV +0.94% [−0.48%, +2.39%], p = 0.097.
Committed as final (results/phase1_dev.json), then unsealed once (results/UNSEALED.json; a second unseal is
refused). V0002 holdout: 173 flags, mean CLV +0.62% [−0.57%, +1.84%], p = 0.16. Both are > 0, so the
pre-registered spending rule does not force a stop. Neither meets the hypothesis.

**Gate-5 arithmetic** (no new CLV computed): at +2% CLV and a £10 stake, about 245 persisting flags a
month are needed to cover about £49 a month in costs. At the observed CLV it would be 550–1,600 a month.
Because of this and the thin liquidity, I recommended stopping. I asked the owner once for the paid-phase
items in case they want to go ahead anyway.

## Next steps

1. Wait for the owner's reply. If "stop": set REPORT.md status to NO EDGE, with the sentence "Historical
   CLV small and non-significant; live test not run on cost grounds", and finish.
2. If the owner says yes to all four items, and Matchbook confirms in writing that the use is permitted:
   build the recorder in `recorder/` (Phase 2 spec in CLAUDE.md s9 and PREREGISTRATION.md "Phases 2–4"),
   unauthenticated Matchbook GETs only (no login file needed), plus the install script and unit tests.
   Then a 1-day dry run, then the 1-week pilot (counts only).
3. Any override goes in a new "Overrides" log section here and in REPORT.md s7.
