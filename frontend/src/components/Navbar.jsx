import React, { useState, useEffect } from 'react';
import { Sparkles, Youtube, BarChart3, RefreshCw, User, LogOut, Lock, GitCompare, History } from 'lucide-react';
import AuthModal from './AuthModal';
import { getStoredUser, getCurrentUser, logoutUser } from '../services/api';
import { useToast } from './Toast';

export default function Navbar({ onReset, isDashboardActive, onOpenCompare, onOpenMyAnalyses }) {
  const [user, setUser] = useState(null);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const { showToast } = useToast();

  useEffect(() => {
    const stored = getStoredUser();
    if (stored) {
      setUser(stored);
    }
    getCurrentUser().then((currentUser) => {
      if (currentUser) {
        setUser(currentUser);
      }
    });
  }, []);

  const handleLogout = () => {
    logoutUser();
    setUser(null);
    showToast("Signed out successfully", "info");
  };

  const handleAuthSuccess = (authedUser) => {
    setUser(authedUser);
  };

  return (
    <>
      <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-950/80 border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo */}
          <div 
            onClick={onReset} 
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-rose-600 via-red-500 to-amber-500 flex items-center justify-center shadow-lg shadow-rose-900/30 group-hover:scale-105 transition-transform duration-200">
              <Youtube className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                  AudiencePulse
                </span>
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20">
                  NLP v2.0
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Automated YouTube Sentiment & Feedback Intelligence
              </p>
            </div>
          </div>

          {/* Action Bar */}
          <div className="flex items-center gap-2.5">
            {/* Compare Videos Button */}
            <button
              onClick={onOpenCompare}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-all shadow-sm"
              title="Compare two videos side by side"
            >
              <GitCompare className="w-3.5 h-3.5 text-indigo-400" />
              <span className="hidden sm:inline">Compare Videos</span>
            </button>

            {/* My Analyses Button (Active or prompt sign-in) */}
            <button
              onClick={() => {
                if (user) {
                  onOpenMyAnalyses();
                } else {
                  setIsAuthModalOpen(true);
                  showToast("Please sign in to view your saved analyses", "info");
                }
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white border border-slate-700/80 transition-all shadow-sm"
              title="View your saved analyses"
            >
              <History className="w-3.5 h-3.5 text-amber-400" />
              <span className="hidden sm:inline">My Analyses</span>
            </button>

            {isDashboardActive && (
              <button
                onClick={onReset}
                className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold rounded-xl bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 border border-rose-500/30 transition-all shadow-sm"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden md:inline">Analyze New Video</span>
              </button>
            )}

            {/* Auth Button or User Badge */}
            {user ? (
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-slate-900 border border-slate-800 text-xs font-medium text-slate-200">
                  <div className="w-5 h-5 rounded-full bg-rose-500/20 text-rose-400 flex items-center justify-center font-bold text-[10px]">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                  <span className="max-w-[90px] truncate hidden sm:inline">{user.username}</span>
                </div>
                <button
                  onClick={handleLogout}
                  title="Sign out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-rose-600 hover:bg-rose-500 text-white shadow-md shadow-rose-950/40 transition-all"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>Sign In</span>
              </button>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />
    </>
  );
}
