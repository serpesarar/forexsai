// Simulate the exact frontend pipeline: normalizeCandles → buildTimelineChartCandles
import { readFileSync } from 'fs';

// Inline the exact functions from the frontend
function getTimeframeMs(timeframe) {
  const rawUnit = timeframe.slice(-1);
  const unit = rawUnit.toLowerCase();
  const value = parseInt(timeframe.slice(0, -1), 10) || 1;
  if (rawUnit === 'M') return value * 30 * 24 * 60 * 60 * 1000;
  switch (unit) {
    case 'm': return value * 60 * 1000;
    case 'h': return value * 60 * 60 * 1000;
    case 'd': return value * 24 * 60 * 60 * 1000;
    default: return 60 * 60 * 1000;
  }
}

function toTimestampMs(ts) { return ts > 1e12 ? Math.floor(ts) : Math.floor(ts * 1000); }

function normalizeRemainderMs(tsMs, tfMs) { return ((tsMs % tfMs) + tfMs) % tfMs; }
function roundRemainderMs(rMs, tfMs) {
  const rounded = Math.round(rMs / 60000) * 60000;
  return rounded >= tfMs ? 0 : rounded;
}

function inferTimeframeOffsetMs(candles, tfMs) {
  if (!candles.length) return 0;
  const nonZero = candles.filter(c => (c.volume ?? 0) > 0);
  const source = nonZero.length > 0 ? nonZero : candles;
  const counts = new Map();
  source.forEach(c => {
    const r = roundRemainderMs(normalizeRemainderMs(c.timestamp, tfMs), tfMs);
    counts.set(r, (counts.get(r) ?? 0) + 1);
  });
  let bestOffset = roundRemainderMs(normalizeRemainderMs(source[0].timestamp, tfMs), tfMs);
  let bestCount = -1;
  counts.forEach((count, offset) => {
    if (count > bestCount || (count === bestCount && offset < bestOffset)) {
      bestOffset = offset; bestCount = count;
    }
  });
  return bestOffset;
}

function snapTimestamp(tsMs, tfMs, offsetMs) {
  const remainder = normalizeRemainderMs(tsMs - offsetMs, tfMs);
  return tsMs - remainder;
}

function normalizeCandles(candles, timeframe) {
  if (!candles.length) return [];
  const tfMs = getTimeframeMs(timeframe);
  const prepared = candles
    .filter(c => Number.isFinite(c.timestamp))
    .map(c => ({ ...c, timestamp: toTimestampMs(c.timestamp) }))
    .sort((a, b) => a.timestamp - b.timestamp);
  const offset = inferTimeframeOffsetMs(prepared, tfMs);
  console.log(`  Inferred offset: ${offset}ms = ${offset/60000}min`);
  
  const deduped = [];
  prepared.forEach(c => {
    const snapped = { ...c, timestamp: snapTimestamp(c.timestamp, tfMs, offset) };
    if (deduped.length > 0 && deduped[deduped.length - 1].timestamp === snapped.timestamp) {
      const prev = deduped[deduped.length - 1];
      deduped[deduped.length - 1] = { ...snapped, open: prev.open, high: Math.max(prev.high, snapped.high), low: Math.min(prev.low, snapped.low), close: snapped.close };
      return;
    }
    deduped.push(snapped);
  });
  return deduped;
}

function buildTimelineChartCandles(candles, timeframe) {
  if (!candles.length) return [];
  const stepSeconds = Math.max(60, Math.floor(getTimeframeMs(timeframe) / 1000));
  const firstActualTimestamp = Math.floor(candles[0].timestamp / 1000);
  return candles.map((c, i) => ({
    ...c,
    time: firstActualTimestamp + i * stepSeconds,
    actualTimestamp: Math.floor(c.timestamp / 1000),
  }));
}

// Fetch and process
const resp = await fetch('https://upbeat-flow-production.up.railway.app/api/data/ohlcv?symbol=NDX.INDX&timeframe=1h&limit=50');
const data = await resp.json();
const candles = data.data || [];

console.log(`\nRaw candles: ${candles.length}`);
const normalized = normalizeCandles(candles, '1h');
console.log(`After normalize: ${normalized.length}`);
const compressed = buildTimelineChartCandles(normalized, '1h');
console.log(`After compress: ${compressed.length}\n`);

// Check time spacing
console.log('Compressed candles (time values):');
for (let i = 0; i < compressed.length; i++) {
  const c = compressed[i];
  const compDate = new Date(c.time * 1000).toISOString();
  const actualDate = new Date(c.actualTimestamp * 1000).toISOString();
  const gap = i > 0 ? c.time - compressed[i-1].time : 0;
  const vol = c.volume ?? 0;
  const marker = vol === 0 ? ' [ZERO-VOL]' : '';
  console.log(`  [${String(i).padStart(2)}] comp=${compDate} actual=${actualDate} gap=${gap}s V=${vol}${marker}`);
}

// Verify all gaps are equal
const gaps = new Set();
for (let i = 1; i < compressed.length; i++) {
  gaps.add(compressed[i].time - compressed[i-1].time);
}
console.log(`\nUnique gap sizes: ${[...gaps].join(', ')} seconds`);
console.log(`All gaps equal? ${gaps.size === 1 ? 'YES' : 'NO - PROBLEM!'}`);

