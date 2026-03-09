# Dashboard Extensions: Advanced Charts & News Feed

## Advanced Charting

**Component**: `frontend/components/AdvancedChart.tsx`

### Usage

```tsx
import AdvancedChart from "../components/AdvancedChart";

<AdvancedChart symbol="NDX.INDX" />
```

### Features
- TradingView-quality candlestick chart via `lightweight-charts`.
- Volume histogram overlay.
- EMA(20/50/200) overlays.
- Support/resistance levels from `/api/data/ohlcv` response.
- Order block zones and entry markers from `/api/order-blocks/detect`.
- RSI + MACD indicator subcharts.
- Crosshair legend and zoom/pan enabled.
- Auto-refresh every 5s with throttled updates.

### Key Files
- `frontend/components/AdvancedChart.tsx`
- `frontend/components/CandlestickChart.tsx`
- `frontend/components/IndicatorChart.tsx`
- `frontend/components/ChartControls.tsx`
- `frontend/components/ChartLegend.tsx`
- `frontend/components/ChartOverlays.tsx`
- `frontend/components/useChartData.ts`

### Performance Notes
- `useChartData` uses memoized indicator calculations to reduce recalculation cost.
- Polling is capped at 1 update per second for candles and 15 seconds for order blocks.
- Lightweight Charts handles 60fps rendering with GPU acceleration.

### API
**Endpoint**: `GET /api/data/ohlcv`

Query params:
- `symbol`: instrument symbol (default `NDX.INDX`)
- `timeframe`: `5m | 15m | 1h | 4h | 1d`
- `limit`: 50-500

Response:
```json
{
  "symbol": "NDX.INDX",
  "timeframe": "5m",
  "data": [{ "timestamp": 1710000000000, "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 1200 }],
  "support_resistance": [{ "type": "support", "price": 21450, "label": "Support" }]
}
```

## News AI Correlation

**Frontend**: `frontend/app/news-correlation/page.tsx`

### Canonical APIs
- `GET /api/rss/news`
- `GET /api/rss/candle-news/{symbol}`
- `POST /api/news-correlation/explain-move`
- `GET /api/calendar/economic`
- `GET /api/calendar/earnings`

### Notes
- News, economic, and earnings items are surfaced through the unified News AI flow.
- Chart markers and candle correlation are sourced from the backend News AI contracts.
- Legacy `GET /api/news/feed` documentation was removed because the canonical panel no longer depends on it.

## Integration Notes

- `frontend/app/page.tsx` links users into the canonical News AI experience via the News Correlation surface.
- Zustand store additions are in `frontend/lib/store.ts` for chart + news state.
- Backend routers are registered in `backend/main.py` and `backend/routers/__init__.py`.

## Error Handling & Loading
- Skeleton loaders provide consistent loading states.
- API failures show inline messages without breaking the dashboard layout.

## Accessibility
- Buttons include `aria-label` and `aria-pressed` where appropriate.
- Content remains readable with high-contrast dark theme colors.
