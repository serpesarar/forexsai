"use client";

type Signal = {
  order_block_index: number;
  entry_type: string;
  entry_price: number;
  stop_loss: number;
  take_profit: number;
  risk_reward: number;
  confidence: number;
};

type Props = {
  signals: Signal[];
};

export default function OrderBlockSignals({ signals }: Props) {
  if (!signals.length) {
    return <p className="text-sm text-textSecondary">No active entry signals.</p>;
  }

  return (
    <div className="space-y-3">
      {signals.map((signal) => (
        <div key={signal.order_block_index} className="border border-white/10 rounded-xl p-4 bg-white/5">
          <div className="flex items-center justify-between">
            <p className="font-semibold">🚀 OB ENTRY SIGNAL</p>
            <span className="text-xs text-textSecondary">#{signal.order_block_index}</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs mt-2">
            <div>Type: {signal.entry_type}</div>
            <div>Entry: {signal.entry_price.toFixed(2)}</div>
            <div>Stop: {signal.stop_loss.toFixed(2)}</div>
            <div>Target: {signal.take_profit.toFixed(2)}</div>
            <div>RR: 1:{signal.risk_reward.toFixed(2)}</div>
            <div>Conf: {Math.round(signal.confidence * 100)}%</div>
          </div>
          <div className="flex gap-2 mt-3">
            <button className="px-3 py-1 rounded-full bg-success/20 text-success text-xs">Open Trade</button>
            <button className="px-3 py-1 rounded-full bg-white/10 text-xs">Dismiss</button>
          </div>
        </div>
      ))}
    </div>
  );
}
