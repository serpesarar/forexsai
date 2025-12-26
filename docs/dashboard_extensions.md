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

## News Feed

**Component**: `frontend/components/NewsFeed.tsx`

### Usage

```tsx
import NewsFeed from "../components/NewsFeed";

<NewsFeed />
```

### Features
- Unified economic + market news feed.
- Filters for impact and category (Fed, inflation, jobs).
- Auto-refresh every 60s.
- Sentiment labels and impact badges.

### Key Files
- `frontend/components/NewsFeed.tsx`
- `frontend/components/NewsCard.tsx`
- `frontend/components/NewsFilters.tsx`
- `frontend/components/useNews.ts`

### API
**Endpoint**: `GET /api/news/feed`

Query params:
- `limit`: 5-100
- `impact`: `high | medium | low`
- `category`: `fed | inflation | jobs`

Response:
```json
{
  "total": 2,
  "news": [
    {
      "type": "economic_event",
      "id": "event_2024-05-01_Fed",
      "timestamp": "2024-05-01T12:00:00Z",
      "title": "Fed Interest Rate Decision",
      "impact": "High",
      "sentiment": "neutral",
      "actual": "5.50%",
      "expected": "5.50%",
      "previous": "5.25%",
      "market_reaction": "Muted reaction expected"
    }
  ]
}
```

## Integration Notes

- `frontend/app/page.tsx` places the chart and news feed at the top of the dashboard layout.
- Zustand store additions are in `frontend/lib/store.ts` for chart + news state.
- Backend routers are registered in `backend/main.py` and `backend/routers/__init__.py`.

## Error Handling & Loading
- Skeleton loaders provide consistent loading states.
- API failures show inline messages without breaking the dashboard layout.

## Accessibility
- Buttons include `aria-label` and `aria-pressed` where appropriate.
- Content remains readable with high-contrast dark theme colors.
