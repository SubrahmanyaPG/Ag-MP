import React, { useState, useEffect, useMemo } from 'react';
import { 
  X, GitCompare, ArrowRight, Trophy, ShieldAlert, Smile, Activity, 
  Loader2, Play, Sparkles, Check, CheckCircle2, TrendingUp, TrendingDown,
  Layers, MessageSquare, Tag, Zap, Search
} from 'lucide-react';
import { getUserJobs, compareVideos, getCompareInsights } from '../services/api';
import { useToast } from './Toast';

export default function CompareVideosModal({ isOpen, onClose, defaultJobId = null }) {
  const [userJobs, setUserJobs] = useState([]);
  const [searchA, setSearchA] = useState('');
  const [searchB, setSearchB] = useState('');
  const [job1, setJob1] = useState(defaultJobId ? String(defaultJobId) : '');
  const [job2, setJob2] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingInsights, setLoadingInsights] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [aiTakeaways, setAiTakeaways] = useState([]);
  const [error, setError] = useState(null);

  const { showToast } = useToast();

  useEffect(() => {
    if (isOpen) {
      getUserJobs().then((data) => {
        const jobsList = Array.isArray(data) ? data : (data?.results || []);
        setUserJobs(jobsList);
        if (jobsList.length >= 2) {
          if (!job1) setJob1(String(jobsList[0].job_id || jobsList[0].id));
          if (!job2) setJob2(String(jobsList[1].job_id || jobsList[1].id));
        } else if (jobsList.length === 1 && !job1) {
          setJob1(String(jobsList[0].job_id || jobsList[0].id));
        }
      }).catch((err) => {
        console.warn("Could not load user jobs:", err);
      });
    }
  }, [isOpen]);

  useEffect(() => {
    if (defaultJobId) {
      setJob1(String(defaultJobId));
    }
  }, [defaultJobId]);

  if (!isOpen) return null;

  const filteredJobsA = userJobs.filter((j) => 
    (j.video_title || '').toLowerCase().includes(searchA.toLowerCase())
  );
  const filteredJobsB = userJobs.filter((j) => 
    (j.video_title || '').toLowerCase().includes(searchB.toLowerCase())
  );

  const handleRunComparison = async () => {
    if (!job1 || !job2) {
      setError("Please select two distinct videos to compare.");
      return;
    }
    if (job1 === job2) {
      setError("Cannot compare a video with itself. Please select two different videos.");
      return;
    }

    setLoading(true);
    setError(null);
    setAiTakeaways([]);
    try {
      const data = await compareVideos(job1, job2);
      setComparisonData(data);
      showToast("Comparative benchmarking generated!", "success");
    } catch (err) {
      const msg = err.response?.data?.error || "Failed to compare videos.";
      setError(msg);
      showToast(msg, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateAiInsights = async () => {
    if (!job1 || !job2) return;
    setLoadingInsights(true);
    try {
      const res = await getCompareInsights(job1, job2);
      setAiTakeaways(res.insights || []);
      showToast("Comparative AI insights generated!", "success");
    } catch (err) {
      showToast("Failed to generate AI insights. Using heuristic takeaways.", "info");
    } finally {
      setLoadingInsights(false);
    }
  };

  const vA = comparisonData?.video_a || comparisonData?.video1;
  const vB = comparisonData?.video_b || comparisonData?.video2;
  const deltas = comparisonData?.deltas || {};
  const sharedKeywords = comparisonData?.shared_keywords || [];
  const jaccard = comparisonData?.jaccard_similarity ?? 0.0;

  // Delta Badge helper
  const renderDeltaBadge = (delta, invertGood = false, isPercent = true) => {
    if (delta === undefined || delta === null || isNaN(delta)) return null;
    const isPositive = delta > 0;
    const isZero = delta === 0;

    // By default, higher is good (e.g. positive sentiment, compound score).
    // For negative sentiment and spam, lower is good (invertGood = true).
    let isFavorable = isPositive;
    if (invertGood) isFavorable = !isPositive;

    const colorClass = isZero 
      ? 'bg-slate-800 text-slate-300 border-slate-700' 
      : isFavorable 
      ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' 
      : 'bg-rose-500/15 text-rose-400 border-rose-500/30';

    const sign = isPositive ? '+' : '';
    const formattedVal = `${sign}${delta}${isPercent ? '%' : ''}`;

    return (
      <span className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-[10px] font-bold border ${colorClass}`}>
        {isPositive && <TrendingUp className="w-2.5 h-2.5" />}
        {!isPositive && !isZero && <TrendingDown className="w-2.5 h-2.5" />}
        <span>{formattedVal}</span>
      </span>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-5xl max-h-[92vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3.5 mb-6">
          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-rose-600 via-indigo-600 to-amber-500 text-white flex items-center justify-center shadow-lg shadow-indigo-950/40 shrink-0">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-black text-white tracking-tight">
                Side-by-Side Video Benchmarking
              </h2>
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-indigo-500/15 text-indigo-400 border border-indigo-500/20">
                Comparative Analytics
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Compare audience sentiment, like-weighted compound scores, keyword overlap, and viewer requests across two videos.
            </p>
          </div>
        </div>

        {/* Video Picker Selectors */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4 mb-6 p-5 rounded-2xl bg-slate-950/80 border border-slate-800 items-end">
          {/* Video A Picker */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="block text-xs font-bold text-rose-400 uppercase tracking-wider">
              Video Target A
            </label>
            <select
              value={job1}
              onChange={(e) => setJob1(e.target.value)}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="">Choose first video...</option>
              {filteredJobsA.map((j) => (
                <option key={j.id || j.job_id} value={j.id || j.job_id}>
                  {j.video_title?.slice(0, 50) || `Job #${j.id}`} ({j.positive_percentage}% Pos)
                </option>
              ))}
            </select>
          </div>

          {/* Video B Picker */}
          <div className="md:col-span-5 space-y-1.5">
            <label className="block text-xs font-bold text-indigo-400 uppercase tracking-wider">
              Video Target B
            </label>
            <select
              value={job2}
              onChange={(e) => setJob2(e.target.value)}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="">Choose second video...</option>
              {filteredJobsB.map((j) => (
                <option key={j.id || j.job_id} value={j.id || j.job_id}>
                  {j.video_title?.slice(0, 50) || `Job #${j.id}`} ({j.positive_percentage}% Pos)
                </option>
              ))}
            </select>
          </div>

          {/* Compare Button */}
          <div className="md:col-span-2">
            <button
              onClick={handleRunComparison}
              disabled={loading || !job1 || !job2}
              className="w-full py-2.5 px-4 rounded-xl font-bold text-xs bg-gradient-to-r from-rose-600 via-rose-500 to-amber-500 hover:from-rose-500 hover:to-amber-400 text-white shadow-lg shadow-rose-950/40 transition-all flex items-center justify-center gap-1.5 disabled:opacity-40"
            >
              {loading ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Comparing...</span>
                </>
              ) : (
                <>
                  <GitCompare className="w-3.5 h-3.5" />
                  <span>Compare</span>
                </>
              )}
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-2xl bg-red-950/40 border border-red-800 text-red-300 text-xs">
            {error}
          </div>
        )}

        {/* Comparative Results View */}
        {comparisonData && vA && vB && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Side-by-Side Video Header Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Card Video A */}
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-rose-500/20 relative overflow-hidden">
                <div className="flex items-start gap-3.5">
                  {vA.video?.thumbnail_url && (
                    <img 
                      src={vA.video.thumbnail_url} 
                      alt="" 
                      className="w-24 aspect-video rounded-xl object-cover shrink-0 shadow-md" 
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">
                      Video A
                    </span>
                    <h3 className="text-sm font-bold text-white truncate mt-0.5">
                      {vA.video?.title}
                    </h3>
                    <p className="text-xs text-slate-400 truncate">
                      {vA.video?.channel || 'YouTube Creator'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Card Video B */}
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-indigo-500/20 relative overflow-hidden">
                <div className="flex items-start gap-3.5">
                  {vB.video?.thumbnail_url && (
                    <img 
                      src={vB.video.thumbnail_url} 
                      alt="" 
                      className="w-24 aspect-video rounded-xl object-cover shrink-0 shadow-md" 
                    />
                  )}
                  <div className="min-w-0 flex-1">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">
                      Video B
                    </span>
                    <h3 className="text-sm font-bold text-white truncate mt-0.5">
                      {vB.video?.title}
                    </h3>
                    <p className="text-xs text-slate-400 truncate">
                      {vB.video?.channel || 'YouTube Creator'}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Grouped Bar Chart: Pos / Neu / Neg Sentiment */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-4">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Smile className="w-4 h-4 text-emerald-400" />
                  <span>Sentiment Distribution Benchmark</span>
                </h4>
                <div className="flex items-center gap-4 text-[11px] font-semibold">
                  <span className="flex items-center gap-1.5 text-rose-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-500"></span> Video A
                  </span>
                  <span className="flex items-center gap-1.5 text-indigo-400">
                    <span className="w-2.5 h-2.5 rounded-full bg-indigo-500"></span> Video B
                  </span>
                </div>
              </div>

              {/* Visual Bars for Pos, Neu, Neg */}
              <div className="space-y-3 pt-2">
                {/* Positive Sentiment Bar */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-emerald-400">Positive Sentiment</span>
                    <span className="text-slate-400 font-mono">
                      A: {vA.positive_percentage}% vs B: {vB.positive_percentage}%
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 h-3 rounded-full bg-slate-900 overflow-hidden p-0.5">
                    <div 
                      className="h-full bg-gradient-to-r from-rose-600 to-rose-400 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, vA.positive_percentage)}%` }}
                    />
                    <div 
                      className="h-full bg-gradient-to-r from-indigo-600 to-indigo-400 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, vB.positive_percentage)}%` }}
                    />
                  </div>
                </div>

                {/* Neutral Sentiment Bar */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-amber-400">Neutral Sentiment</span>
                    <span className="text-slate-400 font-mono">
                      A: {vA.neutral_percentage}% vs B: {vB.neutral_percentage}%
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 h-3 rounded-full bg-slate-900 overflow-hidden p-0.5">
                    <div 
                      className="h-full bg-amber-500/80 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, vA.neutral_percentage)}%` }}
                    />
                    <div 
                      className="h-full bg-amber-400/50 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, vB.neutral_percentage)}%` }}
                    />
                  </div>
                </div>

                {/* Negative Sentiment Bar */}
                <div>
                  <div className="flex justify-between text-xs font-semibold mb-1">
                    <span className="text-rose-400">Negative Sentiment</span>
                    <span className="text-slate-400 font-mono">
                      A: {vA.negative_percentage}% vs B: {vB.negative_percentage}%
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 h-3 rounded-full bg-slate-900 overflow-hidden p-0.5">
                    <div 
                      className="h-full bg-red-600 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, vA.negative_percentage)}%` }}
                    />
                    <div 
                      className="h-full bg-red-400/60 rounded-full transition-all duration-500" 
                      style={{ width: `${Math.min(100, vB.negative_percentage)}%` }}
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Metric Comparison Table with Delta Badges */}
            <div className="rounded-2xl border border-slate-800 overflow-hidden bg-slate-950/70">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase text-[10px] font-bold">
                    <th className="py-3 px-4">Evaluation Metric</th>
                    <th className="py-3 px-4 text-center text-rose-400">Video A</th>
                    <th className="py-3 px-4 text-center text-indigo-400">Video B</th>
                    <th className="py-3 px-4 text-right">Delta (A vs B)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {/* Positive % */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Positive Sentiment Ratio</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-emerald-400">{vA.positive_percentage}%</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-emerald-400">{vB.positive_percentage}%</td>
                    <td className="py-3 px-4 text-right">
                      {renderDeltaBadge(deltas.positive_percentage, false, true)}
                    </td>
                  </tr>

                  {/* Neutral % */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Neutral Sentiment Ratio</td>
                    <td className="py-3 px-4 text-center font-mono text-amber-400">{vA.neutral_percentage}%</td>
                    <td className="py-3 px-4 text-center font-mono text-amber-400">{vB.neutral_percentage}%</td>
                    <td className="py-3 px-4 text-right">
                      {renderDeltaBadge(deltas.neutral_percentage, false, true)}
                    </td>
                  </tr>

                  {/* Negative % */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Negative Sentiment Ratio</td>
                    <td className="py-3 px-4 text-center font-mono text-rose-400">{vA.negative_percentage}%</td>
                    <td className="py-3 px-4 text-center font-mono text-rose-400">{vB.negative_percentage}%</td>
                    <td className="py-3 px-4 text-right">
                      {renderDeltaBadge(deltas.negative_percentage, true, true)}
                    </td>
                  </tr>

                  {/* Average Compound */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Average Compound Score</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-white">
                      {vA.average_compound > 0 ? `+${vA.average_compound}` : vA.average_compound}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-white">
                      {vB.average_compound > 0 ? `+${vB.average_compound}` : vB.average_compound}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {renderDeltaBadge(deltas.average_compound, false, false)}
                    </td>
                  </tr>

                  {/* Like-Weighted Polarity Score */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Like-Weighted Polarity Score</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-amber-400">
                      {vA.weighted_compound > 0 ? `+${vA.weighted_compound}` : vA.weighted_compound}
                    </td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-amber-400">
                      {vB.weighted_compound > 0 ? `+${vB.weighted_compound}` : vB.weighted_compound}
                    </td>
                    <td className="py-3 px-4 text-right">
                      {renderDeltaBadge(deltas.weighted_compound, false, false)}
                    </td>
                  </tr>

                  {/* Spam Rate */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Spam / Bot Filtering Rate</td>
                    <td className="py-3 px-4 text-center font-mono text-slate-300">{vA.spam_rate}%</td>
                    <td className="py-3 px-4 text-center font-mono text-slate-300">{vB.spam_rate}%</td>
                    <td className="py-3 px-4 text-right">
                      {renderDeltaBadge(deltas.spam_rate, true, true)}
                    </td>
                  </tr>

                  {/* Comments Analyzed */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Sample Comments Analyzed</td>
                    <td className="py-3 px-4 text-center font-mono">{vA.comments_analyzed?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-center font-mono">{vB.comments_analyzed?.toLocaleString()}</td>
                    <td className="py-3 px-4 text-right text-slate-400 font-mono">
                      {deltas.comments_analyzed > 0 ? `+${deltas.comments_analyzed}` : deltas.comments_analyzed}
                    </td>
                  </tr>

                  {/* Viewer Requests Count */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Actionable Viewer Requests</td>
                    <td className="py-3 px-4 text-center font-mono">{vA.viewer_requests_count}</td>
                    <td className="py-3 px-4 text-center font-mono">{vB.viewer_requests_count}</td>
                    <td className="py-3 px-4 text-right text-slate-400 font-mono">
                      {deltas.viewer_requests_count > 0 ? `+${deltas.viewer_requests_count}` : deltas.viewer_requests_count}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Keyword Overlap & Jaccard Similarity */}
            <div className="p-5 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                  <Tag className="w-4 h-4 text-indigo-400" />
                  <span>Keyword Overlap &amp; Jaccard Similarity</span>
                </h4>
                <span className="text-xs font-mono font-bold text-indigo-300 px-2.5 py-1 rounded-xl bg-indigo-500/15 border border-indigo-500/30">
                  Jaccard Score: {jaccard} ({Math.round(jaccard * 100)}% match)
                </span>
              </div>

              {/* Shared Keywords */}
              <div>
                <p className="text-[11px] font-semibold text-slate-400 mb-1.5">
                  Shared Keywords Across Both Audiences:
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {sharedKeywords && sharedKeywords.length > 0 ? (
                    sharedKeywords.map((kw, i) => (
                      <span key={i} className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 text-xs font-medium">
                        <Check className="w-3 h-3 text-indigo-400" />
                        <span>{kw}</span>
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 italic">No exact keyword overlap detected between top terms.</span>
                  )}
                </div>
              </div>

              {/* Unique Keywords Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2 border-t border-slate-800/80">
                <div>
                  <p className="text-[11px] font-semibold text-rose-400 mb-1.5">
                    Distinct to Video A:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {vA.unique_keywords && vA.unique_keywords.length > 0 ? (
                      vA.unique_keywords.map((kw, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-lg bg-rose-500/10 text-rose-300 border border-rose-500/20 text-xs">
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">None</span>
                    )}
                  </div>
                </div>

                <div>
                  <p className="text-[11px] font-semibold text-sky-400 mb-1.5">
                    Distinct to Video B:
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {vB.unique_keywords && vB.unique_keywords.length > 0 ? (
                      vB.unique_keywords.map((kw, i) => (
                        <span key={i} className="px-2 py-0.5 rounded-lg bg-sky-500/10 text-sky-300 border border-sky-500/20 text-xs">
                          {kw}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">None</span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Viewer Requests Side by Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
                <h5 className="text-xs font-bold text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Video A Top Requests</span>
                </h5>
                <div className="space-y-1.5">
                  {vA.viewer_requests && vA.viewer_requests.length > 0 ? (
                    vA.viewer_requests.map((req, idx) => (
                      <p key={idx} className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
                        &quot;{typeof req === 'object' ? (req.request || req.text) : req}&quot;
                      </p>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 italic">No specific audience requests detected.</p>
                  )}
                </div>
              </div>

              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800 space-y-2">
                <h5 className="text-xs font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1.5">
                  <MessageSquare className="w-3.5 h-3.5" />
                  <span>Video B Top Requests</span>
                </h5>
                <div className="space-y-1.5">
                  {vB.viewer_requests && vB.viewer_requests.length > 0 ? (
                    vB.viewer_requests.map((req, idx) => (
                      <p key={idx} className="text-xs text-slate-300 bg-slate-900/80 p-2 rounded-xl border border-slate-800">
                        &quot;{typeof req === 'object' ? (req.request || req.text) : req}&quot;
                      </p>
                    ))
                  ) : (
                    <p className="text-xs text-slate-500 italic">No specific audience requests detected.</p>
                  )}
                </div>
              </div>
            </div>

            {/* AI Comparative Insights Section */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950/30 border border-indigo-500/20 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <h4 className="text-xs font-bold text-white uppercase tracking-wider">
                    Executive Comparative Takeaways
                  </h4>
                </div>

                <button
                  onClick={handleGenerateAiInsights}
                  disabled={loadingInsights}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-bold text-xs bg-indigo-600 hover:bg-indigo-500 text-white transition-all shadow-sm disabled:opacity-50"
                >
                  {loadingInsights ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Synthesizing...</span>
                    </>
                  ) : (
                    <>
                      <Zap className="w-3.5 h-3.5 text-amber-300" />
                      <span>{aiTakeaways.length > 0 ? "Regenerate Takeaways" : "Generate AI Takeaways"}</span>
                    </>
                  )}
                </button>
              </div>

              {aiTakeaways.length > 0 ? (
                <ul className="space-y-2 pt-2">
                  {aiTakeaways.map((takeaway, idx) => (
                    <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-300 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
                      <div className="w-4 h-4 rounded-full bg-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 font-bold text-[10px]">
                        {idx + 1}
                      </div>
                      <span className="leading-relaxed">{takeaway}</span>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-xs text-slate-400 pt-1">
                  Click <strong>&quot;Generate AI Takeaways&quot;</strong> to call the Groq model for strategic audience retention analysis.
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
