'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { AuthStore, type User } from '@/lib/auth-store'

const teacherLinks = [
  { href: '/upload', label: 'Upload' },
  { href: '/results', label: 'Results' },
  { href: '/review', label: 'Review Queue' },
]

export default function AppNavbar() {
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

  return (
    <header className="sticky top-0 w-full z-50 bg-obsidian/80 backdrop-blur-xl border-b border-outline-variant/10">
      <nav className="flex justify-between items-center px-8 h-16 max-w-[1440px] mx-auto">
        <div className="flex items-center gap-8">
          <Link href="/" className="font-inter font-extrabold text-xl tracking-tight text-frost">
            Evaluator 2.0
          </Link>
          <div className="hidden md:flex items-center gap-1">
            {teacherLinks.map((link) => {
              const isActive = pathname === link.href || pathname?.startsWith(link.href + '/')
              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive
                      ? 'text-violet-primary bg-violet-primary/10'
                      : 'text-frost-muted hover:text-frost hover:bg-surface-container-high/50'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button className="p-2 text-frost-muted hover:text-violet-primary transition-colors rounded-lg hover:bg-surface-container-high/50">
            <span className="material-symbols-outlined text-[20px]">notifications</span>
          </button>
          <button className="p-2 text-frost-muted hover:text-violet-primary transition-colors rounded-lg hover:bg-surface-container-high/50">
            <span className="material-symbols-outlined text-[20px]">settings</span>
          </button>
          {user ? (
            <div className="relative">
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="h-8 w-8 rounded-full bg-gradient-to-br from-violet-primary to-violet-container flex items-center justify-center text-xs font-bold text-obsidian ml-2 hover:opacity-90 transition-all"
              >
                {user.display_name?.[0]?.toUpperCase() || 'T'}
              </button>
              {menuOpen && (
                <div className="absolute right-0 top-11 w-48 bg-surface-container-high border border-outline-variant/15 rounded-xl shadow-ambient overflow-hidden animate-slide-down z-50">
                  <div className="p-3 border-b border-outline-variant/10">
                    <p className="text-sm font-medium text-frost">{user.display_name || 'Teacher'}</p>
                    <p className="text-[10px] text-frost-muted mt-0.5">{user.email}</p>
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
          ) : (
            <Link
              href="/login"
              className="ml-2 px-4 py-2 bg-gradient-to-r from-violet-primary to-violet-container text-obsidian text-xs font-bold rounded-lg hover:opacity-90 transition-all"
            >
              Sign In
            </Link>
          )}
        </div>
      </nav>
    </header>
  )
}
