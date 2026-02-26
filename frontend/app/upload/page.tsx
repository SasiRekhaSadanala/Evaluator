'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import FileUpload, { type FileUploadData } from '@/components/FileUpload'
import { ResultsStore, type EvaluationResponse } from '@/lib/results-store'

const API_BASE_URL = 'http://127.0.0.1:8000'

export default function UploadPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState<'info' | 'success' | 'error'>('info')

  const handleFileUploadSubmit = async (data: FileUploadData) => {
    setLoading(true)
    setMessage('Submitting evaluation request...')
    setMessageType('info')

    try {
      // Create FormData for multipart request
      const formData = new FormData()

      // Add files
      data.files.forEach((file) => {
        formData.append('files', file)
      })

      // Use the user-selected assignment type
      formData.append('assignment_type', data.assignmentType)

      if (data.problemStatement) {
        formData.append('problem_statement', data.problemStatement)
      }

      if (data.rubric) {
        formData.append('rubric_content', data.rubric)
      }

      // Log for debugging
      console.log('Submitting assignment_type:', data.assignmentType);
      console.log('Files:', data.files.map(f => f.name));

      // Call backend API
      const res = await fetch(`${API_BASE_URL}/api/evaluate`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(
          errorData.detail || `API error: ${res.status} ${res.statusText}`
        )
      }

      const result: EvaluationResponse = await res.json()

      if (result.status === 'success') {
        // Store results for results page
        ResultsStore.setResults(result)

        setMessage(
          `✓ ${result.message} - Evaluated ${result.summary?.total_submissions || 0} submissions`
        )
        setMessageType('success')

        // Redirect to results after 1 second
        setTimeout(() => {
          router.push('/results')
        }, 1000)
      } else {
        setMessage(`✗ Evaluation failed: ${result.message}`)
        setMessageType('error')
      }
    } catch (error) {
      const errorMsg =
        error instanceof Error ? error.message : 'Unknown error occurred'
      setMessage(
        `✗ Error: ${errorMsg}. Make sure the backend is running on ${API_BASE_URL}`
      )
      setMessageType('error')
      console.error('API Error:', error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-indigo-900/40 via-slate-950 to-slate-950 relative overflow-hidden">

      {/* Background decoration */}
      <div className="absolute top-0 left-0 w-full h-96 bg-gradient-to-b from-indigo-500/10 to-transparent pointer-events-none" />
      <div className="absolute top-[-10%] right-[-5%] w-96 h-96 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute top-[20%] left-[-10%] w-72 h-72 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Navigation */}
      <nav className="border-b border-indigo-500/10 backdrop-blur-md sticky top-0 z-50 bg-slate-950/50">
        <div className="max-w-7xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg group-hover:shadow-indigo-500/25 transition-all">
              <span className="text-white font-bold text-lg">A</span>
            </div>
            <span className="text-xl font-bold text-slate-200 group-hover:text-white transition-colors">
              Assignment Evaluator
            </span>
          </Link>
          <div className="flex items-center gap-6">
            <Link href="/upload" className="text-indigo-400 font-medium border-b-2 border-indigo-400 pb-0.5">
              Upload
            </Link>
            <Link href="/results" className="text-slate-400 hover:text-white transition-colors font-medium">
              Results
            </Link>
          </div>
        </div>
      </nav>

      <div className="max-w-7xl mx-auto px-6 py-12 relative z-10">
        <div className="mb-12 text-center max-w-2xl mx-auto">
          <h1 className="text-4xl md:text-5xl font-black text-white mb-6 tracking-tight">
            Upload & <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">Evaluate</span>
          </h1>
          <p className="text-lg text-slate-400 leading-relaxed">
            Submit your student files and let our AI-powered system provide instant, detailed feedback and grading based on your criteria.
          </p>
        </div>

        {/* Message Banner */}
        {message && (
          <div className={`max-w-5xl mx-auto mb-8 p-4 rounded-xl border backdrop-blur-md flex items-center gap-3 animate-slide-up ${messageType === 'success'
            ? 'bg-green-500/10 border-green-500/50 text-green-300'
            : messageType === 'error'
              ? 'bg-red-500/10 border-red-500/50 text-red-300'
              : 'bg-indigo-500/10 border-indigo-500/50 text-indigo-300'
            }`}>
            <span className="text-2xl">
              {messageType === 'success' ? '✅' : messageType === 'error' ? '🚫' : 'ℹ️'}
            </span>
            <p className="font-medium">{message}</p>
          </div>
        )}

        {/* Main Upload Component */}
        <FileUpload
          onSubmit={handleFileUploadSubmit}
          loading={loading}
        />

        {/* Help Section */}
        <div className="mt-20 grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-indigo-500/10 flex items-center justify-center mb-4 text-2xl">
              📂
            </div>
            <h3 className="text-white font-bold mb-2">Multiple Formats</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Support for Python scripts (.py), text documents (.txt), and PDF files (.pdf) for versatile assignment types.
            </p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center mb-4 text-2xl">
              🤖
            </div>
            <h3 className="text-white font-bold mb-2">AI Analysis</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Advanced AI models analyze code logic, structure, and content quality against your specific rubric.
            </p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded-2xl p-6 hover:border-slate-700 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center mb-4 text-2xl">
              📊
            </div>
            <h3 className="text-white font-bold mb-2">Detailed Results</h3>
            <p className="text-slate-400 text-sm leading-relaxed">
              Get comprehensive reports with scores, inline feedback, and areas for improvement for each student.
            </p>
          </div>
        </div>
      </div>
    </main>
  )
}
