'use client'

import Link from 'next/link'
import { useState, useEffect } from 'react'
import { ResultsStore } from '@/lib/results-store'
import type { EvaluationResponse } from '@/lib/results-store'

interface StudentResult {
  id: string
  name: string
  score: number
  maxScore: number
  percentage: number
  feedback: string[]
  status: 'excellent' | 'good' | 'fair' | 'needs-improvement'
}

export default function ResultsPage() {
  const [results, setResults] = useState<StudentResult[]>([])
  const [loading, setLoading] = useState(true)
  const [apiResponse, setApiResponse] = useState<EvaluationResponse | null>(null)

  useEffect(() => {
    // Load results from storage
    const storedResults = ResultsStore.getResults()
    
    if (storedResults && storedResults.status === 'success' && storedResults.results) {
      setApiResponse(storedResults)
      
      // Convert API results to display format
      const formattedResults: StudentResult[] = storedResults.results.map(
        (result, idx) => {
          let status: 'excellent' | 'good' | 'fair' | 'needs-improvement' = 'good'
          if (result.percentage >= 90) status = 'excellent'
          else if (result.percentage >= 80) status = 'good'
          else if (result.percentage >= 70) status = 'fair'
          else status = 'needs-improvement'

          return {
            id: String(idx),
            name: result.submission_id,
            score: result.final_score,
            maxScore: result.max_score,
            percentage: result.percentage,
            feedback: result.feedback,
            status,
          }
        }
      )

      setResults(formattedResults)
    } else {
      // Show placeholder data if no results in storage
      setResults([
        {
          id: '1',
          name: 'No Results',
          score: 0,
          maxScore: 100,
          percentage: 0,
          feedback: ['Upload and evaluate submissions to see results here'],
          status: 'fair',
        },
      ])
    }

    setLoading(false)
  }, [])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'from-green-500/10 border-green-500/30'
      case 'good':
        return 'from-cyan-500/10 border-cyan-500/30'
      case 'fair':
        return 'from-amber-500/10 border-amber-500/30'
      case 'needs-improvement':
        return 'from-red-500/10 border-red-500/30'
      default:
        return 'from-indigo-500/10 border-indigo-500/30'
    }
  }

  const getStatusBadgeColor = (status: string) => {
    switch (status) {
      case 'excellent':
        return 'bg-green-500/20 text-green-300 border border-green-500/30'
      case 'good':
        return 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
      case 'fair':
        return 'bg-amber-500/20 text-amber-300 border border-amber-500/30'
      case 'needs-improvement':
        return 'bg-red-500/20 text-red-300 border border-red-500/30'
      default:
        return 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
    }
  }

  const getScoreColor = (percentage: number) => {
    if (percentage >= 90) return 'text-green-400'
    if (percentage >= 80) return 'text-cyan-400'
    if (percentage >= 70) return 'text-amber-400'
    return 'text-red-400'
  }

  const getScoreBgColor = (percentage: number) => {
    if (percentage >= 90) return 'from-green-500/20 to-green-600/10'
    if (percentage >= 80) return 'from-cyan-500/20 to-cyan-600/10'
    if (percentage >= 70) return 'from-amber-500/20 to-amber-600/10'
    return 'from-red-500/20 to-red-600/10'
  }

  const averageScore =
    results.length > 0 && results[0].name !== 'No Results'
      ? results.reduce((sum, r) => sum + r.percentage, 0) / results.length
      : 0

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-indigo-500/20 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
          <Link href="/" className="text-2xl font-black bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent hover:opacity-80 transition-opacity">
            Assignment Evaluator
          </Link>
          <div className="space-x-6">
            <Link href="/upload" className="text-indigo-300/70 hover:text-indigo-300 transition-colors">
              Upload
            </Link>
            <Link href="/results" className="text-cyan-400 font-semibold hover:text-cyan-300 transition-colors">
              Results
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="mb-12">
          <h1 className="text-5xl font-black text-white mb-3">
            📊 Evaluation Results
          </h1>
          <p className="text-indigo-200/80 text-lg">
            Detailed scores and feedback for all submissions
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-12">
          <div className="bg-gradient-to-br from-indigo-500/10 to-indigo-500/5 backdrop-blur border border-indigo-500/30 rounded-xl p-6 text-center hover:border-indigo-400/60 transition-all">
            <p className="text-indigo-300/70 text-sm font-bold uppercase tracking-wide mb-2">Total Submissions</p>
            <p className="text-4xl font-black text-indigo-300">{results.length > 0 && results[0].name !== 'No Results' ? results.length : '—'}</p>
          </div>
          <div className="bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 backdrop-blur border border-cyan-500/30 rounded-xl p-6 text-center hover:border-cyan-400/60 transition-all">
            <p className="text-cyan-300/70 text-sm font-bold uppercase tracking-wide mb-2">Average Score</p>
            <p className={`text-4xl font-black ${getScoreColor(averageScore)}`}>
              {averageScore > 0 ? `${averageScore.toFixed(1)}%` : '—'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-green-500/10 to-green-500/5 backdrop-blur border border-green-500/30 rounded-xl p-6 text-center hover:border-green-400/60 transition-all">
            <p className="text-green-300/70 text-sm font-bold uppercase tracking-wide mb-2">Highest Score</p>
            <p className="text-4xl font-black text-green-400">
              {results.length > 0 && results[0].name !== 'No Results' ? `${Math.max(...results.map(r => r.percentage))}%` : '—'}
            </p>
          </div>
          <div className="bg-gradient-to-br from-red-500/10 to-red-500/5 backdrop-blur border border-red-500/30 rounded-xl p-6 text-center hover:border-red-400/60 transition-all">
            <p className="text-red-300/70 text-sm font-bold uppercase tracking-wide mb-2">Lowest Score</p>
            <p className="text-4xl font-black text-red-400">
              {results.length > 0 && results[0].name !== 'No Results' ? `${Math.min(...results.map(r => r.percentage))}%` : '—'}
            </p>
          </div>
        </div>

        {/* Results List */}
        <div className="space-y-6 mb-12">
          {results.map((result) => (
            <div
              key={result.id}
              className={`bg-gradient-to-br ${getScoreBgColor(result.percentage)} backdrop-blur border-l-4 border-r border-t border-b border-indigo-500/30 rounded-xl shadow-xl p-8 hover:shadow-2xl hover:shadow-indigo-500/20 transition-all`}
            >
              <div className="flex justify-between items-start mb-6">
                <div>
                  <h3 className="text-2xl font-bold text-white mb-3">
                    {result.name}
                  </h3>
                  <span
                    className={`inline-block px-4 py-2 rounded-full text-xs font-bold ${getStatusBadgeColor(
                      result.status
                    )}`}
                  >
                    {result.status.replace('-', ' ').toUpperCase()}
                  </span>
                </div>
                <div className="text-right">
                  <p className={`text-5xl font-black ${getScoreColor(result.percentage)}`}>
                    {result.percentage}%
                  </p>
                  <p className="text-sm text-indigo-300/70 mt-2">
                    {result.score}/{result.maxScore} points
                  </p>
                </div>
              </div>

              {/* Score Bar */}
              <div className="mb-6 bg-slate-800/50 rounded-full h-3 overflow-hidden border border-indigo-500/20">
                <div
                  style={{ width: `${result.percentage}%` }}
                  className={`h-full transition-all rounded-full ${
                    result.percentage >= 90
                      ? 'bg-gradient-to-r from-green-500 to-green-400'
                      : result.percentage >= 80
                      ? 'bg-gradient-to-r from-cyan-500 to-cyan-400'
                      : result.percentage >= 70
                      ? 'bg-gradient-to-r from-amber-500 to-amber-400'
                      : 'bg-gradient-to-r from-red-500 to-red-400'
                  }`}
                />
              </div>

              {/* Feedback */}
              <div>
                <p className="text-xs font-bold text-indigo-300 mb-4 uppercase tracking-wide">
                  📋 Detailed Feedback
                </p>
                <ul className="space-y-2">
                  {result.feedback.map((item, idx) => (
                    <li key={idx} className="text-sm text-indigo-200/80 flex">
                      <span className="mr-3 text-indigo-400">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex flex-wrap gap-4">
          <Link
            href="/upload"
            className="bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white font-bold py-3 px-8 rounded-lg transition-all hover:shadow-lg hover:shadow-indigo-500/30"
          >
            Evaluate More
          </Link>
          {apiResponse?.csv_output_path && (
            <a
              href={apiResponse.csv_output_path}
              download
              className="bg-gradient-to-r from-cyan-500 to-cyan-600 hover:from-cyan-600 hover:to-cyan-700 text-white font-bold py-3 px-8 rounded-lg transition-all hover:shadow-lg hover:shadow-cyan-500/30"
            >
              📥 Download Summary CSV
            </a>
          )}
          {apiResponse?.csv_detailed_output_path && (
            <a
              href={apiResponse.csv_detailed_output_path}
              download
              className="bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white font-bold py-3 px-8 rounded-lg transition-all hover:shadow-lg hover:shadow-green-500/30"
            >
              📥 Download Detailed CSV
            </a>
          )}
        </div>
      </div>
    </main>
  )
            </p>
          </div>
          <div className="bg-white rounded-lg shadow-md p-6 text-center">
            <p className="text-gray-600 text-sm font-semibold mb-2">Lowest Score</p>
            <p className="text-3xl font-bold text-red-600">
              {Math.min(...results.map(r => r.percentage))}%
            </p>
          </div>
        </div>

        {/* Results List */}
        <div className="space-y-4">
          {results.map((result) => (
            <div
              key={result.id}
              className={`border-l-4 rounded-lg shadow-md p-6 ${getStatusColor(
                result.status
              )}`}
            >
              <div className="flex justify-between items-start mb-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-800">
                    {result.name}
                  </h3>
                  <span
                    className={`inline-block mt-2 px-3 py-1 rounded-full text-xs font-semibold ${getStatusBadgeColor(
                      result.status
                    )}`}
                  >
                    {result.status.replace('-', ' ').toUpperCase()}
                  </span>
                </div>
                <div className="text-right">
                  <p className={`text-4xl font-bold ${getScoreColor(result.percentage)}`}>
                    {result.percentage}%
                  </p>
                  <p className="text-sm text-gray-600">
                    {result.score}/{result.maxScore}
                  </p>
                </div>
              </div>

              {/* Score Bar */}
              <div className="mb-4 bg-gray-300 rounded-full h-2 overflow-hidden">
                <div
                  style={{ width: `${result.percentage}%` }}
                  className={`h-full transition-all ${
                    result.percentage >= 90
                      ? 'bg-green-500'
                      : result.percentage >= 80
                      ? 'bg-blue-500'
                      : result.percentage >= 70
                      ? 'bg-yellow-500'
                      : 'bg-red-500'
                  }`}
                />
              </div>

              {/* Feedback */}
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">
                  Feedback:
                </p>
                <ul className="space-y-1">
                  {result.feedback.map((item, idx) => (
                    <li key={idx} className="text-sm text-gray-700 flex">
                      <span className="mr-2">•</span>
                      <span>{item}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* Actions */}
        <div className="flex gap-4 mt-8">
          <Link
            href="/upload"
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
          >
            Evaluate More Submissions
          </Link>
          {apiResponse?.csv_output_path && (
            <a
              href={apiResponse.csv_output_path}
              download
              className="bg-green-600 hover:bg-green-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              📥 Download CSV (Summary)
            </a>
          )}
          {apiResponse?.csv_detailed_output_path && (
            <a
              href={apiResponse.csv_detailed_output_path}
              download
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition-colors"
            >
              📥 Download CSV (Detailed)
            </a>
          )}
        </div>
      </div>
    </main>
  )
}
