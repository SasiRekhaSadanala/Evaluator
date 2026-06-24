/**
 * Authentication store for Evaluator 2.0.
 * 
 * Manages JWT tokens, user info, and role-based access.
 * Uses localStorage for persistence across page refreshes.
 */

import { API_BASE } from './api'

export interface User {
  id: string
  email: string
  role: 'teacher' | 'student'
  student_id?: string
  display_name: string
}

export interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
}

export const AuthStore = {
  /**
   * Login with username and password.
   * Returns user info on success, throws on failure.
   */
  async login(username: string, password: string): Promise<User> {
    const res = await fetch(`${API_BASE}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    })

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Login failed' }))
      throw new Error(err.detail || 'Login failed')
    }

    const data = await res.json()
    
    if (data.status === 'success' && data.token) {
      localStorage.setItem('auth_token', data.token)
      localStorage.setItem('auth_user', JSON.stringify(data.user))
      return data.user as User
    }

    throw new Error('Invalid response from server')
  },

  /**
   * Logout and clear stored credentials.
   */
  logout(): void {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('auth_user')
  },

  /**
   * Get current auth state from localStorage.
   */
  getState(): AuthState {
    if (typeof window === 'undefined') {
      return { token: null, user: null, isAuthenticated: false }
    }

    const token = localStorage.getItem('auth_token')
    const userStr = localStorage.getItem('auth_user')
    let user: User | null = null

    if (userStr) {
      try {
        user = JSON.parse(userStr) as User
      } catch {
        user = null
      }
    }

    return {
      token,
      user,
      isAuthenticated: !!token && !!user,
    }
  },

  /**
   * Get the JWT token for API requests.
   */
  getToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('auth_token')
  },

  /**
   * Get the current user.
   */
  getUser(): User | null {
    const { user } = this.getState()
    return user
  },

  /**
   * Check if user has a specific role.
   */
  hasRole(role: 'teacher' | 'student'): boolean {
    const { user } = this.getState()
    return user?.role === role
  },

  /**
   * Create an Authorization header for API requests.
   */
  getAuthHeaders(): Record<string, string> {
    const token = this.getToken()
    if (!token) return {}
    return { Authorization: `Bearer ${token}` }
  },

  /**
   * Make an authenticated API request.
   */
  async fetchAuth(url: string, options: RequestInit = {}): Promise<Response> {
    const headers = {
      ...this.getAuthHeaders(),
      ...(options.headers || {}),
    }
    return fetch(url, { ...options, headers })
  },
}
