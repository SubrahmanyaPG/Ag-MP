import React, { useState, useEffect, useRef } from 'react';
import Navbar from './components/Navbar';
import VideoInputForm from './components/VideoInputForm';
import JobProgress from './components/JobProgress';
import SentimentCard from './components/SentimentCard';
import TopicsChart from './components/TopicsChart';
import SentimentTimeline from './components/SentimentTimeline';
import AspectRadarCard from './components/AspectRadarCard';
import CompareVideosModal from './components/CompareVideosModal';
import MyAnalysesModal from './components/MyAnalysesModal';
import AiRecommendations from './components/AiRecommendations';
import CommentsTable from './components/CommentsTable';
import { ToastProvider, useToast } from './components/Toast';
import { analyzeVideo, getJobStatus, getReport, getExportUrl } from './services/api';
import { 
  Youtube, Download, ExternalLink, RefreshCw, BarChart2, ShieldCheck, 
  CheckCircle2, FileText, Copy, Smile, AlertTriangle, ArrowRight, Activity 
} from 'lucide-react';

function DashboardContent() {
  const [viewState, setViewState] = useState('home'); // 'home' | 'analyzing' | 'dashboard'
  const [activeJobId, setActiveJobId] = useState(null);
  const [jobStatus, setJobStatus] = useState('pending');
  const [reportData, setReportData] = useState(null);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Modals for v2.0 features
  const [isCompareModalOpen, setIsCompareModalOpen] = useState(false);
  const [isMyAnalysesModalOpen, setIsMyAnalysesModalOpen] = useState(false);

  // Cross-component interaction filters
  const [activeSentimentFilter, setActiveSentimentFilter] = useState('');
  const [activeSearchQuery, setActiveSearchQuery] = useState('');

  const commentsSectionRef = useRef(null);
  const { showToast } = useToast();

  // Poll job status during 'analyzing' view
  useEffect(() => {
    let intervalId = null;

    if (viewState === 'analyzing' && activeJobId) {
      intervalId = setInterval(async () => {
        try {
          const statusRes = await getJobStatus(activeJobId);
          setJobStatus(statusRes.status);

          if (statusRes.status === 'done') {
            clearInterval(intervalId);
            const reportRes = await getReport(activeJobId);
            setReportData(reportRes);
            setViewState('dashboard');
            showToast("Analysis complete! Dashboard is ready.", "success", "NLP Processing Complete");
          } else if (statusRes.status === 'failed') {
            clearInterval(intervalId);
            const errDetail = statusRes.error_message || "Analysis failed. Please verify the video has public comments.";
            setError(errDetail);
            setViewState('home');
            showToast(errDetail, "error", "Analysis Failed");
          }
        } catch (err) {
          console.error("Polling error:", err);
        }
      }, 1500);
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [viewState, activeJobId]);

  const handleStartAnalysis = async (url, maxComments) => {
    setError(null);
    setIsSubmitting(true);
    try {
      const res = await analyzeVideo(url, maxComments);
      setActiveJobId(res.job_id);
      setJobStatus('pending');
      setViewState('analyzing');
      showToast(`Initiated analysis for ${maxComments} comments`, "info");
    } catch (err) {
      console.error("Analysis initiation error:", err);
      const detail = err.response?.data?.url?.[0] || err.response?.data?.message || err.message || "Failed to trigger analysis";
      setError(detail);
      showToast(detail, "error");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectRecentReport = (report) => {
    setReportData(report);
    setActiveJobId(report.job_id);
    setActiveSentimentFilter('');
    setActiveSearchQuery('');
    setViewState('dashboard');
    showToast(`Loaded cached report for "${report.video?.title?.slice(0, 30) || 'Video'}..."`, "info");
  };

  const handleReset = () => {
    setViewState('home');
    setActiveJobId(null);
    setReportData(null);
    setError(null);
    setActiveSentimentFilter('');
    setActiveSearchQuery('');
  };

  const scrollToComments = () => {
    if (commentsSectionRef.current) {
      commentsSectionRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  const handleFilterSentimentFromCard = (sentiment) => {
    setActiveSentimentFilter(sentiment);
    scrollToComments();
    showToast(`Filtering comments by ${sentiment} sentiment`, "info");
  };

  const handleSearchKeywordFromChart = (keyword) => {
    setActiveSearchQuery(keyword);
    scrollToComments();
    showToast(`Filtering comments for keyword: "${keyword}"`, "info");
  };

  const handleCopyVideoUrl = () => {
    if (!video?.youtube_video_id) return;
    const url = `https://www.youtube.com/watch?v=${video.youtube_video_id}`;
    navigator.clipboard.writeText(url);
    showToast("YouTube video link copied to clipboard", "success");
  };

  const video = reportData?.video;
  const sentimentSummary = reportData?.sentiment_summary || {};
  const posPct = sentimentSummary.positive_percentage || 0;
  const avgCompound = sentimentSummary.average_compound || 0;
  const totalComments = sentimentSummary.total || video?.comments_count || 0;
  const spamFiltered = sentimentSummary.spam_filtered || 0;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-rose-500 selection:text-white">
      <Navbar 
        onReset={handleReset} 
        isDashboardActive={viewState === 'dashboard'} 
        onOpenCompare={() => setIsCompareModalOpen(true)}
        onOpenMyAnalyses={() => setIsMyAnalysesModalOpen(true)}
      />

      <main className="flex-1 pb-16">
        {viewState === 'home' && (
          <VideoInputForm 
            onSubmit={handleStartAnalysis} 
            isLoading={isSubmitting} 
            error={error}
            onSelectRecentReport={handleSelectRecentReport}
          />
        )}

        {viewState === 'analyzing' && (
          <JobProgress 
            jobId={activeJobId} 
            status={jobStatus} 
            videoTitle={video?.title}
            onCancel={handleReset}
          />
        )}

        {viewState === 'dashboard' && reportData && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8 animate-in fade-in duration-300">
            {/* Executive Video Overview Banner */}
            <div className="relative group">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-rose-600/30 via-indigo-600/30 to-amber-500/30 rounded-3xl blur opacity-30"></div>

              <div className="relative bg-slate-900/95 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-2xl">
                <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
                  {/* Left: Thumbnail & Video Info */}
                  <div className="flex items-start gap-4 sm:gap-5 min-w-0 flex-1">
                    {video?.thumbnail_url ? (
                      <div className="relative shrink-0 group/thumb">
                        <img
                          src={video.thumbnail_url}
                          alt={video.title}
                          className="w-28 sm:w-36 aspect-video rounded-2xl object-cover border border-slate-700/80 shadow-lg group-hover/thumb:scale-105 transition-transform duration-300"
                        />
                        <a
                          href={`https://www.youtube.com/watch?v=${video?.youtube_video_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="absolute inset-0 bg-black/40 opacity-0 group-hover/thumb:opacity-100 rounded-2xl flex items-center justify-center transition-opacity"
                          title="Watch on YouTube"
                        >
                          <Youtube className="w-6 h-6 text-white" />
                        </a>
                      </div>
                    ) : (
                      <div className="w-28 sm:w-36 aspect-video rounded-2xl bg-slate-800 flex items-center justify-center shrink-0 border border-slate-700">
                        <Youtube className="w-8 h-8 text-rose-500" />
                      </div>
                    )}

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-2 flex-wrap">
                        <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                          {video?.channel || 'YouTube Video'}
                        </span>
                        <button
                          onClick={handleCopyVideoUrl}
                          className="text-[11px] text-slate-400 hover:text-slate-200 flex items-center gap-1 bg-slate-800/60 hover:bg-slate-800 px-2 py-0.5 rounded-md border border-slate-700/60 transition-colors"
                          title="Copy YouTube URL"
                        >
                          <span className="font-mono">ID: {video?.youtube_video_id}</span>
                          <Copy className="w-3 h-3 text-slate-400" />
                        </button>
                      </div>

                      <h1 className="text-lg sm:text-xl font-black text-white leading-snug line-clamp-2">
                        {video?.title}
                      </h1>

                      {/* Quick Snapshot Metric Chips */}
                      <div className="flex items-center gap-3 text-xs text-slate-400 mt-3 flex-wrap">
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-800 text-slate-300">
                          <Smile className="w-3.5 h-3.5 text-emerald-400" />
                          <span><strong className="text-white">{posPct}%</strong> Positive</span>
                        </div>
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-800 text-slate-300">
                          <Activity className="w-3.5 h-3.5 text-indigo-400" />
                          <span>Polarity: <strong className="text-white font-mono">{avgCompound > 0 ? `+${avgCompound}` : avgCompound}</strong></span>
                        </div>
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-800 text-slate-300">
                          <ShieldCheck className="w-3.5 h-3.5 text-amber-400" />
                          <span><strong className="text-white">{spamFiltered}</strong> Spam Isolated</span>
                        </div>
                        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-xl bg-slate-950 border border-slate-800 text-slate-300">
                          <span>Total: <strong className="text-white">{totalComments}</strong> Comments</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Right: Export & Action Buttons */}
                  <div className="flex items-center gap-2.5 shrink-0 w-full lg:w-auto flex-wrap">
                    <a
                      href={getExportUrl(activeJobId, 'pdf')}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={() => showToast("Downloading executive PDF report...", "info")}
                      className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 text-white shadow-lg shadow-rose-950/40 transition-all duration-200"
                    >
                      <FileText className="w-4 h-4 text-white" />
                      <span>Download PDF</span>
                    </a>
                    <a
                      href={getExportUrl(activeJobId, 'csv')}
                      target="_blank"
                      rel="noopener noreferrer"
                      download
                      onClick={() => showToast("Exporting comments to CSV...", "info")}
                      className="flex-1 sm:flex-initial inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 transition-all shadow-sm"
                    >
                      <Download className="w-4 h-4 text-rose-400" />
                      <span>Export CSV</span>
                    </a>
                    <button
                      onClick={handleReset}
                      className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-2xl font-bold text-xs bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-800 transition-all"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Analyze New Video</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>

            {/* Sentiment Trajectory Timeline */}
            {reportData.sentiment_timeline && reportData.sentiment_timeline.length > 0 && (
              <SentimentTimeline 
                timeline={reportData.sentiment_timeline} 
                weightedCompound={reportData.weighted_compound ?? reportData.sentiment_summary?.average_compound} 
              />
            )}

            {/* Grid Row 1: Sentiment Breakdown & Topic Modeling */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-stretch">
              <div className="lg:col-span-6">
                <SentimentCard 
                  sentimentSummary={reportData.sentiment_summary} 
                  onFilterSentiment={handleFilterSentimentFromCard}
                />
              </div>
              <div className="lg:col-span-6">
                <TopicsChart 
                  topicClusters={reportData.topic_clusters || []} 
                  topKeywords={reportData.top_keywords || []}
                  topRequests={reportData.top_requests || []}
                  onSearchKeyword={handleSearchKeywordFromChart}
                />
              </div>
            </div>

            {/* Grid Row 2: Aspect-Based Feedback & Emotion Polarity */}
            {(reportData.aspect_sentiment || reportData.emotion_breakdown) && (
              <AspectRadarCard 
                aspectSentiment={reportData.aspect_sentiment || {}} 
                emotionBreakdown={reportData.emotion_breakdown || {}} 
              />
            )}

            {/* Grid Row 3: AI Recommendations & Suggested Titles */}
            <AiRecommendations 
              recommendations={reportData.recommendations} 
              suggestedTitles={reportData.suggested_titles}
            />

            {/* Grid Row 4: Filterable Comments Table */}
            <div ref={commentsSectionRef}>
              <CommentsTable 
                videoId={video?.youtube_video_id} 
                jobId={activeJobId} 
                initialSentimentFilter={activeSentimentFilter}
                initialSearchQuery={activeSearchQuery}
              />
            </div>
          </div>
        )}
      </main>

      {/* Global Modals for Side-by-Side Video Comparison & User Analysis History */}
      <CompareVideosModal 
        isOpen={isCompareModalOpen}
        onClose={() => setIsCompareModalOpen(false)}
        defaultJobId={activeJobId}
      />

      <MyAnalysesModal
        isOpen={isMyAnalysesModalOpen}
        onClose={() => setIsMyAnalysesModalOpen(false)}
        onSelectReport={handleSelectRecentReport}
      />

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <p>
            College Major Project: <span className="text-slate-400 font-medium">Automated Audience Sentiment &amp; Feedback Analysis</span>
          </p>
          <p className="text-[11px] text-slate-400">
            Django &bull; PostgreSQL &bull; Celery &bull; React &bull; Tailwind CSS &bull; NLTK &bull; Groq
          </p>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <DashboardContent />
    </ToastProvider>
  );
}
