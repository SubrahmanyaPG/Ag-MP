import React, { useState } from 'react';
import { Sparkles, Copy, Check, Lightbulb, Video, Wand2, Share2, TrendingUp, CheckCircle2 } from 'lucide-react';
import { useToast } from './Toast';

export default function AiRecommendations({ recommendations, suggestedTitles = [] }) {
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [copiedAll, setCopiedAll] = useState(false);
  const { showToast } = useToast();

  const handleCopySingle = (text, index) => {
    navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    showToast(`Copied title: "${text.slice(0, 35)}..."`, 'success');
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleCopyAllTitles = () => {
    if (!suggestedTitles || suggestedTitles.length === 0) return;
    const text = suggestedTitles.map((t, i) => `${i + 1}. ${t}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopiedAll(true);
    showToast("Copied all 5 title suggestions to clipboard", 'success');
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleCopyInsights = () => {
    if (!recommendations) return;
    navigator.clipboard.writeText(recommendations);
    showToast("Copied AI recommendations to clipboard", 'success');
  };

  // Format recommendations text into structured sections
  const renderFormattedRecommendations = (text) => {
    if (!text) return <p className="text-xs text-slate-500">No recommendations generated yet.</p>;

    const lines = text.split('\n');
    return (
      <div className="space-y-3">
        {lines.map((line, idx) => {
          const trimmed = line.trim();
          if (!trimmed) return null;

          // Headers like ### or #
          if (trimmed.startsWith('#')) {
            const cleanHeader = trimmed.replace(/^#+\s*/, '');
            return (
              <h4 key={idx} className="text-sm font-extrabold text-white mt-4 first:mt-0 flex items-center gap-2 border-b border-slate-800 pb-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                {cleanHeader}
              </h4>
            );
          }

          // Bullet points like * or - or 1.
          if (trimmed.startsWith('*') || trimmed.startsWith('-') || /^\d+\./.test(trimmed)) {
            const cleanBullet = trimmed.replace(/^(\*|-|\d+\.)\s*/, '');
            return (
              <div key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 leading-relaxed pl-1">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0"></span>
                <span>{cleanBullet}</span>
              </div>
            );
          }

          // Standard paragraph
          return (
            <p key={idx} className="text-xs text-slate-300 leading-relaxed">
              {trimmed}
            </p>
          );
        })}
      </div>
    );
  };

  const titleBadges = [
    "🔥 High CTR Hook",
    "📈 Algorithmic Match",
    "💡 Educational Angle",
    "🎯 Question-Based",
    "🚀 Viral Growth"
  ];

  return (
    <div className="relative group">
      <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-rose-500 to-amber-500 rounded-3xl blur opacity-20 group-hover:opacity-30 transition duration-500"></div>

      <div className="relative bg-gradient-to-br from-slate-900/95 via-slate-900/95 to-indigo-950/40 border border-indigo-500/30 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-2xl">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-indigo-500 via-purple-500 to-rose-500 flex items-center justify-center text-white shadow-lg shadow-indigo-950 shrink-0">
              <Wand2 className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-extrabold text-white tracking-tight">
                  AI Content Strategy &amp; Title Suggestions
                </h2>
                <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 border border-indigo-500/40">
                  Groq Cloud
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Synthesized directly from sentiment polarity, viewer requests &amp; K-Means centroids
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2 self-start sm:self-auto">
            <button
              onClick={handleCopyInsights}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all shadow-sm"
              title="Copy All AI Recommendations"
            >
              <Copy className="w-3.5 h-3.5 text-indigo-400" />
              <span>Copy Strategy</span>
            </button>
          </div>
        </div>

        {/* Content Columns */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
          {/* Strategic Recommendations Column */}
          <div className="lg:col-span-7 bg-slate-950/80 border border-slate-800/80 rounded-2xl p-5 text-left flex flex-col justify-between">
            <div>
              <h3 className="text-xs font-bold text-indigo-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-amber-400" />
                <span>Actionable Takeaways for Upcoming Videos</span>
              </h3>

              <div className="pr-1 max-h-[380px] overflow-y-auto">
                {renderFormattedRecommendations(recommendations)}
              </div>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
              <span>Optimized to boost audience retention</span>
              <span className="font-semibold text-indigo-400">Groq LLM Engine</span>
            </div>
          </div>

          {/* High-CTR Suggested Titles Column */}
          <div className="lg:col-span-5 bg-slate-950/80 border border-slate-800/80 rounded-2xl p-5 text-left flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-2">
                  <Video className="w-4 h-4 text-rose-400" />
                  <span>5 Suggested Titles</span>
                </h3>

                {suggestedTitles && suggestedTitles.length > 0 && (
                  <button
                    onClick={handleCopyAllTitles}
                    className="text-[11px] font-semibold text-slate-400 hover:text-rose-400 transition-colors flex items-center gap-1"
                  >
                    {copiedAll ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copiedAll ? 'Copied' : 'Copy All'}</span>
                  </button>
                )}
              </div>

              <div className="space-y-2.5">
                {suggestedTitles && suggestedTitles.length > 0 ? (
                  suggestedTitles.map((title, idx) => (
                    <div
                      key={idx}
                      className="group p-3 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/50 flex items-start justify-between gap-3 transition-all duration-200 shadow-sm"
                    >
                      <div className="flex items-start gap-2.5 min-w-0">
                        <span className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-rose-500 group-hover:text-white transition-colors">
                          {idx + 1}
                        </span>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors leading-snug">
                            {title}
                          </p>
                          <span className="inline-block mt-1 text-[9px] font-bold uppercase tracking-wider text-slate-400">
                            {titleBadges[idx % titleBadges.length]}
                          </span>
                        </div>
                      </div>

                      <button
                        onClick={() => handleCopySingle(title, idx)}
                        title="Copy Title"
                        className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all shrink-0"
                      >
                        {copiedIndex === idx ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-slate-500 py-6 text-center">No title suggestions available.</p>
                )}
              </div>
            </div>

            <p className="text-[10px] text-slate-400 mt-4 border-t border-slate-800/80 pt-3 flex items-center justify-between">
              <span>Pro Tip: Test 2 titles with thumbnail A/B testing</span>
              <TrendingUp className="w-3 h-3 text-emerald-400" />
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
