# Project: test a sharp-anchored value bot on Matchbook (idea 1)

You are running a research-and-test project for a UK-based individual (the owner, me). This file is the
project's standing instructions; it lives in the repository as CLAUDE.md.

Work unattended. Never ask me questions except where this file says "ask the owner". Otherwise make the most
conservative reasonable choice, record it in PROGRESS.md with a one-line reason, and carry on. If restarted,
read PROGRESS.md and resume where you left off. Commit and push after every milestone.

**"No edge found" is an acceptable and likely result. A fake pass is not.** The research behind this idea
rated the chance of a real, lasting edge at no better than about 1 in 4.

---

## 1. The idea being tested

A bot takes a margin-free "fair" price from a sharp reference (a low-margin sharp bookmaker such as Pinnacle,
via a paid odds feed). It backs on the Matchbook exchange only when Matchbook offers a price far enough above
fair to cover Matchbook's 2% commission. The claim is that Matchbook, being smaller and slower than the
sharpest markets, sometimes leaves prices on second-tier football stale for minutes after the sharp market
moves. This is a liquidity and attention gap, not a forecasting skill.

**Pre-registered hypothesis (fixed before any data is looked at):** bets taken when the Matchbook back price is
at least 3% above the margin-free reference price beat the margin-free sharp closing price by an average of at
least 2% after Matchbook's 2% commission.

---

## 2. Hard rules

- **Never place a real bet.** This project contains no bet-placing code at all. The only write call allowed is
  the session login, if Matchbook requires one to read prices. Add an automated test that fails if the code
  contains any order or offer submission endpoint, or issues any non-GET request other than login. Staking
  real money is out of scope; if the verdict is CONFIRMED, write a proposal for a small-stakes trial in
  REPORT.md and stop.
- **Do not use the Betfair API.** The live key costs £499 and the free delayed key is for development only.
  Betfair prices are used only through the historical columns in football-data.co.uk files.
- **Logins.** Use public, unauthenticated endpoints where they exist. Credentials will be in environment
  variables (MATCHBOOK_USERNAME, MATCHBOOK_PASSWORD, ODDS_API_KEY). Never print, log or commit them, and never
  use them for anything except reading prices.
- **Money.** Data budget: £50 a month at most. Always-on machine: £10 a month at most. Nothing is bought without
  the owner's explicit yes (see section 4). Track every cost in REPORT.md.
- **Terms.** Use only official APIs and permitted downloads, within their published terms and rate limits.
  Quote, in PROGRESS.md, the licence lines that allow personal automated use for every data source. Never
  scrape sites without an API, never rotate IPs, sessions or proxies to get round limits, and never build
  anything designed to avoid detection. If a limit blocks you, schedule the work for later instead.
- **No lookahead.** A decision at time t may use only data timestamped before t. Enforce this in code with
  tests, not just by care.
- **Honesty.** Every gate below is mandatory and must never be loosened, skipped or reinterpreted after data
  has been seen.

---

## 3. Before building anything: is this market beatable? (Phase 0a)

Write a short section in REPORT.md (half a page) answering, with sources:
1. Who sets Matchbook prices on second-tier football? If most liquidity comes from market makers or bots that
   copy sharp prices within seconds, stale prices will be rare and short. Say what you can find.
2. Why would a stale price survive long enough for a bot polling every few minutes to catch it, and still have
   £20 or more available?
3. Who else is likely competing for the same prices (value scanners, arbitrage software)?
4. What would we expect to see if the idea is wrong? (Answer: few flags, flags that vanish within seconds, or
   flags whose closing line value is near zero or negative.)

This is a sense check, not a gate. But if the honest answer is "this almost certainly can't work", say so at the
top of REPORT.md before continuing.

---

## 4. Owner checklist: ask once

Do Phases 0 and 1 (both free) first, then ask the owner **once**, in a single message, for everything the paid
and live phases need. Put the same list in REPORT.md under "Owner action needed". For each item give: what it is,
why it's needed, the exact steps, the cost, and the environment variable name if any. Expected items:

1. A Matchbook account (free), if reading prices needs a login. Say whether a deposit or ID check is needed.
2. The odds feed you recommend (exact product, plan, price, coverage, update frequency, and the quoted licence
   line allowing personal automated use). Wait for a yes before anyone pays.
