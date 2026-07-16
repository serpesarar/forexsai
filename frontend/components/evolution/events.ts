/**
 * Bileşenler arası mini olay köprüsü — komut paleti bir analiz başlattığında
 * AnalysisRunner'ın çıktı çekmecesini açması için (prop zinciri kurmadan).
 */

type RunListener = (runId: string) => void;
const runListeners = new Set<RunListener>();

export function emitOpenRun(runId: string): void {
  runListeners.forEach((l) => l(runId));
}

export function onOpenRun(listener: RunListener): () => void {
  runListeners.add(listener);
  return () => {
    runListeners.delete(listener);
  };
}
