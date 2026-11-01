import React, { useState, useEffect, useRef } from 'react';
import { 
  Sparkles, Youtube, BarChart3, RefreshCw, User, LogOut, Lock, 
  GitCompare, History, ChevronDown, CheckCircle2, Shield
} from 'lucide-react';
import AuthModal from './AuthModal';
import { getStoredUser, getCurrentUser, logoutUser } from '../services/api';
import { useToast } from './Toast';

export default function Navbar({ 
  onReset, 
  isDashboardActive, 
  onOpenCompare, 
  onOpenMyAnalyses,
  isAuthModalOpen,
  setIsAuthModalOpen,
  user,
  setUser
}) {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);
  const { showToast } = useToast();

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Listen for user-logout event from api interceptor
  useEffect(() => {
    const handleLogoutEvent = () => {
      setUser(null);
      setDropdownOpen(false);
    };
    window.addEventListener('user-logout', handleLogoutEvent);
    return () => window.removeEventListener('user-logout', handleLogoutEvent);
  }, [setUser]);

  const handleLogout = async () => {
    setDropdownOpen(false);
    await logoutUser();
    setUser(null);
    showToast("Signed out successfully", "info");
  };

  const handleAuthSuccess = (authedUser) => {
    setUser(authedUser);
  };

  return (
    <>
      <header className="sticky top-0 z-40 backdrop-blur-md bg-slate-950/85 border-b border-slate-800/80">
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

            {/* My Analyses Button */}
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
                <span className="hidden md:inline">New Analysis</span>
              </button>
            )}

            {/* Auth Dropdown or Sign In Button */}
            {user ? (
              <div className="relative" ref={dropdownRef}>
                <button
                  type="button"
                  onClick={() => setDropdownOpen(!dropdownOpen)}
                  className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700/80 text-xs font-medium text-slate-200 transition-all shadow-sm group"
                  aria-expanded={dropdownOpen}
                  aria-haspopup="true"
                >
                  <div className="w-6 h-6 rounded-lg bg-gradient-to-tr from-rose-600 to-amber-500 text-white flex items-center justify-center font-bold text-xs shadow-inner">
                    {user.username?.charAt(0).toUpperCase() || 'U'}
                  </div>
                  <span className="max-w-[100px] truncate hidden sm:inline font-semibold">
                    {user.username}
                  </span>
                  <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform duration-200 ${dropdownOpen ? 'rotate-180' : ''}`} />
                </button>

                {/* Dropdown Menu */}
                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-slate-900 border border-slate-800 shadow-2xl shadow-rose-950/30 py-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
                    {/* User Info Header */}
                    <div className="px-4 py-2.5 border-b border-slate-800">
                      <p className="text-xs font-bold text-white truncate">
                        {user.username}
                      </p>
                      <p className="text-[11px] text-slate-400 truncate mt-0.5">
                        {user.email || 'Authenticated User'}
                      </p>
                    </div>

                    {/* Nav Actions */}
                    <div className="py-1">
                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          onOpenMyAnalyses();
                        }}
                        className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800/80 transition-colors text-left"
                      >
                        <History className="w-4 h-4 text-amber-400" />
                        <span>My Analyses</span>
                      </button>

                      <button
                        onClick={() => {
                          setDropdownOpen(false);
                          onOpenCompare();
                        }}
                        className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-slate-300 hover:text-white hover:bg-slate-800/80 transition-colors text-left"
                      >
                        <GitCompare className="w-4 h-4 text-indigo-400" />
                        <span>Compare Videos</span>
                      </button>
                    </div>

                    <div className="border-t border-slate-800 my-1" />

                    {/* Sign out */}
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-2.5 px-4 py-2 text-xs text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors text-left font-semibold"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                )}
              </div>
            ) : (
              <button
                onClick={() => setIsAuthModalOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold rounded-xl bg-gradient-to-r from-rose-600 to-amber-500 hover:from-rose-500 hover:to-amber-400 text-white shadow-md shadow-rose-950/40 transition-all"
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
