import React, { useState, useEffect } from 'react';
import { 
  Youtube, Search, Sparkles, AlertCircle, ArrowRight, CheckCircle2, 
  Clipboard, X, History, TrendingUp, ShieldCheck, Cpu, Play, BarChart3
} from 'lucide-react';
import { getRecentReports } from '../services/api';
import { useToast } from './Toast';

export default function VideoInputForm({ onSubmit, isLoading, error, onSelectRecentReport }) {
  const [url, setUrl] = useState('');
  const [maxComments, setMaxComments] = useState(100);
  const [detectedId, setDetectedId] = useState(null);
  const [recentReports, setRecentReports] = useState([]);
  const [loadingRecent, setLoadingRecent] = useState(false);
  const { showToast } = useToast();

  const samplePresets = [
    {
      title: "Rick Astley - Never Gonna Give You Up",
      category: "Music & Pop Culture",
      url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      id: "dQw4w9WgXcQ",
      comments: "100+",
      badge: "Classic Benchmark"
    },
    {
      title: "Building Modern Web Applications",
      category: "Programming & Tech",
      url: "https://www.youtube.com/watch?v=aircAruvnKk",
      id: "aircAruvnKk",
      comments: "80+",
      badge: "Tech Feedback"
    },
    {
      title: "Python Machine Learning Masterclass",
      category: "AI & Data Science",
      url: "https://www.youtube.com/watch?v=7eh4d6sabA0",
      id: "7eh4d6sabA0",
      comments: "150+",
      badge: "Educational"
    }
  ];

  // Detect YouTube ID from input string
  useEffect(() => {
    const trimmed = url.trim();
    if (!trimmed) {
      setDetectedId(null);
      return;
    }

    let match = null;
    if (trimmed.length === 11 && !trimmed.includes('/') && !trimmed.includes('?')) {
      match = trimmed;
    } else if (trimmed.includes('youtu.be/')) {
      match = trimmed.split('youtu.be/')[1]?.split('?')[0]?.substring(0, 11);
    } else if (trimmed.includes('watch?v=' || trimmed.includes('watch?'))) {
      const vMatch = trimmed.match(/[?&]v=([a-zA-Z0-9_-]{11})/);
      match = vMatch ? vMatch[1] : null;
    } else if (trimmed.includes('/shorts/')) {
      match = trimmed.split('/shorts/')[1]?.split('?')[0]?.substring(0, 11);
    } else if (trimmed.includes('/embed/')) {
      match = trimmed.split('/embed/')[1]?.split('?')[0]?.substring(0, 11);
    }

    setDetectedId(match && match.length === 11 ? match : null);
  }, [url]);

  // Fetch recent reports on mount
  useEffect(() => {
    let isMounted = true;
    setLoadingRecent(true);
    getRecentReports()
      .then((data) => {
        if (isMounted) setRecentReports(data || []);
      })
      .catch((err) => {
        console.warn("Could not load recent reports:", err);
      })
      .finally(() => {
        if (isMounted) setLoadingRecent(false);
      });
    return () => { isMounted = false; };
  }, []);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        showToast("Pasted YouTube link from clipboard", "info");
      }
    } catch (e) {
      showToast("Unable to read clipboard. Please paste manually.", "info");
    }
  };

  const handleClear = () => {
    setUrl('');
    setDetectedId(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    onSubmit(url.trim(), maxComments);
  };

  const handleQuickPreset = (presetUrl) => {
    setUrl(presetUrl);
    onSubmit(presetUrl, maxComments);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-10 sm:py-16 text-center animate-in fade-in duration-300">
      {/* Decorative Glow Badge */}
      <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-gradient-to-r from-rose-500/10 via-amber-500/10 to-indigo-500/10 border border-rose-500/20 text-rose-300 text-xs font-semibold mb-6 shadow-sm">
        <Sparkles className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
        <span>NLP Polarity &bull; Spam Shield &bull; K-Means Clustering &bull; Groq LLM Strategy</span>
      </div>

      {/* Hero Title */}
      <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black tracking-tight text-white mb-4 leading-[1.15]">
        Automated Audience Sentiment &amp; <br className="hidden sm:block" />
        <span className="bg-gradient-to-r from-rose-500 via-amber-400 to-indigo-400 bg-clip-text text-transparent">
          Feedback Intelligence
        </span>
      </h1>
      <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto mb-10 leading-relaxed font-normal">
        Transform noisy comment sections into structured analytics: filter spam bots, extract audience questions, map topic clusters, and unlock high-impact video ideas.
      </p>

      {/* Main Analysis Input Card */}
      <div className="relative group">
        <div className="absolute -inset-0.5 bg-gradient-to-r from-rose-600 via-amber-500 to-indigo-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-500"></div>

        <div className="relative bg-slate-900/95 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl backdrop-blur-2xl">
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Input Row */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none text-slate-500">
                  <Youtube className="w-5 h-5 text-rose-500" />
                </div>
                <input
                  type="text"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  placeholder="Paste YouTube Video URL, Short, or ID..."
                  disabled={isLoading}
                  required
                  className="w-full pl-12 pr-20 py-3.5 rounded-2xl bg-slate-950 border border-slate-700/80 text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-rose-500/50 focus:border-rose-500 transition-all text-sm font-medium shadow-inner"
                />

                {/* Right Input Actions (Clear / Paste) */}
                <div className="absolute inset-y-0 right-0 pr-3 flex items-center gap-1.5">
                  {url ? (
                    <button
                      type="button"
                      onClick={handleClear}
                      className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                      title="Clear"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  ) : (
                    <button
                      type="button"
                      onClick={handlePaste}
                      className="flex items-center gap-1 text-[11px] font-semibold px-2 py-1 rounded-lg bg-slate-800 text-slate-300 hover:text-white hover:bg-slate-700 border border-slate-700 transition-all shadow-sm"
                      title="Paste from clipboard"
                    >
                      <Clipboard className="w-3 h-3 text-rose-400" />
                      <span>Paste</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading || !url.trim()}
                className="inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-2xl font-bold text-sm text-white bg-gradient-to-r from-rose-600 via-rose-500 to-amber-500 hover:from-rose-500 hover:to-amber-400 focus:ring-2 focus:ring-rose-500/50 shadow-lg shadow-rose-950/40 disabled:opacity-40 disabled:cursor-not-allowed transition-all duration-200 shrink-0"
              >
                {isLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>Analyzing...</span>
                  </>
                ) : (
                  <>
                    <span>Run Analysis</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>

            {/* Live Detected Video ID indicator */}
            {detectedId && (
              <div className="flex items-center gap-2 text-xs text-emerald-400 bg-emerald-950/30 border border-emerald-900/40 px-3.5 py-1.5 rounded-xl text-left animate-in fade-in">
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>
                  Valid YouTube Target Identified: <strong className="font-mono text-white">{detectedId}</strong>
                </span>
              </div>
            )}

            {/* Controls Bar: Sample Size & Presets */}
            <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-slate-800/80 text-xs">
              <div className="flex items-center gap-2.5">
                <span className="font-semibold text-slate-400">Sample Depth:</span>
                {[50, 100, 200, 500].map((size) => (
                  <button
                    key={size}
                    type="button"
                    onClick={() => setMaxComments(size)}
                    className={`px-3 py-1.5 rounded-xl font-bold transition-all text-xs ${
                      maxComments === size
                        ? 'bg-rose-500 text-white shadow-md shadow-rose-950/40 border border-rose-400/50'
                        : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
                    }`}
                  >
                    {size} Comments
                  </button>
                ))}
              </div>

              <div className="text-slate-500 text-[11px]">
                Estimated runtime: <span className="text-slate-300 font-medium">{maxComments <= 100 ? '~2 to 4 sec' : '~6 to 9 sec'}</span>
              </div>
            </div>
          </form>

          {/* Error Notification Alert */}
          {error && (
            <div className="mt-5 p-4 rounded-2xl bg-red-950/50 border border-red-800/80 text-red-300 text-xs flex items-start gap-3 text-left animate-in fade-in">
              <AlertCircle className="w-5 h-5 text-red-400 shrink-0 mt-0.5" />
              <div className="space-y-1 flex-1">
                <p className="font-bold text-red-200">Analysis Request Failed</p>
                <p className="text-red-300/90 leading-relaxed">{error}</p>
                {error.toLowerCase().includes("disabled") && (
                  <p className="text-[11px] text-amber-300/80 pt-1.5 border-t border-red-900/60">
                    💡 <strong>Creator Setting:</strong> YouTube videos categorized as &quot;Made for Kids&quot;, auto-generated Topic music tracks, or private videos have comments disabled by YouTube. Try testing with an educational tutorial, tech review, or podcast!
                  </p>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Quick 1-Click Presets Section */}
      <div className="mt-12 text-left">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Play className="w-4 h-4 text-rose-500 fill-rose-500" />
            <span>Ready-to-Test Video Presets</span>
          </h2>
          <span className="text-xs text-slate-400">Click to instantly inspect real audience data</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
          {samplePresets.map((preset, idx) => (
            <div
              key={idx}
              onClick={() => handleQuickPreset(preset.url)}
              className="group p-4 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-rose-500/40 cursor-pointer transition-all duration-200 shadow-md flex flex-col justify-between text-left"
            >
              <div>
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 group-hover:text-rose-400 group-hover:bg-rose-500/10 transition-colors">
                    {preset.category}
                  </span>
                  <span className="text-[10px] font-semibold text-slate-400">
                    {preset.comments}
                  </span>
                </div>
                <h3 className="text-xs font-bold text-white group-hover:text-rose-300 transition-colors line-clamp-2">
                  {preset.title}
                </h3>
              </div>

              <div className="mt-3 pt-3 border-t border-slate-800/60 flex items-center justify-between text-[11px] text-slate-400 group-hover:text-rose-400">
                <span className="font-mono text-[10px] text-slate-400">ID: {preset.id}</span>
                <span className="font-semibold inline-flex items-center gap-1">
                  1-Click Test <ArrowRight className="w-3 h-3" />
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Recently Analyzed Database History */}
      {recentReports && recentReports.length > 0 && (
        <div className="mt-12 text-left">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-bold text-slate-200 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" />
              <span>Previously Analyzed in this Session</span>
            </h2>
            <span className="text-xs text-slate-400">Instant load &bull; Zero API delay</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
            {recentReports.slice(0, 6).map((r) => {
              const posPct = r.sentiment_summary?.positive_percentage || 0;
              const negPct = r.sentiment_summary?.negative_percentage || 0;
              const isPositive = posPct >= 50;

              return (
                <div
                  key={r.id}
                  onClick={() => onSelectRecentReport && onSelectRecentReport(r)}
                  className="group p-3.5 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-indigo-500/40 cursor-pointer transition-all duration-200 shadow-sm flex items-center gap-3"
                >
                  {r.video?.thumbnail_url ? (
                    <img
                      src={r.video.thumbnail_url}
                      alt=""
                      className="w-14 h-14 rounded-xl object-cover border border-slate-800 shrink-0"
                    />
                  ) : (
                    <div className="w-14 h-14 rounded-xl bg-slate-800 flex items-center justify-center shrink-0">
                      <BarChart3 className="w-6 h-6 text-slate-500" />
                    </div>
                  )}

                  <div className="min-w-0 flex-1">
                    <h4 className="text-xs font-bold text-white group-hover:text-indigo-300 transition-colors truncate">
                      {r.video?.title || `Report #${r.id}`}
                    </h4>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {r.video?.channel || 'YouTube Video'}
                    </p>
                    <div className="flex items-center gap-2 mt-1.5">
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${
                        isPositive ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'
                      }`}>
                        {posPct}% Pos
                      </span>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {r.sentiment_summary?.total || 0} comments
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Feature Capabilities Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-16 text-left">
        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition-colors">
          <div className="w-8 h-8 rounded-xl bg-rose-500/10 text-rose-400 flex items-center justify-center mb-2.5">
            <TrendingUp className="w-4 h-4" />
          </div>
          <p className="text-white font-bold text-sm">VADER Polarity</p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Lexicon-based valence scoring tuned for online slang, emojis, and sentiment intensity.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition-colors">
          <div className="w-8 h-8 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-2.5">
            <ShieldCheck className="w-4 h-4" />
          </div>
          <p className="text-white font-bold text-sm">Hybrid Spam Shield</p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Eliminates WhatsApp crypto scams, promotional bots, and unsolicited referral links.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition-colors">
          <div className="w-8 h-8 rounded-xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center mb-2.5">
            <Cpu className="w-4 h-4" />
          </div>
          <p className="text-white font-bold text-sm">K-Means Clustering</p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            Unsupervised topic discovery groups viewer discussions into coherent themes.
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-slate-900/40 border border-slate-800 hover:border-slate-700 transition-colors">
          <div className="w-8 h-8 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-2.5">
            <Sparkles className="w-4 h-4" />
          </div>
          <p className="text-white font-bold text-sm">Groq LLM Strategy</p>
          <p className="text-xs text-slate-400 mt-1 leading-relaxed">
            High-speed synthesis formulates actionable next steps and 5 high-CTR suggested video titles.
          </p>
        </div>
      </div>
    </div>
  );
}
