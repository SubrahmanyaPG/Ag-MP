import React, { useState, useEffect } from 'react';
import { X, GitCompare, ArrowRight, Trophy, ShieldAlert, Smile, Activity, Loader2, Play } from 'lucide-react';
import { getRecentReports, compareVideos } from '../services/api';
import { useToast } from './Toast';

export default function CompareVideosModal({ isOpen, onClose, defaultJobId = null }) {
  const [recentReports, setRecentReports] = useState([]);
  const [job1, setJob1] = useState(defaultJobId ? String(defaultJobId) : '');
  const [job2, setJob2] = useState('');
  const [loading, setLoading] = useState(false);
  const [comparisonData, setComparisonData] = useState(null);
  const [error, setError] = useState(null);

  const { showToast } = useToast();

  useEffect(() => {
    if (isOpen) {
      getRecentReports().then((data) => {
        setRecentReports(data || []);
        if (data && data.length >= 2) {
          if (!job1) setJob1(String(data[0].job_id));
          if (!job2) setJob2(String(data[1].job_id));
        }
      });
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleRunComparison = async () => {
    if (!job1 || !job2) {
      setError("Please select two distinct videos to compare.");
      return;
    }
    if (job1 === job2) {
      setError("Please pick two different videos for comparison.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await compareVideos(job1, job2);
      setComparisonData(data);
      showToast("Comparison analysis generated successfully!", "success");
    } catch (err) {
      setError(err.response?.data?.error || "Failed to compare videos.");
      showToast("Comparison failed. Both videos must have completed reports.", "error");
    } finally {
      setLoading(false);
    }
  };

  const v1 = comparisonData?.video1;
  const v2 = comparisonData?.video2;
  const insights = comparisonData?.comparison_insights;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 shadow-2xl text-left"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center shrink-0">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              Side-by-Side Video Comparison
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Benchmark audience sentiment, engagement weighting, and topics across any two videos
            </p>
          </div>
        </div>

        {/* Selection Row */}
        <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 mb-6 p-4 rounded-2xl bg-slate-950/80 border border-slate-800 items-end">
          <div className="sm:col-span-5">
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">
              Video 1 Target
            </label>
            <select
              value={job1}
              onChange={(e) => setJob1(e.target.value)}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="">Select video 1...</option>
              {recentReports.map((r) => (
                <option key={r.job_id} value={r.job_id}>
                  {r.video?.title?.slice(0, 45) || `Job #${r.job_id}`}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:col-span-5">
            <label className="block text-xs font-semibold text-slate-400 mb-1.5">
              Video 2 Target
            </label>
            <select
              value={job2}
              onChange={(e) => setJob2(e.target.value)}
              className="w-full py-2.5 px-3 rounded-xl bg-slate-900 border border-slate-700 text-xs text-white focus:outline-none focus:border-rose-500"
            >
              <option value="">Select video 2...</option>
              {recentReports.map((r) => (
                <option key={r.job_id} value={r.job_id}>
                  {r.video?.title?.slice(0, 45) || `Job #${r.job_id}`}
                </option>
              ))}
            </select>
          </div>

          <div className="sm:col-span-2">
            <button
              onClick={handleRunComparison}
              disabled={loading || !job1 || !job2}
              className="w-full py-2.5 px-3 rounded-xl font-bold text-xs bg-gradient-to-r from-rose-600 to-amber-500 hover:from-rose-500 hover:to-amber-400 text-white shadow-md transition-all flex items-center justify-center gap-1.5 disabled:opacity-40"
            >
              {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <GitCompare className="w-3.5 h-3.5" />}
              <span>Compare</span>
            </button>
          </div>
        </div>

        {error && (
          <div className="mb-6 p-3 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-xs">
            {error}
          </div>
        )}

        {/* Comparison Results Grid */}
        {comparisonData && v1 && v2 && (
          <div className="space-y-6 animate-in fade-in duration-300">
            {/* Cards Header Side by Side */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Video 1 Card */}
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-start gap-3">
                  {v1.video?.thumbnail_url && (
                    <img src={v1.video.thumbnail_url} alt="" className="w-20 aspect-video rounded-xl object-cover shrink-0" />
                  )}
                  <div className="min-w-0">
                    <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wider">Video 1</span>
                    <h3 className="text-xs font-bold text-white truncate mt-0.5">{v1.video?.title}</h3>
                    <p className="text-[11px] text-slate-400">{v1.video?.channel}</p>
                  </div>
                </div>
              </div>

              {/* Video 2 Card */}
              <div className="p-4 rounded-2xl bg-slate-950/70 border border-slate-800">
                <div className="flex items-start gap-3">
                  {v2.video?.thumbnail_url && (
                    <img src={v2.video.thumbnail_url} alt="" className="w-20 aspect-video rounded-xl object-cover shrink-0" />
                  )}
                  <div className="min-w-0">
                    <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider">Video 2</span>
                    <h3 className="text-xs font-bold text-white truncate mt-0.5">{v2.video?.title}</h3>
                    <p className="text-[11px] text-slate-400">{v2.video?.channel}</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Metrics Matrix Table */}
            <div className="rounded-2xl border border-slate-800 overflow-hidden bg-slate-950/60">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 uppercase text-[10px] font-bold">
                    <th className="py-3 px-4">Evaluation Metric</th>
                    <th className="py-3 px-4 text-center">Video 1</th>
                    <th className="py-3 px-4 text-center">Video 2</th>
                    <th className="py-3 px-4 text-right">Advantage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/80">
                  {/* Positive % */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Positive Sentiment Ratio</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-emerald-400">{v1.sentiment_summary?.positive_percentage}%</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-emerald-400">{v2.sentiment_summary?.positive_percentage}%</td>
                    <td className="py-3 px-4 text-right font-bold text-rose-400">
                      {v1.sentiment_summary?.positive_percentage >= v2.sentiment_summary?.positive_percentage ? 'Video 1 (+)' : 'Video 2 (+)'}
                    </td>
                  </tr>

                  {/* Polarity Compound Score */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Average Polarity Compound</td>
                    <td className="py-3 px-4 text-center font-mono font-bold">{v1.sentiment_summary?.average_compound > 0 ? `+${v1.sentiment_summary?.average_compound}` : v1.sentiment_summary?.average_compound}</td>
                    <td className="py-3 px-4 text-center font-mono font-bold">{v2.sentiment_summary?.average_compound > 0 ? `+${v2.sentiment_summary?.average_compound}` : v2.sentiment_summary?.average_compound}</td>
                    <td className="py-3 px-4 text-right font-bold text-indigo-400">
                      {v1.sentiment_summary?.average_compound >= v2.sentiment_summary?.average_compound ? 'Video 1 (+)' : 'Video 2 (+)'}
                    </td>
                  </tr>

                  {/* Like-Weighted Score */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Like-Weighted Polarity Score</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-amber-400">{v1.weighted_compound > 0 ? `+${v1.weighted_compound}` : v1.weighted_compound}</td>
                    <td className="py-3 px-4 text-center font-mono font-bold text-amber-400">{v2.weighted_compound > 0 ? `+${v2.weighted_compound}` : v2.weighted_compound}</td>
                    <td className="py-3 px-4 text-right font-bold text-amber-400">
                      {v1.weighted_compound >= v2.weighted_compound ? 'Video 1 (+)' : 'Video 2 (+)'}
                    </td>
                  </tr>

                  {/* Spam Comments Filtered */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Spam / Bot Comments Quarantined</td>
                    <td className="py-3 px-4 text-center font-mono">{v1.sentiment_summary?.spam_filtered || 0}</td>
                    <td className="py-3 px-4 text-center font-mono">{v2.sentiment_summary?.spam_filtered || 0}</td>
                    <td className="py-3 px-4 text-right font-bold text-slate-300">
                      {(v1.sentiment_summary?.spam_filtered || 0) <= (v2.sentiment_summary?.spam_filtered || 0) ? 'Video 1 (Cleaner)' : 'Video 2 (Cleaner)'}
                    </td>
                  </tr>

                  {/* Sample Volume */}
                  <tr>
                    <td className="py-3 px-4 font-semibold text-white">Sample Volume Analyzed</td>
                    <td className="py-3 px-4 text-center font-mono">{v1.sentiment_summary?.total || 0} comments</td>
                    <td className="py-3 px-4 text-center font-mono">{v2.sentiment_summary?.total || 0} comments</td>
                    <td className="py-3 px-4 text-right text-slate-400">-</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
