'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import StudentNavbar from '@/components/StudentNavbar'
import { AuthStore } from '@/lib/auth-store'
import { API_BASE } from '@/lib/api'

/* ------------------------------------------------------------------ */
/*  Types                                                              */
/* ------------------------------------------------------------------ */

interface LeaderboardEntry {
  rank: number
  display_name: string
  avg_score: number
  submission_count: number
  is_self: boolean
}

/* ------------------------------------------------------------------ */
/*  Page                                                               */
/* ------------------------------------------------------------------ */

export default function LeaderboardPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [myRank, setMyRank] = useState<number | null>(null)
  const [totalStudents, setTotalStudents] = useState(0)

  useEffect(() => {
    const { isAuthenticated, user } = AuthStore.getState()
    if (!isAuthenticated || user?.role !== 'student') {
      router.push('/login')
      return
    }

    const fetchLeaderboard = async () => {
      try {
        const res = await AuthStore.fetchAuth(`${API_BASE}/api/portal/leaderboard`)
        if (res.ok) {
          const json = await res.json()
          if (json.status === 'success') {
            setEntries(json.leaderboard || [])
            setMyRank(json.my_rank)
            setTotalStudents(json.total_students || 0)
          }
        }
      } catch {
        // Silently handle
      } finally {
        setLoading(false)
      }
    }
    fetchLeaderboard()
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-8 h-8 border-2 border-violet-primary/30 border-t-violet-primary rounded-full animate-spin" />
          <p className="text-sm text-frost-muted">Loading leaderboard...</p>
        </div>
      </div>
    )
  }

  // Score distribution for the mini chart
  const maxAvg = entries.length > 0 ? Math.max(...entries.map(e => e.avg_score)) : 100

  function medalIcon(rank: number) {
    if (rank === 1) return '🥇'
    if (rank === 2) return '🥈'
    if (rank === 3) return '🥉'
    return null
  }

  function scoreColor(score: number) {
    if (score >= 85) return 'text-emerald-trust'
    if (score >= 70) return 'text-violet-primary'
    if (score >= 50) return 'text-yellow-400'
    return 'text-coral'
  }

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <StudentNavbar />

      <main className="flex-1 max-w-[1440px] mx-auto w-full px-8 py-10">
        {/* Header */}
        <section className="mb-10 animate-fade-in">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
            <div>
              <h1 className="text-4xl font-bold text-frost tracking-tight mb-2">Class Leaderboard</h1>
              <p className="text-frost-muted text-base">
                {totalStudents} students · Rankings are anonymized for privacy
              </p>
            </div>
            {myRank && (
              <div className="flex items-center gap-3">
                <div className="px-4 py-2 bg-gradient-to-r from-violet-primary to-violet-container rounded-xl text-obsidian font-bold text-sm">
                  Your Rank: #{myRank} of {totalStudents}
                </div>
              </div>
            )}
          </div>
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Table */}
          <div className="lg:col-span-8 bg-surface-container-low rounded-xl border border-outline-variant/10 overflow-hidden">
            <div className="p-6 border-b border-outline-variant/10">
              <h3 className="text-lg font-semibold text-frost">Rankings by Average Score</h3>
              <p className="text-xs text-frost-muted mt-1">Based on all evaluated submissions</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-outline-variant/10 text-frost-muted text-xs">
                    <th className="text-left py-3 px-6 font-semibold uppercase tracking-wider w-16">Rank</th>
                    <th className="text-left py-3 px-6 font-semibold uppercase tracking-wider">Student</th>
                    <th className="text-center py-3 px-6 font-semibold uppercase tracking-wider">Submissions</th>
                    <th className="text-right py-3 px-6 font-semibold uppercase tracking-wider">Avg Score</th>
                    <th className="text-right py-3 px-6 font-semibold uppercase tracking-wider w-32">Bar</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr
                      key={entry.rank}
                      className={`border-b border-outline-variant/5 transition-colors ${
                        entry.is_self
                          ? 'bg-violet-primary/8 hover:bg-violet-primary/12 border-l-2 border-l-violet-primary'
                          : 'hover:bg-surface-container-highest/20'
                      }`}
                    >
                      <td className="py-3.5 px-6">
                        <div className="flex items-center gap-1.5">
                          {medalIcon(entry.rank) ? (
                            <span className="text-lg">{medalIcon(entry.rank)}</span>
                          ) : (
                            <span className="font-mono text-frost-muted text-xs">#{entry.rank}</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3.5 px-6">
                        <div className="flex items-center gap-3">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold ${
                            entry.is_self
                              ? 'bg-gradient-to-br from-violet-primary to-violet-container text-obsidian'
                              : 'bg-surface-container-highest text-frost-muted'
                          }`}>
                            {entry.is_self ? 'You' : `#${entry.rank}`}
                          </div>
                          <span className={`font-medium ${entry.is_self ? 'text-violet-primary' : 'text-frost'}`}>
                            {entry.display_name}
                            {entry.is_self && (
                              <span className="ml-2 px-2 py-0.5 bg-violet-primary/15 text-violet-primary text-[10px] font-medium rounded-full">
                                You
                              </span>
                            )}
                          </span>
                        </div>
                      </td>
                      <td className="py-3.5 px-6 text-center font-mono text-frost-muted text-xs">
                        {entry.submission_count}
                      </td>
                      <td className={`py-3.5 px-6 text-right font-mono font-bold ${scoreColor(entry.avg_score)}`}>
                        {entry.avg_score.toFixed(1)}
                      </td>
                      <td className="py-3.5 px-6">
                        <div className="w-full h-2 bg-surface-container-highest rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${
                              entry.is_self ? 'bg-gradient-to-r from-violet-primary to-violet-container' : 'bg-frost-muted/30'
                            }`}
                            style={{ width: `${(entry.avg_score / maxAvg) * 100}%` }}
                          />
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Side Panel */}
          <div className="lg:col-span-4 space-y-6">
            {/* Your Position */}
            {myRank && (
              <div className="bg-gradient-to-br from-violet-container/80 to-primary-dim/80 rounded-xl p-6 relative overflow-hidden shadow-lg">
                <div className="absolute top-0 right-0 p-2 opacity-10">
                  <span className="material-symbols-outlined text-7xl">leaderboard</span>
                </div>
                <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-2">Your Position</p>
                <div className="text-5xl font-bold text-white mb-1">
                  #{myRank}
                </div>
                <p className="text-sm text-white/70">out of {totalStudents} students</p>
                <p className="text-xs text-white/50 mt-2">
                  Top {totalStudents > 0 ? Math.round((myRank / totalStudents) * 100) : 0}%
                </p>
              </div>
            )}

            {/* Score Distribution */}
            <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
              <h3 className="text-sm font-semibold text-frost mb-4">Score Distribution</h3>
              <div className="h-32 flex items-end justify-between gap-1">
                {entries.map((entry, i) => (
                  <div key={i} className="flex-1 flex flex-col items-center">
                    <div
                      className={`w-full max-w-[20px] rounded-t transition-all duration-500 mx-auto ${
                        entry.is_self
                          ? 'bg-violet-primary shadow-[0_0_8px_rgba(192,193,255,0.4)]'
                          : 'bg-surface-container-highest/60'
                      }`}
                      style={{ height: `${Math.max(4, (entry.avg_score / maxAvg) * 100)}%` }}
                    />
                  </div>
                ))}
              </div>
              <div className="flex justify-between mt-2">
                <span className="text-[9px] text-frost-muted">Rank #1</span>
                <span className="text-[9px] text-frost-muted">Rank #{totalStudents}</span>
              </div>
            </div>

            {/* Privacy Note */}
            <div className="bg-surface-container/50 rounded-xl border border-outline-variant/5 p-4">
              <div className="flex items-start gap-3">
                <span className="material-symbols-outlined text-violet-primary text-lg mt-0.5">shield</span>
                <div>
                  <p className="text-xs font-semibold text-frost mb-1">Privacy Protected</p>
                  <p className="text-[11px] text-frost-muted leading-relaxed">
                    Other students&apos; identities are anonymized. Only you can see your highlighted position.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>

      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: 'radial-gradient(#c0c1ff 1px, transparent 1px)', backgroundSize: '32px 32px' }} />
    </div>
  )
}
