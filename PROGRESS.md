# PROGRESS (working log)

A fresh session can resume from this file alone. Standing instructions: CLAUDE.md.

## Where we are

- Phase 0a (is it beatable?) and Phase 0b (feasibility): done, written up in REPORT.md.
- Phase 1 (historical check): see the log below for the current step.
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
