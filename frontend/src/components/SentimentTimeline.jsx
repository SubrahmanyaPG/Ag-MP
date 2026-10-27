import React from 'react';
import { 
  ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Area, AreaChart 
} from 'recharts';
import { TrendingUp, Calendar, Zap, MessageSquare, Award } from 'lucide-react';

export default function SentimentTimeline({ timeline = [], weightedCompound = 0.0 }) {
  if (!timeline || timeline.length === 0) {
    return null;
  }

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 p-3.5 rounded-2xl shadow-2xl text-xs backdrop-blur-xl text-left">
          <p className="font-bold text-white flex items-center gap-1.5 mb-1.5">
            <Calendar className="w-3.5 h-3.5 text-rose-400" />
            <span>Date: {data.date}</span>
          </p>
          <div className="space-y-1">
            <p className="text-emerald-400 font-semibold">
              Avg Polarity: <strong className="font-mono">{data.avg_sentiment > 0 ? `+${data.avg_sentiment}` : data.avg_sentiment}</strong>
            </p>
            <p className="text-slate-300">
              Comment Volume: <strong className="text-white font-mono">{data.volume}</strong> comments
            </p>
            <p className="text-slate-400 text-[11px] pt-1 border-t border-slate-800">
              Positive: {data.pos_pct}% &bull; Negative: {data.neg_pct}%
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-rose-500" />
            <span>Sentiment Trajectory Over Time</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Chronological audience reaction tracking based on comment timestamps
          </p>
        </div>

        {/* Engagement Weighting Badge */}
        {weightedCompound !== undefined && (
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-semibold self-start sm:self-auto">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>
              Like-Weighted Score: <strong className="font-mono text-white">{weightedCompound > 0 ? `+${weightedCompound}` : weightedCompound}</strong>
            </span>
          </div>
        )}
      </div>

      {/* Main Chart */}
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={timeline} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
            <XAxis 
              dataKey="date" 
              stroke="#64748b" 
              fontSize={11}
              tickLine={false}
              tickFormatter={(d) => d.slice(5)} // Show MM-DD
            />
            <YAxis 
              stroke="#64748b" 
              fontSize={11}
              domain={[-1, 1]}
              ticks={[-1.0, -0.5, 0, 0.5, 1.0]}
              tickLine={false}
            />
            <Tooltip content={<CustomTooltip />} />
            <Area
              type="monotone"
              dataKey="avg_sentiment"
              stroke="#f43f5e"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#sentimentGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      {/* Footer Snapshot */}
      <div className="mt-4 pt-4 border-t border-slate-800/80 flex flex-wrap items-center justify-between text-xs text-slate-400 gap-2">
        <span>Timeline spans {timeline.length} distinct publishing date points</span>
        <span className="text-[11px] text-slate-500">
          Tip: Drops in polarity correlate with controversial topics or technical audio/visual glitches.
        </span>
      </div>
    </div>
  );
}
