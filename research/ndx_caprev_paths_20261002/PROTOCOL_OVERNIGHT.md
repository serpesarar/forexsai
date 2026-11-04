# Phase 4 — attached v2 audit (2026-10-02)

Written after reading the other agent's TUR4/W7 results and our preceding phases. This is retrospective, not an untouched holdout. Snapshot the attached report and source files before running.

Six frozen definitions, same previous-cash stress/VIX>=18.4/Mon–Thu and 1 daily-return-vol initial risk:

1. OPEN_SAME: BUY at NY09:30, exit same cash session16:00. H1 cannot reproduce09:30: use09:00 explicitly as OPEN_PROXY, never claim exact RTH open.
2. DIP_SAME: existing CAPREV, same session exit, baseline.
3. DIP_NEXT: same entry, exit next macro cash session16:00; stop remains active across every available overnight bar. On a gap through stop, use worse next observed bid open. No target.
4. OPEN_NEXT: opening entry with next cash session exit, control.
5. UNION_SAME: chronological opening/dip opportunities, both same-day exit; accept only if the single total position is flat, including600-second decision cooldown. Opening priority only at identical timestamps.
6. UNION_MIXED: OPEN_SAME plus DIP_NEXT, same single-position rule. This tests the textual v2 description, unlike W7's sum of two legs with the same exit horizon.

Dual-leg sum is descriptive only: also report equal half-risk weights (0.5*opening R+0.5*dip R), maximum simultaneous legs and raw event days. It is not an additional selected trading definition or a live-valid portfolio.

Sources: frozen M1 cohorts D25a/D25b/C26/M26/S26; native15/30/60, no new data. Trigger/execution native TF as previously audited; M1 trigger/execution1m. Native time/spread and funding remain proxies. Use complete previous RTH as in phase1. Period outcome crossing boundaries excluded from period summaries; unresolved final exits are counted separately.

Four execution cases: base (recorded/proxy spread,0.2point per-side slip); spread3; slip1; illustrative5bp entry-notional per overnight calendar date (funding stress, not actual broker financing). Funding charged for nights actually held, including missing-quote dates. Scheduled vs missing quote gaps cannot be fully separated; count all and never assert overnight gap-free validation.

Report realized-count vs unique days; bootstrap at day level, chronological halves, drawdown, removal of best5, years; no summing overlapping TFs. A150-event count alone does not pass the project live card.
