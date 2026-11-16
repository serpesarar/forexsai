// @ts-nocheck
/**
 * NOM "Olasılık Motoru" paneli render testi. Fixture'lar canlı API'den alınmış GERÇEK yanıtlardır
 * (2026-11-16, /api/probability/nasdaq 1h 1.5x1.0 ve /calibration). Hook'lar sahte; ağ yok.
 */
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";

import prob from "./fixtures/nom_probability_1h.json";
import cal from "./fixtures/nom_calibration_1h.json";

const calls: { h: string; g: string }[] = [];
let probState: any = { data: prob, isLoading: false, error: null };

vi.mock("@/lib/api/nom", async (orig) => {
  const real: any = await orig();
  return {
    ...real,
    useNomProbability: (h: string, g: string) => {
      calls.push({ h, g });
      return probState;
    },
    useNomCalibration: () => ({ data: cal, isLoading: false, error: null }),
  };
});

import ProbabilityEnginePanel from "../components/nom/ProbabilityEnginePanel";

beforeEach(() => {
  calls.length = 0;
  probState = { data: prob, isLoading: false, error: null };
});

describe("ProbabilityEnginePanel", () => {
  it("LONG/SHORT olasılıkları, %95 bandı, NÖTR durumu ve yön uyarısını gösterir", () => {
    render(<ProbabilityEnginePanel />);
    expect(screen.getByText(prob.durum)).toBeInTheDocument();
    expect(screen.getByText(/yön sinyali değildir/)).toBeInTheDocument();
    const pct = (x: number) => `%${(100 * x).toFixed(1)}`;
    for (const side of ["long", "short"] as const) {
      const s = prob.tahmin[side];
      expect(screen.getAllByText(pct(s.p_tp_once)).length).toBeGreaterThan(0);
      expect(screen.getAllByText(pct(s.p_sl_once)).length).toBeGreaterThan(0);
    }
    expect(screen.getAllByText(/%95:/).length).toBeGreaterThanOrEqual(2);
  });

  it("Neden? bölümünde 5 SHAP faktörünü, S/R haritasını, RSI/rejim/VIX bağlamını gösterir", () => {
    render(<ProbabilityEnginePanel />);
    expect(screen.getAllByText(/en çok etkileyen 5 faktör/).length).toBe(2);
    for (const r of prob.tahmin.long.neden) expect(screen.getAllByText(r.metin).length).toBeGreaterThan(0);
    expect(screen.getByText(/Destek \/ direnç haritası/)).toBeInTheDocument();
    for (const lv of [...prob.baglam.destekler, ...prob.baglam.direncler])
      expect(screen.getAllByText(new RegExp(lv.price.toFixed(1).replace(".", "\\."))).length).toBeGreaterThan(0);
    expect(screen.getByText(/RSI ve rejim/)).toBeInTheDocument();
    expect(screen.getByText(`${prob.baglam.vix.deger} · ${prob.baglam.vix.rejim}`)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(`Model ${prob.model.surum}`))).toBeInTheDocument();
  });

  it("canlı kalibrasyon grafiğini ve mezuniyet durumunu gösterir", () => {
    const { container } = render(<ProbabilityEnginePanel />);
    expect(screen.getByText(/Canlı kalibrasyon/)).toBeInTheDocument();
    expect(screen.getAllByText(/WF bandı/).length).toBe(2);
    expect(screen.getAllByText(/mezun değil/).length).toBe(2);
    expect(container.querySelectorAll("svg line").length).toBeGreaterThan(5);
  });

  it("ufuk ve geometri seçicisi hook'u yeni hedefle çağırır", () => {
    render(<ProbabilityEnginePanel />);
    expect(calls.at(-1)).toEqual({ h: "1h", g: "1.5x1.0" });
    fireEvent.click(screen.getByRole("button", { name: "4 saat" }));
    expect(calls.at(-1)?.h).toBe("4h");
    const sel = screen.getByRole("combobox");
    fireEvent.change(sel, { target: { value: "1.0x1.5" } });
    expect(calls.at(-1)).toEqual({ h: "4h", g: "1.0x1.5" });
  });

  it("veri bayatsa tahmin göstermez, nedenini yazar", () => {
    probState = { data: { ...prob, durum: "VERI_BAYAT", tahmin: null, aciklama: "son bar 12 dk önce kapandı" }, isLoading: false, error: null };
    render(<ProbabilityEnginePanel />);
    expect(screen.getAllByText(/VERI_BAYAT|bayat|12 dk/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/en çok etkileyen 5 faktör/)).toBeNull();
  });
});
