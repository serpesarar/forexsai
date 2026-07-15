"use client";

/**
 * LiveMarketCanvas — self-drawing candlestick market with:
 *  - random-walk candles that grow tick by tick, then commit
 *  - glowing EMA ribbon
 *  - AI "projection cone" forking from the live price
 *  - vertical scan-line sweep + rising data particles
 *  - subtle mouse parallax on the grid
 * Pure canvas / rAF, DPR-aware, pauses when tab hidden,
 * renders a single static frame when prefers-reduced-motion.
 */

import { useEffect, useRef } from "react";
import { useReducedMotion } from "framer-motion";

type Candle = { o: number; h: number; l: number; c: number };

const GREEN = "22, 199, 132";
const RED = "234, 57, 67";
const CYAN = "34, 211, 238";

function makeSeed(n: number): Candle[] {
  const out: Candle[] = [];
  let price = 100;
  for (let i = 0; i < n; i++) {
    const o = price;
    const drift = Math.sin(i / 9) * 0.35;
    const c = o + drift + (Math.random() - 0.5) * 1.7;
    const h = Math.max(o, c) + Math.random() * 0.8;
    const l = Math.min(o, c) - Math.random() * 0.8;
    out.push({ o, h, l, c });
    price = c;
  }
  return out;
}

function emaSeries(closes: number[], period: number): number[] {
  const k = 2 / (period + 1);
  const out: number[] = [];
  let prev = closes[0];
  for (const c of closes) {
    prev = c * k + prev * (1 - k);
    out.push(prev);
  }
  return out;
}

