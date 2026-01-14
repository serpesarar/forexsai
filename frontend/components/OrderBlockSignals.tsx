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
    <div className="space-y-3 max-h-72 overflow-auto pr-1">
      {signals.slice(0, 4).map((signal) => (
        <div key={signal.order_block_index} className="border border-white/10 rounded-xl p-4 bg-white/5">
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm font-semibold">🚀 OB Entry #{signal.order_block_index}</p>
            <span className="text-xs px-3 py-1 bg-accent/20 text-accent rounded-full font-medium">
              {signal.entry_type}
            </span>
          </div>
          <div className="mt-4 space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-textSecondary">Entry Price</span>
              <span className="font-mono font-medium">{signal.entry_price.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-textSecondary">Stop Loss</span>
              <span className="font-mono font-medium text-danger">{signal.stop_loss.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-textSecondary">Take Profit</span>
              <span className="font-mono font-medium text-success">{signal.take_profit.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-textSecondary">Risk/Reward</span>
              <span className="font-mono font-medium">1:{signal.risk_reward.toFixed(2)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-textSecondary">Confidence</span>
              <span className="font-mono font-medium">{Math.round(signal.confidence * 100)}%</span>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button className="flex-1 px-4 py-2 rounded-full bg-success/20 text-success text-sm font-medium hover:bg-success/30 transition">
              Open Trade
            </button>
            <button className="px-4 py-2 rounded-full bg-white/10 text-sm hover:bg-white/20 transition">
              Dismiss
            </button>
          </div>
        </div>
      ))}
      {signals.length > 4 && (
        <p className="text-sm text-textSecondary text-center py-2">+{signals.length - 4} more signals</p>
      )}
    </div>
  );
}
