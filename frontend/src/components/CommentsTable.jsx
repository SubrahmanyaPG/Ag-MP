import React, { useState, useEffect, useRef } from 'react';
import { 
  Filter, Search, ThumbsUp, Calendar, AlertTriangle, 
  Smile, Meh, Frown, ChevronLeft, ChevronRight, Download, FileText, 
  Loader2, X, ArrowUpDown, Check, RefreshCw, MessageSquare, Copy, Sparkles, HelpCircle 
} from 'lucide-react';
import { getVideoComments, getExportUrl, draftCommentReply } from '../services/api';
import { useToast } from './Toast';

export default function CommentsTable({ 
  videoId, 
  jobId, 
  initialSentimentFilter = '', 
  initialSearchQuery = '' 
}) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  // Filters
  const [sentimentFilter, setSentimentFilter] = useState(initialSentimentFilter);
  const [spamFilter, setSpamFilter] = useState('');
  const [aspectFilter, setAspectFilter] = useState('');
  const [needsResponseFilter, setNeedsResponseFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState(initialSearchQuery);
  const [sortBy, setSortBy] = useState('default');
  const [expandedComments, setExpandedComments] = useState({});
  const [copiedReplyId, setCopiedReplyId] = useState(null);

  const { showToast } = useToast();
  const searchTimeoutRef = useRef(null);

  // Sync external filter changes
  useEffect(() => {
    if (initialSentimentFilter !== undefined) {
      setSentimentFilter(initialSentimentFilter);
    }
  }, [initialSentimentFilter]);

  useEffect(() => {
    if (initialSearchQuery !== undefined) {
      setSearchQuery(initialSearchQuery);
    }
  }, [initialSearchQuery]);

  const fetchComments = async (page = 1) => {
    if (!videoId) return;
    setLoading(true);
    try {
      const params = {
        page,
        page_size: 15,
      };
      if (sentimentFilter) params.sentiment = sentimentFilter;
      if (spamFilter !== '') params.is_spam = spamFilter;
      if (aspectFilter) params.aspect = aspectFilter;
      if (needsResponseFilter !== '') params.needs_response = needsResponseFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();

      const data = await getVideoComments(videoId, params);
      let results = data.results || [];

      // Sorting
      if (sortBy === 'likes_desc') {
        results = [...results].sort((a, b) => b.like_count - a.like_count);
      } else if (sortBy === 'sentiment_desc') {
        results = [...results].sort((a, b) => (b.sentiment_score || 0) - (a.sentiment_score || 0));
      } else if (sortBy === 'sentiment_asc') {
        results = [...results].sort((a, b) => (a.sentiment_score || 0) - (b.sentiment_score || 0));
      }

      setComments(results);
      setTotalCount(data.count || 0);
      setTotalPages(Math.ceil((data.count || 0) / 15) || 1);
      setCurrentPage(page);
    } catch (err) {
      console.error("Failed to fetch comments", err);
      showToast("Unable to fetch comments from server.", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComments(1);
  }, [videoId, sentimentFilter, spamFilter, aspectFilter, needsResponseFilter, sortBy]);

  const handleSearchChange = (val) => {
    setSearchQuery(val);
    if (searchTimeoutRef.current) clearTimeout(searchTimeoutRef.current);
    searchTimeoutRef.current = setTimeout(() => {
      fetchComments(1);
    }, 350);
  };

  const handleClearAllFilters = () => {
    setSentimentFilter('');
    setSpamFilter('');
    setAspectFilter('');
    setNeedsResponseFilter('');
    setSearchQuery('');
    setSortBy('default');
  };

  const toggleExpand = (id) => {
    setExpandedComments((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleCopyReply = (text, id) => {
    navigator.clipboard.writeText(text);
    setCopiedReplyId(id);
    showToast("Creator reply draft copied to clipboard!", "success");
    setTimeout(() => setCopiedReplyId(null), 2500);
  };

  const hasActiveFilters = Boolean(
    sentimentFilter || 
    spamFilter !== '' || 
    aspectFilter || 
    needsResponseFilter !== '' || 
    searchQuery.trim() || 
    sortBy !== 'default'
  );

  const getSentimentBadge = (label, score) => {
    if (label === 'positive') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
          <Smile className="w-3 h-3" />
          <span>Pos ({score > 0 ? `+${score}` : score})</span>
        </span>
      );
    }
    if (label === 'negative') {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/20">
          <Frown className="w-3 h-3" />
          <span>Neg ({score})</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-700/20 text-slate-300 border border-slate-700/40">
        <Meh className="w-3 h-3" />
        <span>Neu ({score || 0})</span>
      </span>
    );
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-lg font-bold text-white flex items-center gap-2">
            <Filter className="w-5 h-5 text-rose-500" />
            <span>Audience Comments Log &amp; Creator Assistant</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Full-text search &bull; Explainable spam detection &bull; AI reply drafts for viewer questions
          </p>
        </div>

        {/* Export buttons */}
        {jobId && (
          <div className="flex items-center gap-2.5 self-start md:self-auto flex-wrap">
            <a
              href={getExportUrl(jobId, 'pdf')}
              target="_blank"
              rel="noopener noreferrer"
              onClick={() => showToast("Preparing executive PDF report...", "info")}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold text-white bg-gradient-to-r from-rose-600 to-red-600 hover:from-rose-500 hover:to-red-500 shadow-md shadow-rose-950/40 transition-all"
            >
              <FileText className="w-4 h-4 text-white" />
              <span>Download PDF</span>
            </a>
            <a
              href={getExportUrl(jobId, 'csv')}
              target="_blank"
              rel="noopener noreferrer"
              download
              onClick={() => showToast("Exporting comments to CSV...", "info")}
              className="inline-flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-bold text-slate-200 bg-slate-800 hover:bg-slate-700 border border-slate-700 transition-all shadow-sm"
            >
              <Download className="w-4 h-4 text-rose-400" />
              <span>Export CSV</span>
            </a>
          </div>
        )}
      </div>

      {/* Filter Toolbar */}
      <div className="grid grid-cols-1 sm:grid-cols-12 gap-3 mb-5">
        {/* Search Input with Debounce */}
        <div className="sm:col-span-3 relative">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder="Search comment or author..."
            className="w-full pl-9 pr-8 py-2 rounded-xl bg-slate-950 border border-slate-800 text-xs text-white placeholder-slate-500 focus:outline-none focus:ring-1 focus:ring-rose-500 shadow-inner"
          />
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-2.5" />
          {searchQuery && (
            <button
              onClick={() => handleSearchChange('')}
              className="absolute right-2.5 top-2.5 text-slate-500 hover:text-white"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Sentiment Filter Tabs */}
        <div className="sm:col-span-3 flex items-center gap-1 p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs">
          {[
            { label: 'All', value: '' },
            { label: 'Pos', value: 'positive' },
            { label: 'Neu', value: 'neutral' },
            { label: 'Neg', value: 'negative' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSentimentFilter(tab.value)}
              className={`flex-1 py-1 px-1.5 rounded-lg font-bold text-[11px] transition-all ${
                sentimentFilter === tab.value
                  ? 'bg-rose-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Spam Filter Tabs */}
        <div className="sm:col-span-2 flex items-center gap-1 p-1 rounded-xl bg-slate-950 border border-slate-800 text-xs">
          {[
            { label: 'All', value: '' },
            { label: 'Clean', value: 'false' },
            { label: 'Spam', value: 'true' },
          ].map((tab) => (
            <button
              key={tab.value}
              onClick={() => setSpamFilter(tab.value)}
              className={`flex-1 py-1 px-1 rounded-lg font-bold text-[11px] transition-all ${
                spamFilter === tab.value
                  ? 'bg-rose-500 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Needs Reply / Question Filter */}
        <div className="sm:col-span-2">
          <button
            onClick={() => setNeedsResponseFilter(needsResponseFilter === 'true' ? '' : 'true')}
            className={`w-full py-2 px-2.5 rounded-xl border text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${
              needsResponseFilter === 'true'
                ? 'bg-amber-500 text-white border-amber-400 shadow-md shadow-amber-950/40'
                : 'bg-slate-950 text-slate-300 border-slate-800 hover:border-slate-700'
            }`}
          >
            <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
            <span>Questions</span>
          </button>
        </div>

        {/* Sort Select */}
        <div className="sm:col-span-2">
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full py-2 px-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 focus:outline-none focus:border-rose-500 font-semibold"
          >
            <option value="default">Sort: Default</option>
            <option value="likes_desc">Sort: Most Liked</option>
            <option value="sentiment_desc">Sort: Most Positive</option>
            <option value="sentiment_asc">Sort: Most Critical</option>
          </select>
        </div>
      </div>

      {/* Active Filter Badges Bar */}
      {hasActiveFilters && (
        <div className="flex items-center gap-2 mb-4 text-xs flex-wrap">
          <span className="text-slate-400 font-semibold text-[11px]">Active Filters:</span>
          {sentimentFilter && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-rose-500/10 border border-rose-500/20 text-rose-300 text-[11px]">
              Sentiment: {sentimentFilter}
              <button onClick={() => setSentimentFilter('')}><X className="w-3 h-3 hover:text-white" /></button>
            </span>
          )}
          {spamFilter !== '' && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]">
              {spamFilter === 'true' ? 'Spam comments' : 'Clean comments'}
              <button onClick={() => setSpamFilter('')}><X className="w-3 h-3 hover:text-white" /></button>
            </span>
          )}
          {needsResponseFilter === 'true' && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-amber-300 text-[11px]">
              Viewer Questions &amp; Requests
              <button onClick={() => setNeedsResponseFilter('')}><X className="w-3 h-3 hover:text-white" /></button>
            </span>
          )}
          {searchQuery && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px]">
              Search: "{searchQuery}"
              <button onClick={() => handleSearchChange('')}><X className="w-3 h-3 hover:text-white" /></button>
            </span>
          )}
          {sortBy !== 'default' && (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-slate-800 text-slate-300 text-[11px]">
              Sort: {sortBy.replace('_', ' ')}
              <button onClick={() => setSortBy('default')}><X className="w-3 h-3 hover:text-white" /></button>
            </span>
          )}
          <button
            onClick={handleClearAllFilters}
            className="text-[11px] font-bold text-rose-400 hover:text-rose-300 underline ml-1"
          >
            Clear all
          </button>
        </div>
      )}

      {/* Table Container */}
      <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-950/70 shadow-inner">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-800 bg-slate-900/80 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <th className="py-3 px-4">Author</th>
              <th className="py-3 px-4 w-1/2">Comment Text &amp; Insights</th>
              <th className="py-3 px-4">Sentiment</th>
              <th className="py-3 px-4">Spam Flag &amp; Cause</th>
              <th className="py-3 px-4 text-right">Likes</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {loading ? (
              <tr>
                <td colSpan={5} className="py-14 text-center text-slate-400">
                  <div className="inline-flex items-center gap-2 font-semibold">
                    <Loader2 className="w-4 h-4 animate-spin text-rose-500" />
                    <span>Loading comments...</span>
                  </div>
                </td>
              </tr>
            ) : comments.length > 0 ? (
              comments.map((comment) => {
                const isExpanded = expandedComments[comment.id];
                const isLong = comment.text && comment.text.length > 130;
                const isCopied = copiedReplyId === comment.id;

                return (
                  <tr key={comment.id} className="hover:bg-slate-900/50 transition-colors">
                    {/* Author */}
                    <td className="py-3 px-4 font-bold text-slate-200 whitespace-nowrap align-top">
                      <div className="flex items-center gap-2">
                        {comment.author_profile_image ? (
                          <img 
                            src={comment.author_profile_image} 
                            alt="" 
                            className="w-5 h-5 rounded-full object-cover shrink-0 border border-slate-700"
                          />
                        ) : (
                          <div className="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-bold text-[9px] shrink-0">
                            {comment.author ? comment.author.charAt(0).toUpperCase() : 'A'}
                          </div>
                        )}
                        <div className="min-w-0">
                          <span className="truncate max-w-[110px] font-medium text-slate-300 block">
                            {comment.author || 'Anonymous'}
                          </span>
                          {comment.language && comment.language !== 'en' && (
                            <span className="text-[9px] uppercase font-bold text-indigo-400/90 font-mono">
                              {comment.language}
                            </span>
                          )}
                        </div>
                      </div>
                    </td>

                    {/* Text & Draft Reply Assistant */}
                    <td className="py-3 px-4 text-slate-300 leading-relaxed font-normal align-top">
                      <p className={!isExpanded && isLong ? "line-clamp-2" : ""}>
                        {comment.text}
                      </p>
                      {isLong && (
                        <button
                          onClick={() => toggleExpand(comment.id)}
                          className="mt-1 text-[11px] font-bold text-rose-400 hover:text-rose-300 transition-colors"
                        >
                          {isExpanded ? 'Show less' : 'Read full comment'}
                        </button>
                      )}

                      {/* Aspect & Question Badges */}
                      <div className="flex items-center gap-1.5 mt-2 flex-wrap">
                        {comment.aspect && comment.aspect !== 'general' && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700">
                            Aspect: {comment.aspect}
                          </span>
                        )}
                        {comment.emotion && comment.emotion !== 'neutral' && (
                          <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 border border-slate-700">
                            Tone: {comment.emotion}
                          </span>
                        )}
                        {comment.needs_response && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20">
                            Question / Request
                          </span>
                        )}
                      </div>

                      {/* AI Creator Reply Drafter Card */}
                      {comment.draft_reply && (
                        <div className="mt-2.5 p-3 rounded-xl bg-slate-900 border border-indigo-500/30 text-left">
                          <div className="flex items-center justify-between mb-1.5">
                            <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider flex items-center gap-1">
                              <Sparkles className="w-3 h-3 text-amber-400" />
                              <span>AI Creator Reply Suggestion</span>
                            </span>
                            <button
                              onClick={() => handleCopyReply(comment.draft_reply, comment.id)}
                              className="text-[10px] font-bold text-indigo-300 hover:text-white flex items-center gap-1 bg-indigo-500/20 hover:bg-indigo-500/30 px-2 py-0.5 rounded-md transition-colors"
                            >
                              {isCopied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                              <span>{isCopied ? 'Copied' : 'Copy Reply'}</span>
                            </button>
                          </div>
                          <p className="text-[11px] text-slate-300 italic leading-snug">
                            "{comment.draft_reply}"
                          </p>
                        </div>
                      )}
                    </td>

                    {/* Sentiment */}
                    <td className="py-3 px-4 whitespace-nowrap align-top">
                      {getSentimentBadge(comment.sentiment_label, comment.sentiment_score)}
                    </td>

                    {/* Spam Flag & Explainability */}
                    <td className="py-3 px-4 whitespace-nowrap align-top">
                      {comment.is_spam ? (
                        <div className="space-y-1">
                          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-950/80 text-red-400 border border-red-800/60">
                            <AlertTriangle className="w-3 h-3 text-red-400" />
                            <span>Spam Quarantined</span>
                          </span>
                          {comment.spam_reason && (
                            <p className="text-[10px] text-slate-400 max-w-[140px] truncate" title={comment.spam_reason}>
                              Cause: {comment.spam_reason}
                            </p>
                          )}
                        </div>
                      ) : (
                        <span className="text-slate-400 text-[11px] font-medium">Clean</span>
                      )}
                    </td>

                    {/* Likes */}
                    <td className="py-3 px-4 text-right text-slate-400 font-mono whitespace-nowrap align-top">
                      <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-300">
                        <ThumbsUp className="w-3 h-3 text-slate-400" />
                        {comment.like_count}
                      </span>
                    </td>
                  </tr>
                );
              })
            ) : (
              <tr>
                <td colSpan={5} className="py-12 text-center text-slate-500">
                  <p className="text-sm font-semibold text-slate-400">No comments matched your filter criteria.</p>
                  <button
                    onClick={handleClearAllFilters}
                    className="mt-2 text-xs font-bold text-rose-400 hover:underline"
                  >
                    Reset all filters
                  </button>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between text-xs text-slate-400 mt-4 pt-3 border-t border-slate-800">
        <span>
          Showing <strong className="text-white">{comments.length}</strong> of <strong className="text-white">{totalCount}</strong> comments (Page {currentPage} of {totalPages})
        </span>

        <div className="flex items-center gap-2">
          <button
            onClick={() => fetchComments(currentPage - 1)}
            disabled={currentPage <= 1 || loading}
            className="p-1.5 rounded-xl border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition-colors"
            title="Previous Page"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span className="px-2 font-mono font-bold text-white text-xs">
            {currentPage} / {totalPages}
          </span>
          <button
            onClick={() => fetchComments(currentPage + 1)}
            disabled={currentPage >= totalPages || loading}
            className="p-1.5 rounded-xl border border-slate-800 hover:bg-slate-800 disabled:opacity-40 disabled:cursor-not-allowed text-slate-300 transition-colors"
            title="Next Page"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
