import React from 'react';
import { Target, Mic, Monitor, Zap, Smile, HelpCircle, Frown, Sparkles, Compass } from 'lucide-react';

export default function AspectRadarCard({ aspectSentiment = {}, emotionBreakdown = {} }) {
  const aspectConfig = [
    { key: 'content', label: 'Content & Explanation', icon: Target, color: 'text-indigo-400', bg: 'bg-indigo-500/10' },
    { key: 'audio', label: 'Audio & Sound Quality', icon: Mic, color: 'text-rose-400', bg: 'bg-rose-500/10' },
    { key: 'visuals', label: 'Visuals & Editing', icon: Monitor, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { key: 'pacing', label: 'Pacing & Video Length', icon: Zap, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
  ];

  const emotionEmojis = {
    joy: { icon: Smile, label: 'Joy & Praise', color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    inquiry: { icon: HelpCircle, label: 'Questions & Curiosity', color: 'text-amber-400', bg: 'bg-amber-500/10' },
    frustration: { icon: Frown, label: 'Critique & Frustration', color: 'text-red-400', bg: 'bg-red-500/10' },
    surprise: { icon: Sparkles, label: 'Awe & Surprise', color: 'text-purple-400', bg: 'bg-purple-500/10' },
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl flex flex-col justify-between h-full">
      {/* Aspect Breakdown */}
      <div>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Compass className="w-5 h-5 text-indigo-400" />
              <span>Aspect-Based Audience Sentiment</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Targeted feedback breakdown across production dimensions
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
          {aspectConfig.map((item) => {
            const data = aspectSentiment[item.key] || { count: 0, average_score: 0.0, sentiment: 'neutral' };
            const Icon = item.icon;
            const isPos = data.average_score >= 0.05;
            const isNeg = data.average_score <= -0.05;

            return (
              <div
                key={item.key}
                className="p-3.5 rounded-2xl bg-slate-950/70 border border-slate-800 flex items-center justify-between text-left"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-8 h-8 rounded-xl ${item.bg} ${item.color} flex items-center justify-center shrink-0`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white leading-tight">{item.label}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">{data.count} mentions</p>
                  </div>
                </div>

                <div className="text-right">
                  <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded-md ${
                    isPos ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
                    isNeg ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                    'bg-slate-800 text-slate-400'
                  }`}>
                    {data.average_score > 0 ? `+${data.average_score}` : data.average_score}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Emotion Distribution */}
      <div className="pt-5 border-t border-slate-800/80">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Emotion Polarity Profile
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
          {Object.entries(emotionEmojis).map(([key, config]) => {
            const data = emotionBreakdown[key] || { count: 0, percentage: 0.0 };
            const Icon = config.icon;

            return (
              <div
                key={key}
                className="p-3 rounded-2xl bg-slate-950/60 border border-slate-800 text-left flex flex-col justify-between"
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className={`text-[11px] font-bold ${config.color}`}>{config.label}</span>
                  <Icon className="w-3.5 h-3.5 text-slate-400" />
                </div>
                <p className="text-xl font-black text-white">{data.percentage}%</p>
                <p className="text-[10px] text-slate-400 mt-0.5">{data.count} comments</p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
