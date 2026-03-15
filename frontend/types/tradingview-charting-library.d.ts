export {};

declare global {
  interface Window {
    TradingView?: {
      widget: new (options: Record<string, unknown>) => {
        remove?: () => void;
        onChartReady?: (callback: () => void) => void;
        activeChart?: () => {
          crossHairMoved?: () => {
            subscribe: (context: unknown, callback: (params: { time?: number | null; price?: number | null }) => void) => void;
            unsubscribe?: (context: unknown, callback: (params: { time?: number | null; price?: number | null }) => void) => void;
          };
          refreshMarks?: () => void;
          resetData?: () => void;
        };
        subscribe?: (event: string, callback: (...args: any[]) => void) => void;
        unsubscribe?: (event: string, callback: (...args: any[]) => void) => void;
        resetCache?: () => void;
      };
    };
  }
}
