import React, { useEffect, useState } from 'react';
import { Loader2, CheckCircle, Clock, Sparkles, AlertCircle, RefreshCw, ArrowLeft, Database, ShieldAlert, Heart, Tag, Lightbulb } from 'lucide-react';

export default function JobProgress({ jobId, status, jobDetails, videoTitle, onCancel }) {
  const steps = [
    { 
      key: 'fetching',
      icon: Database,
      title: "Querying YouTube API", 
      desc: "Fetching authentic comments & author metadata via Google API v3" 
    },
    { 
      key: 'filtering',
      icon: ShieldAlert,
      title: "Preprocessing & Spam Shield", 
      desc: "Filtering crypto scams, promo links, HTML unescaping & stopword cleaning" 
    },
    { 
      key: 'sentiment',
      icon: Heart,
      title: "VADER & Hinglish Polarity Classification", 
      desc: "Computing valence compound scores across positive, neutral & negative bands" 
    },
    { 
      key: 'topics',
      icon: Tag,
      title: "Topic Modeling (K-Means)", 
      desc: "TF-IDF vectorization & Silhouette Score centroid keyword grouping" 
    },
    { 
      key: 'insights',
      icon: Lightbulb,
      title: "Synthesizing AI Insights", 
      desc: "Groq Cloud LLM generating audience takeaways & high-CTR title ideas" 
    },
  ];

  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Timer for elapsed seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const stageOrder = {
    'queued': 0,
    'fetching': 0,
    'filtering': 1,
    'sentiment': 2,
    'topics': 3,
    'insights': 4,
    'done': 5,
  };

  const activeStageKey = jobDetails?.stage || (status === 'done' ? 'done' : 'fetching');
  const activeStep = status === 'done' ? 5 : (stageOrder[activeStageKey] ?? 0);

  const progressPercentage = status === 'done' 
    ? 100 
    : (jobDetails?.progress_percent && jobDetails.progress_percent > 0 
        ? jobDetails.progress_percent 
        : Math.min(Math.round(((activeStep + 0.5) / steps.length) * 100), 95));

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m > 0 ? `${m}m ` : ''}${s}s`;
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-12 sm:py-20 text-center animate-in fade-in duration-300">
      {/* Animated Center Spinner */}
      <div className="relative w-20 h-20 mx-auto mb-6 flex items-center justify-center">
        <div className="absolute inset-0 rounded-3xl bg-gradient-to-tr from-rose-500 to-amber-500 blur-lg opacity-40 animate-pulse"></div>
        <div className="relative w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600 via-rose-500 to-amber-500 flex items-center justify-center shadow-2xl shadow-rose-900/50">
          <Loader2 className="w-8 h-8 text-white animate-spin" />
        </div>
      </div>

      <h2 className="text-2xl sm:text-3xl font-extrabold text-white mb-2 tracking-tight">
        Analyzing Audience Feedback
      </h2>
      <p className="text-sm text-slate-400 mb-6 max-w-md mx-auto truncate font-medium">
        {videoTitle ? `"${videoTitle}"` : `Executing asynchronous NLP pipeline for Job #${jobId}...`}
      </p>

      {/* Progress Bar & Live Counter */}
      <div className="max-w-md mx-auto mb-8">
        <div className="flex items-center justify-between text-xs font-semibold mb-2">
          <span className="text-rose-400 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-ping"></span>
            Pipeline Active ({progressPercentage}%)
          </span>
          <span className="text-slate-400 font-mono">Elapsed: {formatTime(elapsedSeconds)}</span>
        </div>
        <div className="w-full h-2 rounded-full bg-slate-900 border border-slate-800 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-rose-500 via-amber-400 to-indigo-500 transition-all duration-500 rounded-full"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>

        {/* Live fetched comment counter badge */}
        {jobDetails?.fetched_count !== undefined && jobDetails.fetched_count > 0 && (
          <div className="mt-2.5 inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 border border-slate-800 text-[11px] text-slate-300">
            <span>Processed:</span>
            <strong className="text-emerald-400 font-mono">
              {jobDetails.fetched_count.toLocaleString()}
            </strong>
            {jobDetails.total_estimate > 0 && (
              <>
                <span className="text-slate-500">/</span>
                <span className="text-slate-400 font-mono">
                  {jobDetails.total_estimate.toLocaleString()} comments
                </span>
              </>
            )}
          </div>
        )}
      </div>

      {/* Stepper Card */}
      <div className="bg-slate-900/95 border border-slate-800 rounded-3xl p-6 sm:p-7 text-left shadow-2xl backdrop-blur-2xl">
        <div className="space-y-4">
          {steps.map((step, idx) => {
            const isCompleted = idx < activeStep || status === 'done';
            const isCurrent = idx === activeStep && status !== 'done';

            return (
              <div
                key={step.key}
                className={`flex items-start gap-3.5 p-3 rounded-2xl transition-all duration-200 ${
                  isCurrent
                    ? 'bg-rose-500/10 border border-rose-500/20'
                    : isCompleted
                    ? 'bg-slate-950/40 border border-transparent'
                    : 'opacity-50'
                }`}
              >
                <div className="mt-0.5 shrink-0">
                  {isCompleted ? (
                    <div className="w-6 h-6 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center border border-emerald-500/40 shadow-sm">
                      <CheckCircle className="w-4 h-4" />
                    </div>
                  ) : isCurrent ? (
                    <div className="w-6 h-6 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/40 shadow-sm animate-pulse">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    </div>
                  ) : (
                    <div className="w-6 h-6 rounded-full bg-slate-800 text-slate-500 flex items-center justify-center border border-slate-700">
                      <Clock className="w-3.5 h-3.5" />
                    </div>
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className={`text-xs sm:text-sm font-bold ${
                      isCurrent ? 'text-white' : isCompleted ? 'text-slate-200' : 'text-slate-400'
                    }`}>
                      {step.title}
                    </p>
                    {isCurrent && (
                      <span className="text-[10px] font-bold uppercase tracking-wider text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded-full border border-rose-500/20">
                        In Progress
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5 leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer info & Cancel */}
        <div className="mt-6 pt-4 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-2">
            <span>Server Worker: <strong className="text-white font-mono uppercase text-[11px]">{status}</strong></span>
            {jobDetails?.stage && (
              <span className="text-slate-500">&bull; Stage: <strong className="text-slate-300 font-mono">{jobDetails.stage}</strong></span>
            )}
          </div>

          {onCancel && (
            <button
              onClick={onCancel}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-800 border border-slate-700/80 transition-all"
            >
              <ArrowLeft className="w-3 h-3" />
              <span>Cancel</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