3. An always-on machine for the 6–10 week recorder (see section 9): your recommended option, monthly cost, and
   whether you need SSH access or will give the owner a one-command install script.
4. Where recorded data will be sent so this cloud session can analyse it (for example a private GitHub repo
   that the recorder pushes compressed daily files to).

Then set REPORT.md status to BLOCKED and stop until the owner replies.

**Overrides.** The owner may later override a decision. An override can: extend or shorten recording, add or
pay for data, fix a technical problem, or stop the project. An override cannot: change the hypothesis,
thresholds, markets or pass criteria after data has been seen; re-include excluded data; or unseal holdout data
early. **An override can never lead to a CONFIRMED verdict;** CONFIRMED requires every gate passed exactly as
written. Log every override in PROGRESS.md.

---

## 5. Phase 0b: feasibility

1. Check Matchbook's current API docs and terms: which price endpoints exist and whether they need login, rate
   limits, GET-request fees (reports suggested £100 per million GET requests on some tiers), and confirmation
   that automated use is allowed. Quote the relevant lines. Estimate the monthly request count of the planned
   recorder and keep it far below any fee threshold.
2. Find odds feeds that include a sharp bookmaker (Pinnacle or similar) for the target markets, within £50 a
   month, whose licence allows personal automated use. List each with price, coverage of the target leagues,
   update frequency, whether it returns a per-price "last updated" timestamp, and the licence wording. If none
   qualifies, Phase 2 onwards cannot run: say so plainly at the top of REPORT.md (Phase 1 still runs).
3. Check that the leagues you plan to target actually have Matchbook match-odds markets with some liquidity.
4. Write findings to REPORT.md and PROGRESS.md.

---

## 6. How proof works for this strategy

- **The primary measure is closing line value (CLV), not profit.** For a value strategy, CLV gives a verdict in
  weeks with far less noise than P&L. Do not use "profitable in X% of months" style tests: they are noisy and
  unfair to any strategy with lumpy results.
- **Definitions (fixed now):**
  - Margin removal: the **power method** over the three 1X2 outcomes of one bookmaker snapshot. Report the
    proportional method as a robustness check only; it must agree in sign and be within 1 percentage point, or
    flag it in the report. It is not a separate variant and never used for the verdict.
  - `fair_t` = margin-free sharp price for the selection at decision time t.
  - `edge_t` = Matchbook best back price / `fair_t` − 1. A flag needs `edge_t` ≥ 0.03.
  - Effective price after commission: `eff = 1 + (back_price − 1) × 0.98`.
  - `CLV = eff / fair_close − 1`, where `fair_close` is the margin-free sharp price at the last reference
    snapshot before the market goes in-play (use the actual in-play flag, not the scheduled kick-off). If no
    reference snapshot exists within 10 minutes of going in-play, exclude the flag and count the exclusion.
  - Secondary: CLV against the Matchbook closing back price. Reported, not a gate.
- **One bet per selection:** only the first qualifying flag per (event, selection) counts. Later flags on the
  same selection are ignored in the primary analysis.
- **Statistics:** outcomes within one match are correlated, so all confidence intervals use a cluster bootstrap
  by event (10,000 resamples).
- **The luck test.** Keep `variants.csv`, an append-only log written automatically by a wrapper that every
  analysis run goes through. Every run that computes CLV or P&L on real (non-placebo) data is a variant:
  thresholds, leagues, time windows, model tweaks and quick one-off checks all count, from day one. With N
  variants at verdict time, the significance bar is one-sided p < 0.05 / N (Bonferroni).
- **The placebo check.** Build it before the real test, and run the full pass/fail machinery on placebo data:
  - Placebo selection: pick the same number of random (event, selection, snapshot) records, matched on league,
    price band and time to start, instead of the flagged ones.
  - Whenever outcomes or results are shuffled (for example in P&L checks), shuffle each whole outcome record
    together: result, its prices and its closing price move as one unit. **Never shuffle results alone while
    keeping the original prices.** That mistake made almost every placebo pass falsely in an earlier project.
  - Calibrate: run 200 placebo sets at a nominal α = 0.05 (no Bonferroni). The pass rate must be no more than
    10%. If it is higher, the test machinery is broken: stop, find the bug, and record it.

