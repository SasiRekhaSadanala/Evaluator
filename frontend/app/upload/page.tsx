'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import AppNavbar from '@/components/AppNavbar'
import FileUpload, { type FileUploadData } from '@/components/FileUpload'
import { ResultsStore, type EvaluationResponse } from '@/lib/results-store'

import { API_BASE } from '@/lib/api'

export default function UploadPage() {
  const router = useRouter()
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState<'info' | 'success' | 'error'>('info')

  const handleFileUploadSubmit = async (data: FileUploadData) => {
    setLoading(true)
    const fileCount = data.files.length
    const estMinutes = Math.max(1, Math.ceil(fileCount / 20))
    setMessage(
      fileCount > 10
        ? `Evaluating ${fileCount} submissions — estimated ${estMinutes}-${estMinutes + 2} minutes. Please don't close this tab.`
        : 'Connecting to evaluation engine...'
    )
    setMessageType('info')

    try {
      const formData = new FormData()
      data.files.forEach((file) => {
        formData.append('files', file)
      })

      formData.append('assignment_type', data.assignmentType)

      if (data.problemStatement) {
        formData.append('problem_statement', data.problemStatement)
      }

      if (data.rubric) {
        formData.append('rubric_content', data.rubric)
      }

      if (data.topic) {
        formData.append('topic', data.topic)
      }

      if (data.testCases) {
        formData.append('test_cases', data.testCases)
      }

      if (data.transcriptText) {
        formData.append('transcript_text', data.transcriptText)
      }

      const res = await fetch(`${API_BASE}/api/evaluate`, {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}))
        throw new Error(
          errorData.detail || `Server error: ${res.status}`
        )
      }

      const result: EvaluationResponse = await res.json()

      if (result.status === 'success') {
        ResultsStore.setResults(result)
        setMessage(`Successfully evaluated ${result.summary?.total_submissions || 0} submissions.`)
        setMessageType('success')
        setTimeout(() => {
          router.push('/results')
        }, 800)
      } else {
        setMessage('Evaluation failed. Please try again.')
        setMessageType('error')
      }
    } catch (error) {
      const msg = error instanceof Error ? error.message : 'Connection failed. Is the backend running?'
      setMessage(msg)
      setMessageType('error')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-frost flex flex-col">
      <AppNavbar />

      <main className="flex-grow max-w-[1440px] mx-auto w-full px-8 py-10">
        {/* Status Message */}
        {message && (
          <div className={`mb-8 p-4 rounded-xl border animate-slide-up flex items-center gap-3 ${
            messageType === 'success'
              ? 'bg-emerald-trust/5 border-emerald-trust/20 text-emerald-trust'
              : messageType === 'error'
                ? 'bg-coral/5 border-coral/20 text-coral'
                : 'bg-violet-primary/5 border-violet-primary/20 text-violet-primary'
          }`}>
            <span className="material-symbols-outlined text-[20px]">
              {messageType === 'success' ? 'check_circle' : messageType === 'error' ? 'error' : 'info'}
            </span>
            <p className="text-sm font-medium">{message}</p>
          </div>
        )}

        {/* Page Header */}
        <section className="mb-10">
          <h1 className="text-4xl font-bold text-frost tracking-tight mb-2">
            Upload Submissions
          </h1>
          <p className="text-frost-muted text-base">
            Upload student assignments for AI-powered evaluation and feedback.
          </p>
        </section>

        {/* Two Column Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Upload Form */}
          <div className="lg:col-span-2">
            <FileUpload
              onSubmit={handleFileUploadSubmit}
              loading={loading}
            />
          </div>

          {/* Right: Sidebar */}
          <div className="space-y-6">
            {/* System Status */}
            <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className="w-2 h-2 rounded-full bg-emerald-trust animate-pulse" />
                <span className="text-xs font-semibold uppercase tracking-wider text-frost-muted">System Status</span>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <span className="text-sm text-frost-muted">Engine</span>
                  <span className="text-sm font-medium text-emerald-trust">Operational</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-frost-muted">Queue</span>
                  <span className="text-sm font-medium text-frost">Ready</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-sm text-frost-muted">Avg. Processing</span>
                  <span className="text-sm font-medium text-frost">~12s / file</span>
                </div>
              </div>
            </div>

            {/* Accepted Formats */}
            <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-frost-muted mb-4">
                Accepted Formats
              </h3>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { ext: '.py', label: 'Python' },
                  { ext: '.cpp', label: 'C++' },
                  { ext: '.cc', label: 'C++' },
                  { ext: '.h', label: 'Header' },
                  { ext: '.txt', label: 'Text' },
                  { ext: '.pdf', label: 'PDF' },
                  { ext: '.html', label: 'HTML' },
                  { ext: '.zip', label: 'ZIP Archive' },
                ].map((fmt) => (
                  <div key={fmt.ext} className="flex items-center gap-2 text-sm text-frost-muted">
                    <span className="material-symbols-outlined text-[14px] text-violet-primary">check</span>
                    <span className="font-mono text-xs">{fmt.ext}</span>
                    <span className="text-xs text-frost-muted/60">{fmt.label}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tips */}
            <div className="bg-violet-primary/5 rounded-xl border border-violet-primary/10 p-6">
              <div className="flex items-center gap-2 mb-3">
                <span className="material-symbols-outlined text-[18px] text-violet-primary">lightbulb</span>
                <span className="text-xs font-semibold text-violet-primary">Quick Tips</span>
              </div>
              <ul className="space-y-2 text-xs text-frost-muted leading-relaxed">
                <li>• Upload multiple files at once for batch evaluation</li>
                <li>• Add a rubric for more accurate scoring</li>
                <li>• Test cases enable automated pass-rate calculation</li>
                <li>• Results are saved for review across sessions</li>
              </ul>
            </div>
          </div>
        </div>
      </main>

      {/* Subtle background pattern */}
      <div className="fixed inset-0 pointer-events-none opacity-[0.015] z-[-1]"
        style={{ backgroundImage: `radial-gradient(#c0c1ff 1px, transparent 1px)`, backgroundSize: '32px 32px' }} />
    </div>
  )
}