export default function LiveMarketCanvas({ className = "" }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: 0.5, y: 0.5 });
  const reduced = useReducedMotion();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const DPR = Math.min(window.devicePixelRatio || 1, 2);
    let W = 0;
    let H = 0;
    let raf = 0;
    let hidden = false;

    const resize = () => {
      W = canvas.clientWidth;
      H = canvas.clientHeight;
      canvas.width = Math.max(1, Math.floor(W * DPR));
      canvas.height = Math.max(1, Math.floor(H * DPR));
      ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    };
    resize();

    const N = 84;
    const candles = makeSeed(N);
    let live: Candle = { ...candles[candles.length - 1], o: candles[candles.length - 1].c };
    let tick = 0;
    const TICKS_PER_CANDLE = 46;

    const particles = Array.from({ length: 60 }, () => ({
      x: Math.random(),
      y: Math.random(),
      r: 0.6 + Math.random() * 1.6,
      v: 0.0005 + Math.random() * 0.0014,
      a: 0.08 + Math.random() * 0.35,
      hueGreen: Math.random() > 0.35,
    }));

    let scan = 0;

    const stepMarket = () => {
      tick++;
      const wobble = (Math.random() - 0.492) * 0.42;
      live.c += wobble;
      live.h = Math.max(live.h, live.c);
      live.l = Math.min(live.l, live.c);
      if (tick >= TICKS_PER_CANDLE) {
        tick = 0;
        candles.push({ ...live });
        candles.shift();
        live = { o: live.c, h: live.c, l: live.c, c: live.c };
      }
    };

    const drawBackdrop = (mx: number, my: number) => {
      ctx.fillStyle = "#04060c";
      ctx.fillRect(0, 0, W, H);
      const g = ctx.createRadialGradient(W * 0.5, H * 0.42, 60, W * 0.5, H * 0.42, Math.max(W, H) * 0.75);
      g.addColorStop(0, "rgba(23, 37, 64, 0.55)");
      g.addColorStop(1, "rgba(4, 6, 12, 0)");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, W, H);

      // parallax grid
      const ox = (mx - 0.5) * 24;
      const oy = (my - 0.5) * 16;
      ctx.strokeStyle = "rgba(120, 150, 210, 0.055)";
      ctx.lineWidth = 1;
      const step = 64;
      for (let x = (ox % step) - step; x < W + step; x += step) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, H);
        ctx.stroke();
      }
      for (let y = (oy % step) - step; y < H + step; y += step) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(W, y);
        ctx.stroke();
      }
    };

    const priceScale = () => {
      const all = [...candles, live];
      let lo = Infinity;
      let hi = -Infinity;
      for (const c of all) {
        if (c.l < lo) lo = c.l;
        if (c.h > hi) hi = c.h;
      }
      const pad = (hi - lo) * 0.22 || 1;
      lo -= pad;
      hi += pad;
      const top = H * 0.1;
      const bottom = H * 0.94;
      return (p: number) => bottom - ((p - lo) / (hi - lo)) * (bottom - top);
    };

    const drawCandles = (toY: (p: number) => number, colWidth: number) => {
      const all = [...candles, live];
      const bodyW = Math.max(2, colWidth * 0.55);
      all.forEach((c, i) => {
        const x = i * colWidth + colWidth / 2;
        const up = c.c >= c.o;
        const rgb = up ? GREEN : RED;
        const isRecent = i > all.length - 7;
        const alpha = 0.25 + (i / all.length) * 0.75;
        ctx.strokeStyle = `rgba(${rgb}, ${alpha * 0.85})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(x, toY(c.h));
        ctx.lineTo(x, toY(c.l));
        ctx.stroke();

        ctx.shadowBlur = isRecent ? 14 : 0;
        ctx.shadowColor = `rgba(${rgb}, 0.55)`;
        ctx.fillStyle = `rgba(${rgb}, ${alpha})`;
        const yO = toY(c.o);
        const yC = toY(c.c);
        ctx.fillRect(x - bodyW / 2, Math.min(yO, yC), bodyW, Math.max(1.4, Math.abs(yC - yO)));
        ctx.shadowBlur = 0;
      });
    };

    const drawEma = (toY: (p: number) => number, colWidth: number) => {
      const closes = [...candles.map((c) => c.c), live.c];
      const ema = emaSeries(closes, 14);
      ctx.beginPath();
      ema.forEach((v, i) => {
        const x = i * colWidth + colWidth / 2;
        const y = toY(v);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      });
      ctx.strokeStyle = `rgba(${CYAN}, 0.75)`;
      ctx.lineWidth = 1.6;
      ctx.shadowBlur = 16;
      ctx.shadowColor = `rgba(${CYAN}, 0.8)`;
      ctx.stroke();
      ctx.shadowBlur = 0;
    };

    const drawProjection = (toY: (p: number) => number, colWidth: number, t: number) => {
      const i = candles.length;
      const x0 = i * colWidth + colWidth / 2;
      const y0 = toY(live.c);
      const reach = Math.min(W - x0 - 8, colWidth * 14);
      if (reach < 24) return;
      const breathe = 1 + Math.sin(t / 900) * 0.18;
      const spread = H * 0.09 * breathe;

      const cone = ctx.createLinearGradient(x0, 0, x0 + reach, 0);
      cone.addColorStop(0, `rgba(${CYAN}, 0.16)`);
      cone.addColorStop(1, `rgba(${CYAN}, 0)`);
      ctx.fillStyle = cone;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x0 + reach, y0 - spread);
      ctx.lineTo(x0 + reach, y0 + spread);
      ctx.closePath();
      ctx.fill();

      ctx.setLineDash([5, 6]);
      ctx.lineDashOffset = -(t / 40);
      ctx.lineWidth = 1;
      ctx.strokeStyle = `rgba(${GREEN}, 0.5)`;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x0 + reach, y0 - spread);
      ctx.stroke();
      ctx.strokeStyle = `rgba(${RED}, 0.4)`;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x0 + reach, y0 + spread);
      ctx.stroke();
      ctx.setLineDash([]);

      // live price dot + halo
      const halo = 5 + Math.sin(t / 300) * 2;
      ctx.beginPath();
      ctx.arc(x0, y0, halo, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${CYAN}, 0.18)`;
      ctx.fill();
      ctx.beginPath();
      ctx.arc(x0, y0, 2.4, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${CYAN}, 0.95)`;
      ctx.shadowBlur = 12;
      ctx.shadowColor = `rgba(${CYAN}, 1)`;
      ctx.fill();
      ctx.shadowBlur = 0;
    };

    const drawScanline = () => {
      scan = (scan + 0.0012) % 1.25;
      const x = scan * W;
      const g = ctx.createLinearGradient(x - 70, 0, x + 2, 0);
      g.addColorStop(0, "rgba(34, 211, 238, 0)");
      g.addColorStop(1, "rgba(34, 211, 238, 0.07)");
      ctx.fillStyle = g;
      ctx.fillRect(x - 70, 0, 72, H);
      ctx.fillStyle = "rgba(34, 211, 238, 0.25)";
      ctx.fillRect(x, 0, 1, H);
    };

    const drawParticles = () => {
      for (const p of particles) {
        p.y -= p.v;
        if (p.y < -0.02) {
          p.y = 1.02;
          p.x = Math.random();
        }
        const rgb = p.hueGreen ? GREEN : CYAN;
        ctx.beginPath();
        ctx.arc(p.x * W, p.y * H, p.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${rgb}, ${p.a})`;
        ctx.fill();
      }
    };

    const frame = (t: number) => {
      const colWidth = W / (N + 16);
      stepMarket();
      drawBackdrop(mouseRef.current.x, mouseRef.current.y);
      const toY = priceScale();
      drawCandles(toY, colWidth);
      drawEma(toY, colWidth);
      drawProjection(toY, colWidth, t);
      drawScanline();
      drawParticles();
    };

    const loop = (t: number) => {
      if (!hidden) frame(t);
      raf = requestAnimationFrame(loop);
    };

    const onMouse = (e: MouseEvent) => {
      mouseRef.current = { x: e.clientX / window.innerWidth, y: e.clientY / window.innerHeight };
    };
    const onVisibility = () => {
      hidden = document.hidden;
    };

    window.addEventListener("resize", resize);
    window.addEventListener("mousemove", onMouse);
    document.addEventListener("visibilitychange", onVisibility);

    if (reduced) {
      // Single static frame — no motion for users who opted out.
      frame(0);
    } else {
      raf = requestAnimationFrame(loop);
    }

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouse);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [reduced]);

  return <canvas ref={canvasRef} className={`absolute inset-0 h-full w-full ${className}`} aria-hidden />;
}
