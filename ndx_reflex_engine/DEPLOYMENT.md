# Reflex Engine — Live Deployment Guide (2026-07-06)

The validated NDX edge (momentum-continuation + 15-minute time-stop, leak-free) wired
end-to-end into the main panel: backend detector → Supabase → panel card → MT5 bot.
**Ships SHADOW by default. Nothing trades real money until you flip two switches.**

## Pieces built
| Layer | File | Role |
|---|---|---|
| DB | `supabase/migrations/20260706_create_reflex_signals.sql` | `reflex_signals` table |
| Backend service | `backend/services/reflex_engine_service.py` | leak-free mom_cont detector + signal emit + 15m time-stop/SL resolver |
| Backend loop | `backend/main.py` (§4.6) | 30s tick, opt-in `REFLEX_ENABLED=1` |
| Backend API | `backend/routers/reflex_router.py` | `/api/reflex/{live,signals,performance}` |
| Frontend | `frontend/lib/api/reflexEngine.ts` + `frontend/components/panels/ReflexEnginePanel.tsx` | live card (signals table + WR/EV/PF/DD), wired into `SymbolPage` (NDX only) |
| MT5 bot | `yeni deneme/reflex_exec.py` + hook in `forexsai_demo_bot.py` | own magic (+3), market entry + catastrophic SL, 15m time-stop close |

## Data flow
```
MT5 tick feed → Redis → DataHub 1m/15m bars
   → reflex_engine_service.detect_event()  (closed bars only, no lookahead)
   → reflex_signals (Supabase, status=active, mode=shadow)
   → [panel]  GET /api/reflex/*  → ReflexEnginePanel card (live)
   → [bot]    GET /api/reflex/live → reflex_exec (SHADOW: logs; LIVE: MT5 order)
   → 15 min later: resolver walks real 1m bars → status=closed_win/loss, r_multiple
```

## Turn-on sequence (do in order)
1. **Apply the migration** — run `supabase/migrations/20260706_create_reflex_signals.sql`
   in the Supabase SQL editor (MCP is read-only; must be applied manually once).
2. **Backend detector (writes shadow signals):** set env `REFLEX_ENABLED=1` on the Railway
   backend (leave `REFLEX_MODE=shadow`). Redeploy. The panel card starts populating within
   the NY session (13:00–20:00 UTC) as momentum events fire (~2–3/day expected).
3. **Watch the panel:** the "Reflex Engine" section on the NASDAQ page shows live signals +
   rolling WR/EV/PF. Confirm signals appear and resolve after 15 min. Expect **WR ~45%, EV
   positive** — do NOT be alarmed by sub-50% win rate, that is the design (bigger winners).
4. **Shadow-graduate (2–4 weeks):** once ≥50 signals resolved AND live shadow WR is ~45% AND
   EV ≥ 0 AND you've checked real IC spreads/fills against the assumptions, proceed.
5. **Go live (demo account):** set `REFLEX_LIVE = True` in `yeni deneme/config.py` (or env
   `REFLEX_LIVE=1`) and restart the bot. It trades the `+3` magic slot at `LOT_SIZE`, own
   catastrophic SL, closes each position at its 15-minute time-stop. Set backend
   `REFLEX_MODE=live` so signals are tagged live.

## Safety / honesty properties (built in)
- **No lookahead:** detector uses only closed 1m/15m bars (the exact `label="right"` fix that
  killed the 70%→52% leak). ATR/stretch/regime strictly causal.
- **Honest resolution:** outcomes walk real 1m bars (catastrophic SL checked intrabar, else
  time-stop at deadline close) — never an optimistic fill convention.
- **Isolated:** own magic (+3), own table, own resolver — does not touch prediction_logs,
  signal_lifecycle, or the other bot scopes.
- **Shadow-first:** `REFLEX_ENABLED` (backend loop) and `REFLEX_LIVE` (bot orders) are separate
  and both default OFF/observe. The panel works in shadow with zero live risk.
- **Direction-agnostic:** the engine never claims to predict direction (proven unpredictable);
  it harvests momentum drift with asymmetric payoff and a deterministic exit.

## Expected performance (from leak-free backtest, 10 groups, realistic fills)
mom_cont + time-stop: **WR 47–58%, EV +0.49R (2025 holdout) / +1.03R (2026 broker), PF 2.0–3.7,
tiny drawdown (~5R)**. This is the whole validated edge; the reversion families were dropped
(leak-inflated / negative when clean). Size small (0.25–0.5% risk/trade).

## Env summary
```
# backend (Railway)
REFLEX_ENABLED=1            # start the 30s detector/resolver loop
REFLEX_MODE=shadow          # shadow | live (tag on signals)
REFLEX_SYMBOL=NDX.INDX
# bot (yeni deneme/config.py)
REFLEX_ENABLED=True         # poll backend each tick
REFLEX_LIVE=False           # ⚠️ False=observe; True=real orders (after graduation)
```
