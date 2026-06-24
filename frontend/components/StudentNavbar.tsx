'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { AuthStore, type User } from '@/lib/auth-store'

const studentLinks = [
  { href: '/portal', label: 'Dashboard', icon: 'dashboard' },
  { href: '/portal/submissions', label: 'My Submissions', icon: 'assignment' },
  { href: '/portal/progress', label: 'Progress', icon: 'trending_up' },
  { href: '/portal/leaderboard', label: 'Leaderboard', icon: 'leaderboard' },
  { href: '/portal/coach', label: 'AI Coach', icon: 'auto_awesome' },
]

export default function StudentNavbar() {
  const pathname = usePathname()
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)

  useEffect(() => {
    setUser(AuthStore.getUser())
  }, [])

  const handleLogout = () => {
    AuthStore.logout()
    router.push('/login')
  }

  const initials = user?.display_name
    ? user.display_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'S'

  return (
    <header className="sticky top-0 w-full z-50 bg-obsidian/80 backdrop-blur-xl border-b border-outline-variant/10">
      <nav className="flex justify-between items-center px-8 h-16 max-w-[1440px] mx-auto">
        <div className="flex items-center gap-8">
          <Link href="/portal" className="font-inter font-extrabold text-xl tracking-tight text-frost flex items-center gap-2">
            <span className="bg-gradient-to-r from-violet-primary to-violet-container bg-clip-text text-transparent">E</span>
            Evaluator 2.0
          </Link>
          <div className="hidden md:flex items-center gap-1">
            {studentLinks.map((link) => {
              const isActive = pathname === link.href || (link.href !== '/portal' && pathname?.startsWith(link.href))
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 flex items-center gap-2 ${
                    isActive
                      ? 'text-violet-primary bg-violet-primary/10'
                      : 'text-frost-muted hover:text-frost hover:bg-surface-container-high/50'
                  }`}
                >
                  <span className="material-symbols-outlined text-[18px]">{link.icon}</span>
                  {link.label}
                </Link>
              )
            })}
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* User info */}
          <div className="hidden sm:flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs font-medium text-frost leading-none">{user?.display_name || 'Student'}</p>
              <p className="text-[10px] text-frost-muted leading-none mt-1">{user?.student_id || ''}</p>
            </div>
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="h-9 w-9 rounded-full bg-gradient-to-br from-emerald-trust to-emerald-trust/70 flex items-center justify-center text-xs font-bold text-obsidian hover:opacity-90 transition-all"
              >
                {initials}
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-12 w-48 bg-surface-container-high border border-outline-variant/15 rounded-xl shadow-ambient overflow-hidden animate-slide-down">
                  <div className="p-3 border-b border-outline-variant/10">
                    <p className="text-sm font-medium text-frost">{user?.display_name}</p>
                    <p className="text-[10px] text-frost-muted mt-0.5">{user?.email}</p>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full px-3 py-2.5 text-left text-sm text-coral hover:bg-error/5 transition-colors flex items-center gap-2"
                  >
                    <span className="material-symbols-outlined text-[16px]">logout</span>
                    Sign Out
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Mobile logout */}
          <button
            onClick={handleLogout}
            className="sm:hidden p-2 text-frost-muted hover:text-coral transition-colors rounded-lg"
          >
            <span className="material-symbols-outlined text-[20px]">logout</span>
          </button>
        </div>
      </nav>
    </header>
  )
}
