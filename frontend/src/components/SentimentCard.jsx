import React from 'react';
import { ResponsiveContainer, PieChart, Pie, Cell, Tooltip } from 'recharts';
import { Smile, Meh, Frown, ShieldAlert, Activity, ArrowDownRight, Info } from 'lucide-react';

const COLORS = {
  positive: '#10B981', // Emerald
  neutral: '#64748B',  // Slate
  negative: '#EF4444', // Red
};

export default function SentimentCard({ sentimentSummary, onFilterSentiment }) {
  if (!sentimentSummary) return null;

  const {
    total = 0,
    positive_count = 0,
    positive_percentage = 0,
    neutral_count = 0,
    neutral_percentage = 0,
    negative_count = 0,
    negative_percentage = 0,
    average_compound = 0,
    spam_filtered = 0,
  } = sentimentSummary;

  const chartData = [
    { name: 'Positive', value: positive_count, percentage: positive_percentage, color: COLORS.positive },
    { name: 'Neutral', value: neutral_count, percentage: neutral_percentage, color: COLORS.neutral },
    { name: 'Negative', value: negative_count, percentage: negative_percentage, color: COLORS.negative },
  ];

  // Helper for qualitative interpretation
  const getIntensityLabel = (score) => {
    if (score >= 0.35) return { label: 'Strongly Positive', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' };
    if (score >= 0.05) return { label: 'Moderately Positive', color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30' };
    if (score <= -0.35) return { label: 'Critically Negative', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' };
    if (score <= -0.05) return { label: 'Mildly Critical', color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30' };
    return { label: 'Neutral & Balanced', color: 'text-slate-300', bg: 'bg-slate-700/20', border: 'border-slate-700/40' };
  };

  const intensity = getIntensityLabel(average_compound);

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-2xl text-xs backdrop-blur-md">
          <p className="font-bold text-white flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: data.color }}></span>
            {data.name} Sentiment
          </p>
          <p className="text-slate-300 mt-1 font-semibold">{data.value} comments ({data.percentage}%)</p>
          <p className="text-[10px] text-slate-500 mt-0.5">Click card to filter comment log</p>
        </div>
      );
    }
    return null;
  };

  const handleCardClick = (sentiment) => {
    if (onFilterSentiment) {
      onFilterSentiment(sentiment);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl flex flex-col justify-between h-full">
      {/* Header */}
      <div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Smile className="w-5 h-5 text-emerald-400" />
              <span>Audience Sentiment Breakdown</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Computed with NLTK VADER &bull; Normalized Polarity ($[-1.0, +1.0]$)
            </p>
          </div>

          {spam_filtered > 0 && (
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/20 text-amber-400 text-xs font-semibold self-start sm:self-auto">
              <ShieldAlert className="w-3.5 h-3.5" />
              <span>{spam_filtered} Spam Excluded</span>
            </div>
          )}
        </div>

        {/* Center Grid: Donut + Stat Cards */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
          {/* Donut Chart */}
          <div className="md:col-span-5 h-52 relative flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  innerRadius={65}
                  outerRadius={88}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} stroke="#0f172a" strokeWidth={2} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>

            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-black text-white">{total}</span>
              <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Comments</span>
            </div>
          </div>

          {/* Interactive Stat Tiles */}
          <div className="md:col-span-7 grid grid-cols-1 sm:grid-cols-3 gap-3">
            {/* Positive */}
            <div
              onClick={() => handleCardClick('positive')}
              className="p-3.5 rounded-2xl bg-slate-950/60 hover:bg-emerald-950/20 border border-emerald-900/40 hover:border-emerald-500/50 cursor-pointer transition-all duration-200 text-left group shadow-sm"
              title="Click to filter table by positive comments"
            >
              <div className="flex items-center justify-between text-emerald-400 mb-1">
                <span className="text-xs font-bold">Positive</span>
                <Smile className="w-4 h-4 group-hover:scale-110 transition-transform" />
              </div>
              <p className="text-2xl font-black text-white">{positive_percentage}%</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{positive_count} comments</p>
              <div className="mt-2 text-[10px] text-emerald-400/80 font-medium flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Filter</span> <ArrowDownRight className="w-3 h-3" />
              </div>
            </div>

            {/* Neutral */}
            <div
              onClick={() => handleCardClick('neutral')}
              className="p-3.5 rounded-2xl bg-slate-950/60 hover:bg-slate-800/40 border border-slate-800 hover:border-slate-700 cursor-pointer transition-all duration-200 text-left group shadow-sm"
              title="Click to filter table by neutral comments"
            >
              <div className="flex items-center justify-between text-slate-400 mb-1">
                <span className="text-xs font-bold">Neutral</span>
                <Meh className="w-4 h-4 group-hover:scale-110 transition-transform" />
              </div>
              <p className="text-2xl font-black text-white">{neutral_percentage}%</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{neutral_count} comments</p>
              <div className="mt-2 text-[10px] text-slate-400 font-medium flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Filter</span> <ArrowDownRight className="w-3 h-3" />
              </div>
            </div>

            {/* Negative */}
            <div
              onClick={() => handleCardClick('negative')}
              className="p-3.5 rounded-2xl bg-slate-950/60 hover:bg-red-950/20 border border-red-900/40 hover:border-red-500/50 cursor-pointer transition-all duration-200 text-left group shadow-sm"
              title="Click to filter table by negative comments"
            >
              <div className="flex items-center justify-between text-red-400 mb-1">
                <span className="text-xs font-bold">Negative</span>
                <Frown className="w-4 h-4 group-hover:scale-110 transition-transform" />
              </div>
              <p className="text-2xl font-black text-white">{negative_percentage}%</p>
              <p className="text-[11px] text-slate-400 mt-0.5">{negative_count} comments</p>
              <div className="mt-2 text-[10px] text-red-400/80 font-medium flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <span>Filter</span> <ArrowDownRight className="w-3 h-3" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom: Polarity Index Slider */}
      <div className="mt-6 pt-5 border-t border-slate-800/80">
        <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800/80 text-left">
          <div className="flex items-center justify-between text-xs mb-2.5">
            <span className="text-slate-300 font-bold flex items-center gap-1.5">
              <Activity className="w-4 h-4 text-indigo-400" />
              <span>Overall Polarity Index:</span>
            </span>
            <span className={`font-bold px-2.5 py-0.5 rounded-full border ${intensity.bg} ${intensity.color} ${intensity.border} text-xs`}>
              {intensity.label} ({average_compound > 0 ? `+${average_compound}` : average_compound})
            </span>
          </div>

          {/* Slider track from -1.0 to +1.0 */}
          <div className="w-full bg-slate-900 h-3 rounded-full relative overflow-hidden flex shadow-inner">
            <div className="w-1/2 h-full bg-gradient-to-r from-red-600 via-red-500 to-slate-700"></div>
            <div className="w-1/2 h-full bg-gradient-to-r from-slate-700 via-emerald-500 to-emerald-400"></div>
            
            {/* Indicator Marker */}
            <div
              className="absolute top-0 bottom-0 w-3 bg-white rounded-full shadow-lg border border-slate-900 transform -translate-x-1/2"
              style={{ left: `${Math.max(5, Math.min(95, ((average_compound + 1) / 2) * 100))}%` }}
              title={`Score: ${average_compound}`}
            />
          </div>

          <div className="flex justify-between text-[10px] text-slate-400 font-mono mt-1.5 font-medium">
            <span className="text-red-400">-1.0 (Critical)</span>
            <span className="text-slate-400">0.0 (Neutral)</span>
            <span className="text-emerald-400">+1.0 (Praise)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
