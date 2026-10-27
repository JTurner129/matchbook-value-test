# REPORT: sharp-anchored value bot on Matchbook

**Status:** BLOCKED (owner action needed). The free historical check found a small positive average
(+0.6% to +0.9%) that is not statistically significant and well below the +2% target; the paid live
test needs your decision, and I recommend **not** paying for it (reasons below).

**Costs to date:** £0.00 (football-data.co.uk: free; Matchbook API: free, unauthenticated reads; no
odds feed bought; no machine rented). Total £0.00.

**Owner action needed:** Item 1 is done: Matchbook gave the OK (28 Oct 2026, reported by the owner). Still
needed: a decision to pay for the live test (about £50 a month for 2–3 months) despite my recommendation to
stop. If yes, a yes to items 2–4 in [Owner action needed](#owner-action-needed). If no, reply "stop" and I
will mark the project NO EDGE.

---

## Up front: this is very unlikely to make money at £5–10 stakes

Pass gate 5 asks whether the idea can pay for its own data and machine costs. Suppose the full
hypothesised edge of +2% were real. Even then, with £10 stakes the bot would need about **245 bets a
month** that survive 30 seconds with £20+ available, just to cover about £49 a month in costs. With £5
stakes it would need about 490. At the edge Phase 1 actually measured (+0.6% to +0.9%), it would need
550 to 1,600 a month. Matchbook's second-tier football markets showed only £2–£25 at the best back price
in our snapshot (see below). So hundreds of qualifying bets a month looks out of reach. The live test
could still say whether stale prices exist, but it is very unlikely to reach CONFIRMED.

---

## 1. Is this market beatable? (Phase 0a sense check)

1. **Who sets Matchbook prices on second-tier football?** No authoritative source says. Matchbook says it
   does not trade on its own exchange ("Matchbook as an entity does not trade on the exchange", a Matchbook
   staff post, SportsbookReview forum, 2012). Users in the same thread report bots that post offers copied
   from Pinnacle ("some bot use Pinnacle odds to offer odds on matchbook";
   [thread](https://www.sportsbookreview.com/forum/sportsbooks-industry/912566-matchbook-bets-have-been-cancelled)).
   This is old and anecdotal. Our own snapshot (27 Oct 2026) fits that picture. Summed best-back prices on
   second-tier 1X2 markets were only 101–108% of a full book, which is close to fair. The amounts at the best
   price were tiny: a median of £2–£25 on the thinnest outcome. Small, tight quotes fit (but do not prove) automated
   copying of a sharp price.
2. **Why would a stale price survive a few minutes with £20+ on it?** The main way is if the copier bots
   update slowly or skip these leagues. But a stale price is free money to anyone watching, and each one only
   holds a few pounds, so it would be taken quickly. We found no evidence that £20+ stale prices last for
   minutes.
3. **Who else is competing?** Commercial value-bet scanners and odds APIs sell exactly this comparison. The
   Odds API and OddsPapi both carry Matchbook alongside Pinnacle, and vendors publish "build a value-betting
   scanner" tutorials. Anyone with a $30–$60 feed can run the same scan.
4. **What would we see if the idea is wrong?** Few flags; flags that vanish within seconds; or flags whose
   closing line value is near zero or negative.

**Verdict of the sense check:** it is doubtful, but not certainly impossible. The live test exists to
measure points 2 and 4 directly.

## 2. Feasibility (Phase 0b)

**Matchbook API** ([docs](https://developers.matchbook.com/)).
- Event and price reads (`GET /edge/rest/events?...&include-prices=true&exchange-type=back-lay`) work
  **without logging in**. So no login and no write call of any kind is needed. You must pass
  `exchange-type=back-lay`, because the default here is "binary".
- Rate limits (Fair Usage Policy 4.2): Events group 700 requests/minute, Navigation 100/minute.
- Fees (pricing page): "Each set of 1 million GET requests in a calendar month will be charged at 100 GBP".
  The planned recorder needs about 15,000–25,000 GETs a month: one combined events call every 3 minutes,
  plus re-polls at +30 s and +60 s on flags. That is about 2% of the fee threshold.
- Automated use: "Typically, customers use the API to connect automatic trading bots to the exchange" (FAQ).
- **Terms risk:** Fair Usage Policy 3.5(d) forbids using the API "for purposes of monitoring the
  availability, performance, or functionality of any of Matchbooks' products and services or for any other
  benchmarking or competitive purposes". A recorder that measures how stale Matchbook's prices are could be
  read as monitoring. Before any recording, I ask you to get written OK from api@matchbook.com. Section 2.1
  of the policy invites exactly this request.

**Odds feeds with a sharp bookmaker, within £50 a month**

| Feed | Price | Sharp book | Target-league coverage | Update rate | Freshness timestamp | Licence |
|---|---|---|---|---|---|---|
| **The Odds API** (recommended) | $59/mo for 100,000 credits (≈ £44–47; check VAT at checkout). $30/mo for 20,000 credits. | Pinnacle (`eu` region; "Odds are from public website which may incur a delay") | Championship, League 1, League 2, 2. Bundesliga, Serie B, La Liga 2, Ligue 2. **Not** the National League or the Scottish lower leagues. | Pre-match 1X2 every 60 s (exchanges 20 s) | Yes: per-market `last_update`, "the last time our system saw odds for that market from the bookmaker" | "Permitted uses include … Storing our data and retaining it indefinitely … Using our data in research papers and analytical dashboards"; it forbids only reselling the data as a raw feed |
| Pinnacle-only APIs (pinnodds, pinnapi) | $99–229/mo | Pinnacle | not checked | — | — | over budget |
| SportsGameOdds | from $99/mo | Pinnacle | not checked | 3-min delay on the cheapest plan | — | over budget |
| OddsPapi | free tier with 250 requests/mo; paid plans not public | Pinnacle (vendor's claim) | not checked | — | — | free tier is far too small |
| Pinnacle's own API | closed to the public since July 2025 (per a 2026 comparison) | — | — | — | — | not available |

**Liquidity in the target leagues.** Snapshot taken 27 Oct 2026, 21:23 UTC, unauthenticated. The file is
`docs/evidence/matchbook_liquidity_snapshot_2026-10-27T2123Z.csv`. All these leagues have Matchbook 1X2
markets. The median £ available at the best back price on each game's thinnest outcome was:
Championship £3, League 1 £2, League 2 £8, National League £2, Serie B £4, Ligue 2 £16, 2. Bundesliga £24
(2 games). Most games were 1–4 days from kick-off. Liquidity usually grows near kick-off, but **£20 at the
best price is clearly not the norm** in these leagues.

## 3. Phase 1 results (historical check, free data)

**What was tested.** For each match outcome, the bot "bets" when the Betfair Exchange price exceeds the
margin-free Pinnacle price by at least 3%, both taken from the same Friday/Tuesday-afternoon snapshot.
Each bet is then scored against the margin-free Pinnacle closing price, after 2% commission. That score is
closing line value (CLV). A positive CLV means the bet got a better price than the sharp market's final
view.

**Data window, and a forced change to the plan.** Betfair Exchange prices only appear in the
football-data files from 2024-25 onwards (coverage table: `results/coverage.csv`). The plan had reserved
2024-25 and 2025-26 as the sealed holdout, which would have left nothing to develop on. So, before
computing anything, I used **2024-25 as the development set** and sealed **2025-26 as the holdout**. The
2025-26 holdout is smaller because football-data's Pinnacle prices for that season stop around January
2026. This is recorded in PREREGISTRATION.md, committed before any result was computed.

| | Development 2024-25 | Holdout 2025-26 |
|---|---|---|
| Outcome records used (after exclusions) | 12,522 | 4,116 |
| Flags (bets) | 300 (2.4%) | 173 (4.2%) |
| **Mean CLV after commission** | **+0.94%** | **+0.62%** |
| 95% confidence interval | −0.48% to +2.39% | −0.57% to +1.84% |
| One-sided p-value (mean > 0) | 0.097 | 0.16 |
| Bonferroni bar (N variants) | 0.05 (N=1) | 0.025 (N=2) |
| Meets hypothesis (≥ +2% and significant)? | **No** | **No** |
| Placebo: random matched bets, average mean CLV | −4.8% | −4.0% |
| Robustness: proportional method | +1.68% (same sign, within 1 pt) | +1.48% (same sign, within 1 pt) |
| Secondary: CLV against Betfair's closing price | +1.11% | −1.73% |
| Flat-stake P&L per £1 (noisy, secondary) | +13.3p (CI −6.7p to +34.0p) | +7.1p (CI −19.8p to +34.8p) |
| First half vs second half of period | +1.05% vs +0.83% | +0.07% vs +1.16% |
| Mean without the best league | +0.75% (dropping SC3) | +0.15% (dropping E2) |
| Flags with edge > 20% (kept in) | 1 | 3 |

**What these numbers mean, in plain words.**
- The flags do pick prices that are better than average. A random matched bet loses about 4–5% against
  the close, and the flagged bets come out about 0.6–0.9% ahead.
- That small lead is **not reliable**. Both confidence intervals include zero, and neither p-value is
  anywhere near the bar.
- It is also **less than half the +2% the hypothesis needs**. In the holdout, nearly all of it comes from
  one league (League One). Without it, the mean is +0.15%.
- Football-data gives one snapshot per match. Betfair is not Matchbook, and these prices carry no stake
  sizes, so we cannot tell whether £20 was available. This is evidence for the spending decision, not a
  verdict.

**Tables by league and by month** (development / holdout) are in `results/phase1_dev.json` and
`results/phase1_holdout.json` (`by_league`, `by_month`). No single month or league is reliably positive.
In the development season, only La Liga 2 (SP2, 20 flags, +5.0%) has a confidence interval above zero.
That is one of 11 leagues, which is the kind of result chance alone produces.

**Pre-registered spending rule.** "Recommend paid phases only if both development and holdout mean CLV
are above 0." Both are above 0 (+0.94%, +0.62%), so the rule **does not require stopping**. It is a
minimum condition, not a reason to go ahead. Weighing everything (small, non-significant effect; thin
liquidity; the gate-5 arithmetic at the top; a terms question), **my recommendation is to stop and not
pay.** If you prefer to learn the answer directly, the cheapest informative path is in item 2 below: one
month of the feed for the dry run and the 1-week pilot, cancelled if the pilot's early-stop rule triggers.

## 4. Live results

Not started (needs owner approval).

## 5. Variants, significance bar and placebo calibration

- `variants.csv`: **N = 2** real-data runs so far (V0001 development, V0002 holdout). The bar at the
  holdout run was p < 0.025.
- Placebo calibration (200 matched placebo sets, nominal α = 0.05, development data):
  - Pass rate for the sets as written: **0.0%** (limit 10%).
  - Null-centred check, where each record is centred on its stratum's mean so the true mean is exactly 0:
    **3.0%** rejections, against about 5% expected and a 10% limit. **Passed.**
  - The first run of the null-centred check failed (100%). The cause was a bug in the check: it centred on
    the pool mean instead of the stratum means. I found and fixed it before any development CLV was
    computed. It is recorded in PREREGISTRATION.md (addendum) and PROGRESS.md.

## 6. Exclusions (with counts)

| Reason | Development | Holdout |
|---|---|---|
| Outcome records in files | 12,606 | 12,606 |
| No valid Pinnacle pre-closing price | 24 | 8,415 (Pinnacle data stops ~Jan 2026) |
| Pinnacle pre-closing overround outside 1.00–1.12 | 3 | 3 |
| No Betfair pre-closing price | 57 | 69 |
| No Pinnacle closing price | 0 | 0 |
| Pinnacle closing overround outside 1.00–1.12 | 0 | 3 |
| No result | 0 | 0 |
| **Used** | **12,522** | **4,116** |

## 7. Overrides

None.

## 8. Data-source terms and limitations

- football-data.co.uk: "its use is intended for private individuals only, NOT commerical or data training
  products using automated bots/scrapers/AI". This project is a private individual's non-commercial
  research using the site's own download links, so I read it as within the intended use. Please confirm
  you are happy with that reading.
- The notes do not say whether Betfair Exchange prices are best back prices or net of commission. I treated
  them as gross back prices and applied 2% commission, which is the conservative choice.

## Owner action needed

Only needed if you decide to go ahead despite the recommendation. Reply with yes or no to each item.

1. **DONE (28 Oct 2026): Matchbook gave the OK, per the owner.** **Matchbook account: not needed.** Prices are readable without logging in, so no account, deposit or ID
   check is required. **Instead, please email api@matchbook.com** (free), because of Fair Usage Policy
   3.5(d). Suggested text: *"I'm a private UK customer planning a personal, non-commercial research script
   that reads pre-match football prices from the public events endpoint every 3 minutes (about 20,000 GETs
   a month) to study price movements. No bets will be placed by the script. Is this permitted under your
   Fair Usage Policy?"* I will not start recording without a yes from them. No environment variable is
   needed.
2. **Odds feed: The Odds API, 100K plan, $59/month (about £44–47).** Sign up at
   https://the-odds-api.com, choose the 100,000-credit plan, and check the checkout total. If VAT or
   currency conversion pushes it above £50, choose the $30 (20,000-credit) plan instead, and I will limit
   recording to the three English leagues every 5 minutes. Why: it is the only feed found within budget that
   has Pinnacle for the target leagues, a per-market freshness timestamp and a licence that permits this
   use. Estimated use: about 58,000 credits a month (7 leagues, polled every 3 minutes while a game is within
   24 h). Put the key in the environment variable `ODDS_API_KEY`. Cancel after month 1 if the pilot's
   early-stop rule triggers.
3. **Always-on machine: a small cloud server, about £4 a month** (for example Hetzner Cloud CAX11 or CX22,
   about €4–5/month; check the price at sign-up). You do not need to give me SSH access. I will provide a
   one-command install script that sets up the recorder as a service with automatic restart and clock sync.
   You run it once on the server.
4. **Where recorded data goes: a new private GitHub repository** (free), for example
   `jturner129/matchbook-value-data`. Add a deploy key with write access to that repository only, and
   install it on the server. The recorder pushes one compressed file per day plus a daily health summary.
   This session then reads that repository.

Expected total if run to the maximum: about £50 a month × 2–3 months = **£100–£150**.
