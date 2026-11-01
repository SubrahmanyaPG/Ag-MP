import React, { useState, useEffect, useRef } from 'react';
import { 
  X, Lock, Mail, User, AlertCircle, Loader2, Sparkles, CheckCircle2, 
  Eye, EyeOff, ShieldCheck, ArrowRight, Check, Zap, BarChart2
} from 'lucide-react';
import { loginUser, registerUser } from '../services/api';
import { useToast } from './Toast';

export default function AuthModal({ isOpen, onClose, onAuthSuccess }) {
  const [isRegister, setIsRegister] = useState(false);
  const [identifier, setIdentifier] = useState(''); // username or email for login, username for register
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [generalError, setGeneralError] = useState(null);
  const [fieldErrors, setFieldErrors] = useState({});
  const [successMsg, setSuccessMsg] = useState(null);

  const modalRef = useRef(null);
  const inputRef = useRef(null);
  const { showToast } = useToast();

  // Focus trap & Escape key listener
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    // Auto-focus input on open
    setTimeout(() => {
      inputRef.current?.focus();
    }, 100);

    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Calculate password strength (score 0-4)
  const calculatePasswordStrength = (pwd) => {
    if (!pwd) return { score: 0, label: 'Too short', color: 'bg-slate-700' };
    let score = 0;
    if (pwd.length >= 8) score += 1;
    if (pwd.length >= 12) score += 1;
    if (/[A-Z]/.test(pwd) && /[a-z]/.test(pwd)) score += 1;
    if (/\d/.test(pwd) && /[^A-Za-z0-9]/.test(pwd)) score += 1;

    switch (score) {
      case 1:
        return { score: 1, label: 'Weak', color: 'bg-red-500', text: 'text-red-400' };
      case 2:
        return { score: 2, label: 'Fair', color: 'bg-amber-500', text: 'text-amber-400' };
      case 3:
        return { score: 3, label: 'Good', color: 'bg-sky-500', text: 'text-sky-400' };
      case 4:
        return { score: 4, label: 'Strong', color: 'bg-emerald-500', text: 'text-emerald-400' };
      default:
        return { score: 0, label: 'Too short', color: 'bg-slate-700', text: 'text-slate-500' };
    }
  };

  const strength = calculatePasswordStrength(password);

  const switchMode = (toRegister) => {
    setIsRegister(toRegister);
    setGeneralError(null);
    setFieldErrors({});
    setSuccessMsg(null);
    setPassword('');
  };

  const handleInputChange = (field, setter) => (e) => {
    setter(e.target.value);
    if (fieldErrors[field]) {
      setFieldErrors((prev) => {
        const next = { ...prev };
        delete next[field];
        return next;
      });
    }
    if (generalError) setGeneralError(null);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setGeneralError(null);
    setFieldErrors({});
    setSuccessMsg(null);
    setLoading(true);

    try {
      if (isRegister) {
        const res = await registerUser(identifier.trim(), email.trim(), password);
        setSuccessMsg("Account created successfully!");
        showToast(`Welcome @${res.user.username}! Your account is ready.`, "success", "Account Created");
        setTimeout(() => {
          onAuthSuccess(res.user);
          onClose();
        }, 700);
      } else {
        const res = await loginUser(identifier.trim(), password);
        setSuccessMsg("Signed in successfully!");
        showToast(`Welcome back, @${res.user.username}!`, "success", "Signed In");
        setTimeout(() => {
          onAuthSuccess(res.user);
          onClose();
        }, 600);
      }
    } catch (err) {
      console.error("Authentication error:", err);
      const data = err.response?.data;
      if (data && typeof data === 'object') {
        const errors = {};
        let topMsg = null;

        for (const [key, val] of Object.entries(data)) {
          const text = Array.isArray(val) ? val.join(' ') : String(val);
          if (key === 'detail' || key === 'non_field_errors') {
            topMsg = text;
          } else {
            errors[key] = text;
          }
        }
        setFieldErrors(errors);
        if (topMsg) {
          setGeneralError(topMsg);
        } else if (Object.keys(errors).length === 0) {
          setGeneralError("Authentication failed. Please check your credentials.");
        }
      } else {
        setGeneralError(err.message || "An unexpected error occurred. Please try again.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 bg-slate-950/85 backdrop-blur-md animate-in fade-in duration-200"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-labelledby="auth-modal-title"
    >
      <div 
        ref={modalRef}
        className="relative w-full max-w-3xl bg-slate-900 border border-slate-800 rounded-3xl shadow-2xl shadow-rose-950/30 overflow-hidden flex flex-col md:flex-row max-h-[92vh]"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <button
          onClick={onClose}
          aria-label="Close dialog"
          className="absolute top-4 right-4 z-20 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Left Side: Branded Panel (Desktop) */}
        <div className="hidden md:flex md:w-5/12 bg-gradient-to-br from-slate-950 via-slate-900 to-rose-950/40 p-8 flex-col justify-between border-r border-slate-800/80 relative overflow-hidden">
          {/* Ambient Glow */}
          <div className="absolute top-0 right-0 w-48 h-48 bg-rose-600/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute bottom-0 left-0 w-48 h-48 bg-amber-600/10 rounded-full blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="relative z-10">
            <div className="inline-flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs font-semibold mb-6">
              <Zap className="w-3.5 h-3.5" />
              <span>AudiencePulse NLP v2.0</span>
            </div>

            <h2 className="text-2xl font-black text-white tracking-tight leading-tight">
              AI-Powered Feedback Intelligence
            </h2>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              Transform thousands of YouTube viewer comments into clear, actionable sentiment insights in seconds.
            </p>
          </div>

          {/* Feature Highlights */}
          <div className="relative z-10 space-y-3.5 my-8">
            <div className="flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-lg bg-emerald-500/15 text-emerald-400 flex items-center justify-center shrink-0 mt-0.5 border border-emerald-500/20">
                <Check className="w-3 h-3" />
              </div>
              <p className="text-xs text-slate-300">
                <strong className="text-white">Dual NLP Engine:</strong> VADER & Hinglish slang sentiment classification.
              </p>
            </div>

            <div className="flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-lg bg-rose-500/15 text-rose-400 flex items-center justify-center shrink-0 mt-0.5 border border-rose-500/20">
                <Check className="w-3 h-3" />
              </div>
              <p className="text-xs text-slate-300">
                <strong className="text-white">Intelligent Spam Filter:</strong> 95%+ precision filtering with explainability reasons.
              </p>
            </div>

            <div className="flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-lg bg-amber-500/15 text-amber-400 flex items-center justify-center shrink-0 mt-0.5 border border-amber-500/20">
                <Check className="w-3 h-3" />
              </div>
              <p className="text-xs text-slate-300">
                <strong className="text-white">Creator Assistance:</strong> Question detection and automated reply drafting.
              </p>
            </div>

            <div className="flex items-start gap-2.5">
              <div className="w-5 h-5 rounded-lg bg-indigo-500/15 text-indigo-400 flex items-center justify-center shrink-0 mt-0.5 border border-indigo-500/20">
                <Check className="w-3 h-3" />
              </div>
              <p className="text-xs text-slate-300">
                <strong className="text-white">Video Comparison:</strong> Side-by-side benchmarking and Jaccard keyword overlap.
              </p>
            </div>
          </div>

          {/* Footer note */}
          <div className="relative z-10 pt-4 border-t border-slate-800/60">
            <p className="text-[11px] text-slate-500">
              Secured with JWT rotation, scoped rate limits & per-user authorization.
            </p>
          </div>
        </div>

        {/* Right Side: Form Area */}
        <div className="flex-1 p-6 sm:p-8 flex flex-col justify-center overflow-y-auto">
          {/* Form Header */}
          <div className="mb-6">
            <h3 id="auth-modal-title" className="text-xl font-bold text-white tracking-tight">
              {isRegister ? "Create Your Creator Account" : "Sign In to AudiencePulse"}
            </h3>
            <p className="text-xs text-slate-400 mt-1">
              {isRegister
                ? "Join to run analyses, unlock video comparisons, and track history."
                : "Sign in with your username or email to manage your saved analyses."}
            </p>
          </div>

          {/* Tab Selector */}
          <div className="flex rounded-xl bg-slate-950 p-1 mb-6 border border-slate-800">
            <button
              type="button"
              onClick={() => switchMode(false)}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                !isRegister
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => switchMode(true)}
              className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all ${
                isRegister
                  ? 'bg-slate-800 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>

          {/* General Alerts */}
          {generalError && (
            <div 
              aria-live="polite"
              className="mb-4 p-3.5 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-xs flex items-center gap-2.5"
            >
              <AlertCircle className="w-4 h-4 shrink-0 text-red-400" />
              <span>{generalError}</span>
            </div>
          )}

          {successMsg && (
            <div 
              aria-live="polite"
              className="mb-4 p-3.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2.5"
            >
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username or Email Input */}
            <div>
              <label 
                htmlFor="auth-identifier" 
                className="block text-xs font-semibold text-slate-300 mb-1.5"
              >
                {isRegister ? "Username" : "Username or Email"}
              </label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  id="auth-identifier"
                  ref={inputRef}
                  type="text"
                  required
                  value={identifier}
                  onChange={handleInputChange('username', setIdentifier)}
                  placeholder={isRegister ? "Choose a unique username" : "Enter username or email address"}
                  aria-invalid={!!fieldErrors.username}
                  className={`w-full pl-10 pr-4 py-2.5 text-xs bg-slate-950 border rounded-xl text-white placeholder-slate-500 focus:outline-none transition-colors ${
                    fieldErrors.username 
                      ? 'border-red-500/80 focus:border-red-500' 
                      : 'border-slate-800 focus:border-rose-500'
                  }`}
                />
              </div>
              {fieldErrors.username && (
                <p className="text-[11px] text-red-400 mt-1.5 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 shrink-0" />
                  {fieldErrors.username}
                </p>
              )}
            </div>

            {/* Email field (Register mode) */}
            {isRegister && (
              <div>
                <label 
                  htmlFor="auth-email" 
                  className="block text-xs font-semibold text-slate-300 mb-1.5"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                  <input
                    id="auth-email"
                    type="email"
                    required
                    value={email}
                    onChange={handleInputChange('email', setEmail)}
                    placeholder="name@example.com"
                    aria-invalid={!!fieldErrors.email}
                    className={`w-full pl-10 pr-4 py-2.5 text-xs bg-slate-950 border rounded-xl text-white placeholder-slate-500 focus:outline-none transition-colors ${
                      fieldErrors.email 
                        ? 'border-red-500/80 focus:border-red-500' 
                        : 'border-slate-800 focus:border-rose-500'
                    }`}
                  />
                </div>
                {fieldErrors.email && (
                  <p className="text-[11px] text-red-400 mt-1.5 flex items-center gap-1">
                    <AlertCircle className="w-3 h-3 shrink-0" />
                    {fieldErrors.email}
                  </p>
                )}
              </div>
            )}

            {/* Password Input */}
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label 
                  htmlFor="auth-password" 
                  className="block text-xs font-semibold text-slate-300"
                >
                  Password
                </label>
                {isRegister && password && (
                  <span className={`text-[11px] font-medium ${strength.text}`}>
                    Strength: {strength.label}
                  </span>
                )}
              </div>

              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
                <input
                  id="auth-password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={handleInputChange('password', setPassword)}
                  placeholder={isRegister ? "Minimum 8 characters" : "Enter your password"}
                  aria-invalid={!!fieldErrors.password}
                  className={`w-full pl-10 pr-10 py-2.5 text-xs bg-slate-950 border rounded-xl text-white placeholder-slate-500 focus:outline-none transition-colors ${
                    fieldErrors.password 
                      ? 'border-red-500/80 focus:border-red-500' 
                      : 'border-slate-800 focus:border-rose-500'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>

              {/* Password strength meter on register */}
              {isRegister && password && (
                <div className="mt-2 space-y-1">
                  <div className="grid grid-cols-4 gap-1.5 h-1.5">
                    {[1, 2, 3, 4].map((step) => (
                      <div
                        key={step}
                        className={`rounded-full transition-all duration-300 ${
                          strength.score >= step ? strength.color : 'bg-slate-800'
                        }`}
                      />
                    ))}
                  </div>
                  <p className="text-[10px] text-slate-500">
                    Use 8+ chars with uppercase, numbers and symbols for highest security.
                  </p>
                </div>
              )}

              {fieldErrors.password && (
                <p className="text-[11px] text-red-400 mt-1.5 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3 shrink-0" />
                  {fieldErrors.password}
                </p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-3 py-3 px-4 rounded-xl font-bold text-xs bg-gradient-to-r from-rose-600 via-red-500 to-amber-500 hover:from-rose-500 hover:to-amber-400 text-white shadow-lg shadow-rose-950/40 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed group"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <>
                  <span>{isRegister ? "Create Account & Sign In" : "Sign In to Workspace"}</span>
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
                </>
              )}
            </button>
          </form>

          {/* Switch link at bottom */}
          <div className="text-center mt-5 pt-4 border-t border-slate-800/80">
            <p className="text-xs text-slate-400">
              {isRegister ? "Already have an account?" : "Don't have an account yet?"}{' '}
              <button
                type="button"
                onClick={() => switchMode(!isRegister)}
                className="font-semibold text-rose-400 hover:text-rose-300 transition-colors"
              >
                {isRegister ? "Sign In" : "Create one now"}
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
