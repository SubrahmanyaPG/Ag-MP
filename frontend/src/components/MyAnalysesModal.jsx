import React, { useState, useEffect } from 'react';
import { X, History, ExternalLink, Calendar, CheckCircle2, Loader2, ArrowRight } from 'lucide-react';
import { getMyAnalyses, getReport } from '../services/api';
import { useToast } from './Toast';

export default function MyAnalysesModal({ isOpen, onClose, onSelectReport }) {
  const [analyses, setAnalyses] = useState([]);
  const [loading, setLoading] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      getMyAnalyses()
        .then((data) => setAnalyses(data || []))
        .catch((err) => {
          console.warn("Error fetching user analyses:", err);
          showToast("Sign in with JWT to view your saved analyses.", "info");
        })
        .finally(() => setLoading(false));
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleOpenJob = async (job) => {
    try {
      const report = await getReport(job.id);
      onSelectReport(report);
      onClose();
    } catch (e) {
      showToast("Could not load report for this job.", "error");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-in fade-in duration-200">
      <div 
        className="relative w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl text-left"
        onClick={(e) => e.stopPropagation()}
      >
        <button
          onClick={onClose}
          className="absolute top-5 right-5 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center shrink-0">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xl font-bold text-white tracking-tight">
              My Saved Analyses
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              Securely associated with your authenticated JWT account
            </p>
          </div>
        </div>

        {loading ? (
          <div className="py-16 text-center text-slate-400 flex items-center justify-center gap-2">
            <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
            <span className="text-xs">Loading your saved analyses...</span>
          </div>
        ) : analyses.length > 0 ? (
          <div className="space-y-3">
            {analyses.map((job) => (
              <div
                key={job.id}
                onClick={() => handleOpenJob(job)}
                className="group p-4 rounded-2xl bg-slate-950/70 hover:bg-slate-950 border border-slate-800 hover:border-rose-500/40 cursor-pointer transition-all flex items-center justify-between gap-4"
              >
                <div className="flex items-center gap-3.5 min-w-0">
                  {job.video?.thumbnail_url ? (
                    <img src={job.video.thumbnail_url} alt="" className="w-16 aspect-video rounded-xl object-cover shrink-0" />
                  ) : (
                    <div className="w-16 aspect-video rounded-xl bg-slate-800 shrink-0" />
                  )}

                  <div className="min-w-0">
                    <h3 className="text-xs font-bold text-white group-hover:text-rose-300 transition-colors truncate">
                      {job.video?.title || `Job #${job.id}`}
                    </h3>
                    <p className="text-[11px] text-slate-400 truncate mt-0.5">
                      {job.video?.channel || 'YouTube Video'} &bull; <span className="font-mono">{job.video?.youtube_video_id}</span>
                    </p>
                    <p className="text-[10px] text-slate-500 mt-1 flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>{job.created_at ? job.created_at.slice(0, 10) : 'Recent'}</span>
                    </p>
                  </div>
                </div>

                <div className="shrink-0 text-right">
                  <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-400 group-hover:translate-x-0.5 transition-transform">
                    <span>Inspect</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="py-14 text-center text-slate-500 text-xs">
            <p className="font-semibold text-slate-400">No saved analyses found for this account.</p>
            <p className="mt-1">When logged in, your analyzed videos will automatically save here.</p>
          </div>
        )}
      </div>
    </div>
  );
}
