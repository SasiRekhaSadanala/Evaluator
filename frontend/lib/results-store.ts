'use client'

import { API_BASE } from './api'

export interface EvaluationResult {
  submission_id: string
  final_score: number
  max_score: number
  percentage: number
  feedback: string[]
  assignment_type: string
  file: string
  flag_score?: number
  flag_reasons?: string[]
  percentile?: number
  improvement_delta?: number
  trend?: string
  batch_id?: string
  evaluated_at?: string
}

export interface EvaluationResponse {
  status: string
  message: string
  results?: EvaluationResult[]
  summary?: {
    total_submissions: number
    average_score: number
    average_percentage: number
    highest_score: number
    lowest_score: number
  }
  csv_output_path?: string
  csv_detailed_output_path?: string
  error_message?: string
}

const STORAGE_KEY = 'evaluation_results'

export const ResultsStore = {
  setResults: (results: EvaluationResponse) => {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(results))
    }
  },

  getResults: (): EvaluationResponse | null => {
    if (typeof window !== 'undefined') {
      const data = sessionStorage.getItem(STORAGE_KEY)
      return data ? JSON.parse(data) : null
    }
    return null
  },

  clearResults: () => {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(STORAGE_KEY)
    }
  },

  /**
   * Fetch all historical evaluation results from the backend DB.
   * Falls back to sessionStorage if the API is unavailable.
   */
  fetchHistory: async (): Promise<{
    results: EvaluationResult[]
    batches: Array<{
      batch_id: string
      assignment_type: string
      total_submissions: number
      average_score: number
      average_percentage: number
      highest_score: number
      lowest_score: number
      csv_output_path?: string
      csv_detailed_output_path?: string
      evaluated_at: string
    }>
  }> => {
    try {
      const res = await fetch(`${API_BASE}/api/evaluations/history`)
      if (res.ok) {
        const data = await res.json()
        if (data.status === 'success') {
          return {
            results: data.all_results || [],
            batches: data.batches || [],
          }
        }
      }
    } catch {
      // Backend unavailable — fall through
    }

    // Fallback: return session-stored results
    const session = ResultsStore.getResults()
    if (session?.results) {
      return {
        results: session.results,
        batches: session.summary
          ? [{ batch_id: 'session', evaluated_at: new Date().toISOString(), ...session.summary, assignment_type: session.results[0]?.assignment_type || '' }]
          : [],
      }
    }

    return { results: [], batches: [] }
  },
}
