'use client'

import { useState, useRef } from 'react'

interface FileUploadProps {
  onSubmit?: (data: FileUploadData) => void
  onFileChange?: (files: File[]) => void
  loading?: boolean
}

export interface FileUploadData {
  files: File[]
  problemStatement: string
  rubric: string | null
  rubricSource: 'text' | 'file'
}

export default function FileUpload({ onSubmit, onFileChange, loading }: FileUploadProps) {
  // File upload state
  const [files, setFiles] = useState<File[]>([])
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const rubricInputRef = useRef<HTMLInputElement>(null)

  const [problemStatement, setProblemStatement] = useState('')
  const [rubricSource, setRubricSource] = useState<'text' | 'file'>('text')
  const [rubricText, setRubricText] = useState('')
  const [rubricFile, setRubricFile] = useState<File | null>(null)
  const [errors, setErrors] = useState<string[]>([])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files)
    }
  }

  const handleFileSelect = (selectedFiles: FileList | null) => {
    if (!selectedFiles) return

    const newFiles: File[] = []
    const allowedExtensions = ['.py', '.txt', '.pdf']

    Array.from(selectedFiles).forEach((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (allowedExtensions.includes(ext)) {
        if (!files.some((f) => f.name === file.name)) {
          newFiles.push(file)
        }
      } else {
        setErrors((prev) => [...prev, `File type not supported: ${file.name}`])
      }
    })

    if (newFiles.length > 0) {
      const updatedFiles = [...files, ...newFiles]
      setFiles(updatedFiles)
      onFileChange?.(updatedFiles)
      setErrors((prev) => prev.filter((e) => !e.startsWith('File type')))
    }
  }

  const removeFile = (index: number) => {
    const updatedFiles = files.filter((_, i) => i !== index)
    setFiles(updatedFiles)
    onFileChange?.(updatedFiles)
  }

  const handleRubricFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0]
      if (file.name.endsWith('.json')) {
        setRubricFile(file)
        setErrors((prev) => prev.filter((e) => !e.includes('rubric')))
      } else {
        setErrors((prev) => [...prev, 'Rubric must be a JSON file'])
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const formErrors: string[] = []
    if (files.length === 0) formErrors.push('Please upload at least one student submission')

    if (rubricSource === 'text' && rubricText) {
      try {
        JSON.parse(rubricText)
      } catch (err) {
        formErrors.push('Invalid JSON in rubric text')
      }
    }

    if (formErrors.length > 0) {
      setErrors(formErrors)
      return
    }

    let finalRubric = null
    if (rubricSource === 'text') {
      finalRubric = rubricText
    } else if (rubricSource === 'file' && rubricFile) {
      try {
        finalRubric = await rubricFile.text()
        JSON.parse(finalRubric) // Validate JSON
      } catch (err) {
        setErrors(['Invalid JSON in rubric file'])
        return
      }
    }

    if (onSubmit) {
      onSubmit({
        files,
        problemStatement,
        rubric: finalRubric,
        rubricSource,
      })
    }
  }

  return (
    <div className="w-full max-w-5xl mx-auto space-y-8">
      <form onSubmit={handleSubmit} className="space-y-8">

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="bg-red-500/10 border-l-4 border-red-500 p-4 rounded-r-lg animate-fade-in">
            <div className="flex items-start">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-200">Please correct the following errors:</h3>
                <ul className="mt-2 text-sm text-red-300 list-disc list-inside space-y-1">
                  {errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column: File Upload */}
          <div className="space-y-6">
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="text-2xl">📂</span> Student Submissions
                </h2>
                <span className="px-3 py-1 text-xs font-medium text-indigo-300 bg-indigo-500/10 rounded-full border border-indigo-500/20">
                  Required
                </span>
              </div>

              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                className={`relative group cursor-pointer transition-all duration-300 ease-in-out border-2 border-dashed rounded-xl h-64 flex flex-col items-center justify-center text-center p-8 ${dragActive
                    ? 'border-indigo-500 bg-indigo-500/10 scale-[1.02]'
                    : 'border-slate-600 hover:border-indigo-400 bg-slate-800/30 hover:bg-slate-800/50'
                  }`}
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={(e) => handleFileSelect(e.target.files)}
                  multiple
                  accept=".py,.txt,.pdf"
                  className="hidden"
                />

                <div className={`transition-transform duration-300 ${dragActive ? 'scale-110' : 'group-hover:scale-110'}`}>
                  <div className="w-16 h-16 mb-4 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
                    <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                    </svg>
                  </div>
                </div>

                <h3 className="text-lg font-semibold text-white mb-2">
                  {dragActive ? 'Drop files now' : 'Click or Drag files'}
                </h3>
                <p className="text-sm text-slate-400 max-w-xs mx-auto">
                  Upload Python (.py), Text (.txt), or PDF (.pdf) files to begin evaluation
                </p>
              </div>

              {files.length > 0 && (
                <div className="mt-6 space-y-3">
                  <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">
                    Selected Files ({files.length})
                  </p>
                  <div className="max-h-60 overflow-y-auto pr-2 space-y-2 scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-transparent">
                    {files.map((file, idx) => (
                      <div
                        key={idx}
                        className="group flex items-center justify-between p-3 bg-slate-800/50 hover:bg-slate-700/50 rounded-lg border border-slate-700 transition-colors"
                      >
                        <div className="flex items-center gap-3 overflow-hidden">
                          <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center flex-shrink-0">
                            <span className="text-lg">
                              {file.name.endsWith('.py') ? '🐍' : file.name.endsWith('.pdf') ? '📕' : '📄'}
                            </span>
                          </div>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-slate-200 truncate group-hover:text-white transition-colors">
                              {file.name}
                            </p>
                            <p className="text-xs text-slate-500">
                              {(file.size / 1024).toFixed(1)} KB
                            </p>
                          </div>
                        </div>
                        <button
                          type="button"
                          onClick={(e) => {
                            e.stopPropagation()
                            removeFile(idx)
                          }}
                          className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-all"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column: Context & Rubric */}
          <div className="space-y-6">
            {/* Problem Statement */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="text-2xl">📝</span> Problem Context
                </h2>
                <span className="px-3 py-1 text-xs font-medium text-slate-400 bg-slate-800 rounded-full border border-slate-700">
                  Optional
                </span>
              </div>
              <div className="relative">
                <textarea
                  value={problemStatement}
                  onChange={(e) => setProblemStatement(e.target.value)}
                  placeholder="Describe the assignment requirements, specific constraints, or grading criteria..."
                  className="w-full h-32 px-4 py-3 bg-slate-950/50 border border-slate-700 rounded-xl text-slate-300 placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all resize-none text-sm leading-relaxed scrollbar-thin scrollbar-thumb-slate-700"
                />
              </div>
            </div>

            {/* Rubric */}
            <div className="bg-slate-900/50 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                  <span className="text-2xl">📊</span> Grading Rubric
                </h2>
                <div className="flex bg-slate-800 rounded-lg p-1 border border-slate-700">
                  <button
                    type="button"
                    onClick={() => setRubricSource('text')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${rubricSource === 'text'
                        ? 'bg-indigo-500 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                      }`}
                  >
                    JSON
                  </button>
                  <button
                    type="button"
                    onClick={() => setRubricSource('file')}
                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${rubricSource === 'file'
                        ? 'bg-indigo-500 text-white shadow-sm'
                        : 'text-slate-400 hover:text-white'
                      }`}
                  >
                    File
                  </button>
                </div>
              </div>

              {rubricSource === 'text' ? (
                <div className="relative animate-fade-in">
                  <textarea
                    value={rubricText}
                    onChange={(e) => {
                      setRubricText(e.target.value)
                      setErrors((prev) => prev.filter((e) => !e.includes('rubric')))
                    }}
                    placeholder={`{\n  "criteria": [\n    { "name": "Logic", "points": 10 }\n  ]\n}`}
                    className="w-full h-40 px-4 py-3 bg-slate-950/50 border border-slate-700 rounded-xl text-slate-300 placeholder-slate-500 font-mono text-xs focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-all resize-none scrollbar-thin scrollbar-thumb-slate-700"
                  />
                </div>
              ) : (
                <div className="relative animate-fade-in">
                  <input
                    ref={rubricInputRef}
                    type="file"
                    accept=".json"
                    onChange={handleRubricFileSelect}
                    className="hidden"
                  />
                  <div className="flex gap-2">
                    <button
                      type="button"
                      onClick={() => rubricInputRef.current?.click()}
                      className="flex-1 px-4 py-3 bg-slate-950/50 border border-slate-700 border-dashed rounded-xl text-slate-400 hover:text-indigo-400 hover:border-indigo-500/50 hover:bg-slate-900/80 transition-all flex items-center justify-center gap-2 group"
                    >
                      <svg className="w-5 h-5 group-hover:scale-110 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                      </svg>
                      <span className="text-sm font-medium">
                        {rubricFile ? rubricFile.name : 'Upload JSON Rubric'}
                      </span>
                    </button>
                    {rubricFile && (
                      <button
                        type="button"
                        onClick={() => {
                          setRubricFile(null)
                          if (rubricInputRef.current) rubricInputRef.current.value = ''
                        }}
                        className="px-4 py-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 hover:bg-red-500/20 transition-all"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                  <p className="mt-2 text-xs text-slate-500 text-center">
                    Supported format: .json
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Bar */}
        <div className="sticky bottom-4 z-10">
          <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-4 shadow-2xl flex items-center justify-between gap-4 max-w-2xl mx-auto">
            <button
              type="button"
              disabled={loading}
              onClick={() => {
                setFiles([])
                setProblemStatement('')
                setRubricText('')
                setRubricFile(null)
                setErrors([])
                if (fileInputRef.current) fileInputRef.current.value = ''
                if (rubricInputRef.current) rubricInputRef.current.value = ''
              }}
              className="px-6 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white hover:bg-slate-800 transition-all disabled:opacity-50"
            >
              Reset All
            </button>
            <button
              type="submit"
              disabled={loading || files.length === 0}
              className="flex-1 px-8 py-2.5 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white text-sm font-bold rounded-xl shadow-lg shadow-indigo-500/25 transition-all transform hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </>
              ) : (
                <>
                  <span>Begin Evaluation</span>
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
