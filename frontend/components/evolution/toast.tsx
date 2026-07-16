"use client";

/**
 * Minik toast sistemi — bağımlılıksız. Her aksiyon (çalıştır, öğret, backlog)
 * sağ altta yumuşak bir bildirim düşürür; kullanıcı "oldu mu?" diye tahmin etmez.
 */

import { AnimatePresence, motion } from "framer-motion";
import { CheckCircle2, Info, XCircle } from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";

type ToastKind = "success" | "error" | "info";
interface Toast {
  id: number;
  kind: ToastKind;
  text: string;
}

let _id = 0;
type Listener = (t: Toast) => void;
const listeners = new Set<Listener>();

/** Her yerden çağrılabilir: toast.success("Analiz başladı") */
export const toast = {
  success: (text: string) => emit("success", text),
  error: (text: string) => emit("error", text),
  info: (text: string) => emit("info", text),
};

function emit(kind: ToastKind, text: string) {
  const t = { id: ++_id, kind, text };
  listeners.forEach((l) => l(t));
}

const STYLE: Record<ToastKind, { icon: ReactNode; ring: string }> = {
  success: { icon: <CheckCircle2 size={16} className="text-emerald-400" />, ring: "ring-emerald-400/30" },
  error: { icon: <XCircle size={16} className="text-rose-400" />, ring: "ring-rose-400/30" },
  info: { icon: <Info size={16} className="text-sky-400" />, ring: "ring-sky-400/30" },
};

export function Toaster() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    const push: Listener = (t) => {
      setToasts((prev) => [...prev.slice(-3), t]);
      setTimeout(() => setToasts((prev) => prev.filter((x) => x.id !== t.id)), 4200);
    };
    listeners.add(push);
    return () => {
      listeners.delete(push);
    };
  }, []);

  return (
    <div className="pointer-events-none fixed bottom-5 right-5 z-[70] flex flex-col gap-2">
      <AnimatePresence>
        {toasts.map((t) => {
          const s = STYLE[t.kind];
          return (
            <motion.div
              key={t.id}
              initial={{ opacity: 0, x: 40, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.95 }}
              transition={{ type: "spring", damping: 24, stiffness: 300 }}
              className={`pointer-events-auto flex max-w-sm items-center gap-2.5 rounded-2xl border border-white/10 bg-[#0D1119]/95 px-4 py-3 shadow-2xl ring-1 backdrop-blur-sm ${s.ring}`}
            >
              {s.icon}
              <span className="text-[12px] leading-snug text-slate-200">{t.text}</span>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