---

## 7. Data hygiene (applies to every phase)

- **Verify every download.** Record URL, date fetched, file size, SHA-256 and row count in
  `data/MANIFEST.csv`. Read every file to the end; compare row counts with the expected number of matches per
  league-season. A truncated file must be re-fetched, never silently used.
- **Check field coverage by year before designing anything.** Produce a table of which columns are populated,
  by league and season. The usable test window is set by the field with the shortest history; state it plainly.
- **Check every field was really known at the time.** Read the data source's notes on when each price was
  collected. Watch for sources that rewrite history (for example current team names or details applied to old
  rows). If a field's timing is unclear, don't use it for decisions.
- **Plan holdout inputs at the start.** Fetch everything the sealed holdout will need in the same pass as the
  development data, so opening it later needs no new downloads.
- **Fetch politely.** Respect rate limits with backoff, schedule large downloads, and start them early.
- All timestamps in UTC. Store both the API's own timestamp and the time you received the data.

---

## 8. Phase 1: historical sanity check (free data)

Use football-data.co.uk CSVs. Read its notes file first and quote, in PROGRESS.md, what the columns mean and
when opening and closing prices are collected. The likely relevant columns are the Pinnacle prices
(early and closing) and the Betfair Exchange prices (early and closing), but confirm names and meanings.

- **Leagues:** second-tier and lower leagues, for example English Championship, League One, League Two and
  National League plus comparable European tiers, as far as coverage allows. Fix the list in
  PREREGISTRATION.md before computing any CLV.
- **Window:** the research assumed 2012–2026, but the Betfair Exchange columns may start much later. The
  coverage table decides; use only seasons where both sharp and exchange prices exist. Exclude the current,
  incomplete 2026–27 season.
- **Sealed holdout:** the two most recent complete seasons (2024–25 and 2025–26). Move them to
  `data/sealed/`, record their SHA-256 in PREREGISTRATION.md, and make the analysis code refuse to read that
  folder until a single explicit `unseal` step, run once, after the development result is final.
- **Test:** for each match outcome, flag it when the Betfair early price is at least 3% above the margin-free
  Pinnacle early price (both collected at the same time, so no lookahead). Measure CLV against the margin-free
  Pinnacle closing price, after 2% commission.
- **Report:** number of flags; mean CLV with cluster-bootstrap confidence interval; the placebo comparison; a
  table by season and by league; an early-half versus late-half comparison of development seasons, and the
  trend of per-season CLV, to show whether any edge is fading. A good total can hide an edge that has
  disappeared, so the per-season table is required. Then unseal and report the holdout once.
- **Limits of this check:** Betfair is not Matchbook, and two snapshots can't show minute-by-minute staleness.
  Treat Phase 1 as evidence for the spending decision, not as a verdict on the idea. In the owner checklist,
  recommend going ahead with paid phases only if both development and holdout mean CLV are above 0; otherwise
  recommend stopping and say why.

Write PREREGISTRATION.md and commit it **before** any CLV is computed. The git timestamp is the proof.

---

## 9. Phases 2–4: live log-only recording

Only after the owner has approved the costs.

### Phase 2: build the recorder
- **Where it runs:** on the always-on machine, not this cloud session. Cloud containers are temporary.
- **What it records, every 2–5 minutes, for target matches from 24 hours before start until in-play:** Matchbook
  best back and lay prices with available size, the sharp reference prices with their own last-updated
  timestamps, and the market status.
- **When a selection flags,** re-poll that Matchbook market at +30 and +60 seconds to measure whether the price
  persisted. Stay within rate limits.
- **Flag rules (fixed in PREREGISTRATION.md before recording):** `edge_t` ≥ 0.03; at least £20 available at the
  flagged price; reference snapshot no more than 2 minutes old (so a stale reference isn't mistaken for a stale
  Matchbook price); Matchbook and reference snapshots within 60 seconds of each other; flag time at least 5
  minutes before start.
- **Event matching:** map feed events to Matchbook events by kick-off time (within 15 minutes) and both team
  names. Log every unmatched event. Any flag with `edge_t` above 20% is automatically checked for a mapping or
  data error (wrong match, swapped home/away, wrong market); exclude it only if an error is proven, and report
  the count. Exclude voided or postponed events and report the count.
