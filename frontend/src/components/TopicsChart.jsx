import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from 'recharts';
import { Layers, Hash, HelpCircle, MessageSquare, ArrowDownRight, Tag } from 'lucide-react';

export default function TopicsChart({ 
  topicClusters = [], 
  topKeywords = [], 
  topRequests = [],
  onSearchKeyword 
}) {
  const [activeTab, setActiveTab] = useState('keywords'); // 'keywords' | 'topics' | 'requests'

  // Prepare data for Keywords
  const keywordData = (topKeywords || []).slice(0, 8).map((k) => ({
    name: k.keyword,
    count: k.count,
    type: k.type || 'term',
  }));

  // Prepare data for Topic Clusters
  const clusterData = (topicClusters || []).map((c) => ({
    name: c.topic_name.length > 20 ? c.topic_name.slice(0, 18) + '...' : c.topic_name,
    fullName: c.topic_name,
    count: c.comment_count,
    percentage: c.percentage,
    keywords: c.keywords,
  }));

  const chartData = activeTab === 'keywords' ? keywordData : clusterData;

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 border border-slate-700 p-3 rounded-xl shadow-2xl text-xs backdrop-blur-md">
          <p className="font-bold text-white">{data.fullName || data.name}</p>
          <p className="text-rose-400 mt-1 font-semibold">{data.count} comment mentions</p>
          {data.keywords && (
            <p className="text-slate-400 text-[11px] mt-1">
              Centroid: {data.keywords.join(', ')}
            </p>
          )}
          <p className="text-[10px] text-slate-500 mt-1">Click to filter comment log</p>
        </div>
      );
    }
    return null;
  };

  const handleItemClick = (term) => {
    if (onSearchKeyword && term) {
      onSearchKeyword(term);
    }
  };

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-7 shadow-2xl backdrop-blur-xl flex flex-col justify-between h-full">
      <div>
        {/* Header and Toggle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-400" />
              <span>Topic Modeling &amp; Interests</span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              TF-IDF Vectorization &bull; K-Means Centroid Clustering
            </p>
          </div>

          {/* Tab Switcher */}
          <div className="inline-flex p-1 rounded-2xl bg-slate-950 border border-slate-800 text-xs font-semibold self-start sm:self-auto">
            <button
              onClick={() => setActiveTab('keywords')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                activeTab === 'keywords'
                  ? 'bg-rose-500 text-white shadow-md shadow-rose-950/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Hash className="w-3.5 h-3.5" />
              <span>Keywords</span>
            </button>
            <button
              onClick={() => setActiveTab('topics')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                activeTab === 'topics'
                  ? 'bg-rose-500 text-white shadow-md shadow-rose-950/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              <span>Clusters</span>
            </button>
            <button
              onClick={() => setActiveTab('requests')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl transition-all ${
                activeTab === 'requests'
                  ? 'bg-rose-500 text-white shadow-md shadow-rose-950/40'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Requests ({topRequests?.length || 0})</span>
            </button>
          </div>
        </div>

        {/* Tab 1 & 2: Bar Chart or Clusters */}
        {activeTab !== 'requests' ? (
          <div>
            <div className="h-56 w-full">
              {chartData.length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={chartData}
                    layout="vertical"
                    margin={{ top: 5, right: 25, left: 25, bottom: 5 }}
                  >
                    <XAxis type="number" stroke="#64748b" fontSize={11} />
                    <YAxis
                      type="category"
                      dataKey="name"
                      stroke="#94a3b8"
                      fontSize={11}
                      width={100}
                      tickLine={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar 
                      dataKey="count" 
                      radius={[0, 8, 8, 0]}
                      onClick={(e) => handleItemClick(e?.name || e?.fullName)}
                      cursor="pointer"
                    >
                      {chartData.map((entry, index) => (
                        <Cell
                          key={`cell-${index}`}
                          fill={index % 2 === 0 ? '#f43f5e' : '#fb7185'}
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                  No keywords or clusters extracted from this sample.
                </div>
              )}
            </div>

            {/* Quick Interactive Tags Cloud */}
            {topKeywords && topKeywords.length > 0 && (
              <div className="mt-4 pt-4 border-t border-slate-800/80">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <Tag className="w-3.5 h-3.5 text-rose-400" />
                  <span>Click keyword to filter comments:</span>
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {topKeywords.slice(0, 10).map((k, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleItemClick(k.keyword)}
                      className="px-2.5 py-1 rounded-lg bg-slate-950 hover:bg-rose-500/10 border border-slate-800 hover:border-rose-500/30 text-xs text-slate-300 hover:text-rose-300 font-medium transition-all group flex items-center gap-1"
                    >
                      <span>#{k.keyword}</span>
                      <span className="text-[10px] text-slate-400 font-mono">({k.count})</span>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          /* Tab 3: Audience Requests Direct List */
          <div className="space-y-3">
            {topRequests && topRequests.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {topRequests.map((req, idx) => (
                  <div
                    key={idx}
                    onClick={() => handleItemClick(req.request)}
                    className="p-3.5 rounded-2xl bg-slate-950/70 hover:bg-amber-950/20 border border-slate-800/80 hover:border-amber-500/40 text-left transition-all cursor-pointer group shadow-sm flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between text-[10px] text-amber-400 font-bold uppercase mb-1.5">
                        <span className="px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20">
                          {req.category ? req.category.replace('_', ' ') : 'Viewer Request'}
                        </span>
                        <span className="text-slate-400">{req.count} request{req.count > 1 ? 's' : ''}</span>
                      </div>
                      <p className="text-xs font-semibold text-slate-200 group-hover:text-amber-200 transition-colors line-clamp-3">
                        "{req.request}"
                      </p>
                    </div>

                    <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[10px] text-slate-400 group-hover:text-amber-300">
                      <span>Search related comments</span>
                      <ArrowDownRight className="w-3 h-3" />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="py-12 text-center text-slate-500 text-xs">
                No explicit tutorial or feature requests detected in this sample.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
