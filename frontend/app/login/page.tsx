'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { AuthStore } from '@/lib/auth-store'

export default function LoginPage() {
  const router = useRouter()
  const [role, setRole] = useState<'student' | 'teacher'>('student')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // Redirect if already logged in
  useEffect(() => {
    const { isAuthenticated, user } = AuthStore.getState()
    if (isAuthenticated && user) {
      router.push(user.role === 'teacher' ? '/upload' : '/portal')
    }
  }, [router])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      const user = await AuthStore.login(username, password)
      if (user.role === 'teacher') {
        router.push('/upload')
      } else {
        router.push('/portal')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Panel — Branding */}
      <div className="hidden lg:flex lg:w-[55%] relative overflow-hidden items-center justify-center">
        {/* Background effects */}
        <div className="absolute inset-0 bg-obsidian" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] rounded-full bg-violet-primary/10 blur-[120px] animate-glow" />
        <div className="absolute bottom-20 right-20 w-[300px] h-[300px] rounded-full bg-violet-container/8 blur-[100px] animate-glow stagger-3" />
        <div className="absolute top-20 left-20 w-[200px] h-[200px] rounded-full bg-emerald-trust/5 blur-[80px] animate-glow stagger-2" />

        {/* Dot grid */}
        <div className="absolute inset-0 opacity-[0.03]"
          style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />

        {/* Geometric shapes */}
        <div className="absolute top-1/4 right-1/4 w-32 h-32 border border-violet-primary/20 rounded-2xl rotate-12 animate-float" />
        <div className="absolute bottom-1/3 left-1/4 w-24 h-24 border border-violet-container/15 rounded-xl -rotate-6 animate-float stagger-2" />
        <div className="absolute top-1/3 left-1/3 w-16 h-16 border border-emerald-trust/10 rounded-lg rotate-45 animate-float stagger-4" />

        {/* Content */}
        <div className="relative z-10 text-center px-12 max-w-lg">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-surface-container/60 border border-outline-variant/10 mb-8">
            <span className="w-2 h-2 rounded-full bg-emerald-trust animate-pulse" />
            <span className="text-frost-muted text-xs font-medium tracking-wide uppercase">AI-Powered Assessment</span>
          </div>

          <h1 className="text-5xl font-black text-frost leading-tight tracking-tight mb-4">
            Evaluator
            <span className="bg-gradient-to-r from-violet-primary to-violet-container bg-clip-text text-transparent"> 2.0</span>
          </h1>

          <p className="text-frost-muted text-lg leading-relaxed mb-8">
            Intelligent academic grading with multi-agent AI analysis,
            semantic understanding, and personalized feedback.
          </p>

          {/* Decorative mini-dashboard */}
          <div className="bg-surface-container-low/60 backdrop-blur-sm rounded-xl border border-outline-variant/10 p-4 text-left">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-2.5 h-2.5 rounded-full bg-coral/60" />
              <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
              <div className="w-2.5 h-2.5 rounded-full bg-emerald-trust/50" />
              <div className="ml-3 h-4 flex-1 rounded-full bg-surface-container-highest/40" />
            </div>
            {[
              { name: 'student_01.py', score: 92 },
              { name: 'report.txt', score: 78 },
              { name: 'algo_hw3.cpp', score: 85 },
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 py-1.5">
                <span className="text-frost-muted text-xs w-28 truncate font-mono">{item.name}</span>
                <div className="flex-1 h-1.5 rounded-full bg-surface-container-highest/40">
                  <div
                    className={`h-full rounded-full ${item.score >= 85 ? 'bg-emerald-trust/70' : 'bg-violet-primary/60'}`}
                    style={{ width: `${item.score}%` }}
                  />
                </div>
                <span className="text-frost text-xs font-bold font-mono w-8 text-right">{item.score}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel — Login Form */}
      <div className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="w-full max-w-md">
          {/* Mobile logo */}
          <div className="lg:hidden text-center mb-10">
            <h1 className="text-3xl font-black text-frost tracking-tight">
              Evaluator <span className="bg-gradient-to-r from-violet-primary to-violet-container bg-clip-text text-transparent">2.0</span>
            </h1>
          </div>

          {/* Login card */}
          <div className="glass-panel rounded-2xl p-8 shadow-ambient">
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-frost mb-2">Welcome back</h2>
              <p className="text-frost-muted text-sm">Sign in to continue to your dashboard</p>
            </div>

            {/* Role toggle */}
            <div className="flex bg-surface-container-lowest rounded-xl p-1 mb-6 border border-outline-variant/10">
              {(['student', 'teacher'] as const).map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => { setRole(r); setError('') }}
                  className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all duration-200 ${
                    role === r
                      ? 'bg-gradient-to-r from-violet-primary to-violet-container text-obsidian shadow-violet-glow'
                      : 'text-frost-muted hover:text-frost'
                  }`}
                >
                  <span className="flex items-center justify-center gap-2">
                    <span className="material-symbols-outlined text-[18px]">
                      {r === 'teacher' ? 'school' : 'person'}
                    </span>
                    {r.charAt(0).toUpperCase() + r.slice(1)}
                  </span>
                </button>
              ))}
            </div>

            <form onSubmit={handleLogin} className="space-y-4">
              {/* Username */}
              <div>
                <label className="block text-xs font-semibold text-frost-muted uppercase tracking-wider mb-2">
                  {role === 'teacher' ? 'Username' : 'Student ID'}
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-frost-muted">
                    {role === 'teacher' ? 'mail' : 'badge'}
                  </span>
                  <input
                    id="login-username"
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder={role === 'teacher' ? 'teacher' : 'e.g. student_ravi'}
                    className="w-full pl-10 pr-4 py-3 bg-surface-container-lowest border border-outline-variant/15 rounded-xl text-frost placeholder:text-frost-muted/50 focus:outline-none focus:border-violet-primary/50 focus:ring-1 focus:ring-violet-primary/20 transition-all text-sm"
                    required
                  />
                </div>
              </div>

              {/* Password */}
              <div>
                <label className="block text-xs font-semibold text-frost-muted uppercase tracking-wider mb-2">Password</label>
                <div className="relative">
                  <span className="absolute left-3 top-1/2 -translate-y-1/2 material-symbols-outlined text-[18px] text-frost-muted">lock</span>
                  <input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder={role === 'teacher' ? '••••••••' : 'Same as your student ID'}
                    className="w-full pl-10 pr-4 py-3 bg-surface-container-lowest border border-outline-variant/15 rounded-xl text-frost placeholder:text-frost-muted/50 focus:outline-none focus:border-violet-primary/50 focus:ring-1 focus:ring-violet-primary/20 transition-all text-sm"
                    required
                  />
                </div>
              </div>

              {/* Error */}
              {error && (
                <div className="flex items-center gap-2 p-3 bg-error/10 border border-error/20 rounded-lg animate-slide-down">
                  <span className="material-symbols-outlined text-[16px] text-error">error</span>
                  <span className="text-error text-sm">{error}</span>
                </div>
              )}

              {/* Submit */}
              <button
                id="login-submit"
                type="submit"
                disabled={loading}
                className="w-full py-3.5 bg-gradient-to-r from-violet-primary to-violet-container text-obsidian font-bold rounded-xl hover:opacity-90 transition-all shadow-violet-glow disabled:opacity-50 disabled:cursor-not-allowed text-sm flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-obsidian/30 border-t-obsidian rounded-full animate-spin" />
                    Signing in...
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined text-[18px]">login</span>
                    Sign In
                  </>
                )}
              </button>
            </form>

            {/* Divider */}
            <div className="my-6 flex items-center gap-3">
              <div className="flex-1 h-px bg-outline-variant/15" />
              <span className="text-frost-muted text-[10px] uppercase tracking-widest">Info</span>
              <div className="flex-1 h-px bg-outline-variant/15" />
            </div>

            {/* Help text */}
            <div className="space-y-2">
              <p className="text-frost-muted text-xs text-center">
                <span className="text-violet-primary font-medium">Students:</span> Use your student ID as both username and password
              </p>
              <p className="text-frost-muted text-xs text-center">
                <span className="text-violet-primary font-medium">Teachers:</span> Username: <span className="font-mono text-frost/70">teacher</span> · Password: <span className="font-mono text-frost/70">teacher</span>
              </p>
            </div>
          </div>

          {/* Footer */}
          <p className="text-center text-frost-muted/40 text-[10px] mt-6 tracking-wider">
            Evaluator 2.0 · AI-Powered Academic Assessment
          </p>
        </div>
      </div>

      {/* Background pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.012] z-[-1]"
        style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
    </div>
  )
}