- **Reliability:** run as a service with automatic restart; keep the clock synced; write compact compressed
  daily files; detect and log gaps; push data daily to the agreed location; send a short daily health summary
  (counts, gaps, errors). The health summary must not contain any CLV or P&L figures.
- Add unit tests for: no lookahead, the margin-removal maths, the CLV formula, the event mapper, and the
  "no bet-placing code" rule. Do a one-day dry run before the pilot.

### Phase 3: pilot (1 week)
Run the recorder for a week to fix bugs and finish the team-name mapping. Report only counts: flags per day,
how many had £20 available, how many persisted 30 seconds. **Do not compute CLV on pilot data.** Pilot data
never enters the verdict.

Pre-registered early stop: if the pilot produces fewer than 10 qualifying flags in the week, the opportunity
rate is too low for the idea to be worth anything. Report NO EDGE (no opportunities) and stop, after one more
week to rule out a quiet fixture week.

### Phase 4: confirmation recording
Freeze the code and config (record the git commit). Any change to the flag logic after this point restarts the
confirmation clock.

- **Stopping rule (based on counts, never on results):** run until at least 6 weeks have passed **and** at least
  300 qualifying flags have been recorded, up to a maximum of 10 weeks. If there are fewer than 300 flags at 10
  weeks, the verdict is INCONCLUSIVE (too few opportunities), unless the futility check below already applies.
- **Stay blind:** don't compute CLV or P&L during recording, except at one pre-registered interim look at week 4,
  for futility only: if the upper end of the 95% confidence interval on mean CLV is below 0, stop with NO EDGE
  to save data fees. The interim look can stop the test, never pass it.
- Exploratory ideas (tennis, other leagues, other thresholds) may be logged but are analysed only as
  exploratory, count as variants, and can never produce the verdict. One that looks good must be
  pre-registered and tested on a fresh, later recording window.

### Phase 5: analysis and verdict
**Pass (CONFIRMED) needs all of these, on the confirmation data:**
1. At least 300 qualifying flags.
2. Mean CLV after commission of at least +2%.
3. One-sided p-value for mean CLV > 0 below 0.05 / N, where N is the variant count in `variants.csv`.
4. At least 50% of flagged prices still available, at the same or better price with £20 or more, 30 seconds
   later.
5. Positive expected value after costs: mean CLV × a realistic £5–10 stake × flags per month that pass gate 4,
   minus the monthly data and machine costs, is above 0. Also show it next to what £500 earns in an easy-access
   savings account (roughly £1–2 a month).
6. The placebo calibration passed, and the result does not rest on one league or one week: report results by
   league and by week, and the mean CLV with the single best league removed.

Also report simulated flat-stake P&L with its confidence interval, labelled as noisy and secondary.

---

## 10. Engineering on the cloud machine

- This cloud session is temporary and has about 15 GB of memory. Checkpoint long jobs so they resume after a
  restart, keep data compact (Parquet, only needed columns), limit parallel workers, and recover from
  out-of-memory kills by resuming at a smaller batch size. Don't run heavy one-off tests alongside a main job.
- Use scheduled check-ins, where available, to monitor long jobs and the recorder's daily health summary.
- Raw data stays out of git (`.gitignore`); `data/MANIFEST.csv` and all code, configs, PREREGISTRATION.md,
  `variants.csv`, PROGRESS.md and REPORT.md are committed.

---

## 11. Reporting

**REPORT.md** starts with three lines, kept up to date:
- **Status:** one of NOT STARTED, IN PROGRESS, BLOCKED (owner action needed), NO EDGE, INCONCLUSIVE,
  PROMISING (historical check positive; live test not finished), CONFIRMED. Then one plain sentence.
- **Costs to date:** each item and the total, in GBP.
- **Owner action needed:** the exact asks, or "none".

Then: the "is this beatable?" check, feasibility findings, Phase 1 results, live results, the variant count and
significance bar used, the placebo calibration, every exclusion with counts, every override, and a plain
conclusion. Write for a non-specialist: short sentences, say what each number means. Never round a negative
result into a positive one.

**PROGRESS.md** is the working log: date, what was done, every conservative choice made and why, and what's
next. Keep it good enough that a fresh session can resume from it alone.
