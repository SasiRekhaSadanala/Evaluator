'use client'

import React, { useState, useRef } from 'react'

interface ContextInputsProps {
  assignmentType: 'code' | 'content' | 'mixed' | 'transcript'
  problemStatement: string
  setProblemStatement: (val: string) => void
  topic: string
  setTopic: (val: string) => void
  testCases: string
  setTestCases: (val: string) => void
  transcriptText: string
  setTranscriptText: (val: string) => void
  rubricSource: 'text' | 'file'
  setRubricSource: (val: 'text' | 'file') => void
  rubricText: string
  setRubricText: (val: string) => void
  rubricFile: File | null
  setRubricFile: (file: File | null) => void
  rubricInputRef: React.RefObject<HTMLInputElement>
  handleRubricFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
}

export const ContextInputs: React.FC<ContextInputsProps> = ({
  assignmentType,
  problemStatement,
  setProblemStatement,
  topic,
  setTopic,
  testCases,
  setTestCases,
  transcriptText,
  setTranscriptText,
  rubricSource,
  setRubricSource,
  rubricText,
  setRubricText,
  rubricFile,
  setRubricFile,
  rubricInputRef,
  handleRubricFileSelect
}) => {
  const [showTestCases, setShowTestCases] = useState(false)
  const vttInputRef = useRef<HTMLInputElement>(null)

  const inputClasses = "w-full bg-surface-container-lowest border border-outline-variant/20 text-frost px-4 py-3 rounded-lg focus:ring-2 focus:ring-violet-primary/40 focus:border-violet-primary/60 outline-none transition-all text-sm placeholder:text-frost-muted/40"

  const isTranscript = assignmentType === 'transcript'

  const handleVttFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    const text = await file.text()
    setTranscriptText(text)
  }

  return (
    <div className="space-y-6">
      {/* Topic & Test Cases Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-frost-muted">
            Topic / Subject
          </label>
          <input
            type="text"
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="e.g., Data Structures, Linear Algebra"
            className={inputClasses}
          />
        </div>

        {!isTranscript && (
          <div className="flex flex-col justify-end">
            <button
              type="button"
              onClick={() => setShowTestCases(!showTestCases)}
              className={`h-[46px] flex items-center justify-center gap-2 rounded-lg border transition-all text-sm font-medium ${
                showTestCases
                  ? 'bg-violet-primary/10 border-violet-primary/30 text-violet-primary'
                  : 'bg-surface-container-high/40 border-outline-variant/20 text-frost-muted hover:text-frost hover:bg-surface-container-high/60'
              }`}
            >
              <span className="material-symbols-outlined text-[18px]">science</span>
              {showTestCases ? 'Hide Test Cases' : 'Add Test Cases'}
            </button>
          </div>
        )}
      </div>

      {/* Test Cases (Collapsible) — hidden for transcript type */}
      {!isTranscript && showTestCases && (
        <div className="space-y-2 animate-fade-in">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold uppercase tracking-wider text-frost-muted">
              Test Cases (JSON)
            </label>
            <span className="text-[10px] text-emerald-trust/60 font-medium">
              Optional — for pass-rate calculation
            </span>
          </div>
          <textarea
            value={testCases}
            onChange={(e) => setTestCases(e.target.value)}
            placeholder={`[{"stdin": "5\\n3", "expected_output": "8"}]`}
            className={`${inputClasses} min-h-[100px] resize-none font-mono text-xs`}
          />
        </div>
      )}

      {/* Transcript Input — shown ONLY for transcript type */}
      {isTranscript && (
        <div className="space-y-3 animate-fade-in">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold uppercase tracking-wider text-frost-muted">
              Lecture Transcript (VTT)
            </label>
            <div className="flex items-center gap-2">
              <input
                ref={vttInputRef}
                type="file"
                accept=".vtt,.txt"
                onChange={handleVttFileUpload}
                className="hidden"
              />
              <button
                type="button"
                onClick={() => vttInputRef.current?.click()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md bg-violet-primary/10 border border-violet-primary/20 text-violet-primary hover:bg-violet-primary/20 transition-all"
              >
                <span className="material-symbols-outlined text-[14px]">upload_file</span>
                Upload .vtt
              </button>
            </div>
          </div>
          <textarea
            value={transcriptText}
            onChange={(e) => setTranscriptText(e.target.value)}
            placeholder={"Paste VTT transcript here or upload a .vtt file...\n\nWEBVTT\n\n1\n00:00:01.000 --> 00:00:05.000\nSpeaker: Today we will discuss supervised learning..."}
            className={`${inputClasses} min-h-[200px] resize-none font-mono text-xs leading-relaxed`}
          />
          {transcriptText && (
            <div className="flex items-center gap-2 text-xs text-emerald-trust/80">
              <span className="material-symbols-outlined text-[14px]">check_circle</span>
              Transcript loaded ({transcriptText.split('\n').length} lines, ~{transcriptText.split(/\s+/).length} words)
            </div>
          )}
        </div>
      )}

      {/* Problem Statement — hidden for transcript type */}
      {!isTranscript && (
        <div className="space-y-2">
          <label className="block text-xs font-semibold uppercase tracking-wider text-frost-muted">
            Problem Statement
          </label>
          <textarea
            value={problemStatement}
            onChange={(e) => setProblemStatement(e.target.value)}
            placeholder="Describe the assignment requirements..."
            className={`${inputClasses} min-h-[120px] resize-none`}
          />
        </div>
      )}

      {/* Rubric Section — hidden for transcript type */}
      {!isTranscript && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="block text-xs font-semibold uppercase tracking-wider text-frost-muted">
              Rubric Definition
            </label>
            <div className="flex p-0.5 bg-surface-container-lowest rounded-md border border-outline-variant/10">
              <button
                type="button"
                onClick={() => setRubricSource('text')}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                  rubricSource === 'text'
                    ? 'bg-violet-primary text-obsidian'
                    : 'text-frost-muted hover:text-frost'
                }`}
              >
                Text Input
              </button>
              <button
                type="button"
                onClick={() => setRubricSource('file')}
                className={`px-3 py-1.5 text-xs font-medium rounded transition-all ${
                  rubricSource === 'file'
                    ? 'bg-violet-primary text-obsidian'
                    : 'text-frost-muted hover:text-frost'
                }`}
              >
                JSON File
              </button>
            </div>
          </div>

          {rubricSource === 'text' ? (
            <textarea
              value={rubricText}
              onChange={(e) => setRubricText(e.target.value)}
              placeholder="Enter rubric criteria or paste JSON schema..."
              className={`${inputClasses} h-40 resize-none animate-fade-in`}
            />
          ) : (
            <div className="animate-fade-in">
              <input
                ref={rubricInputRef}
                type="file"
                accept=".json"
                onChange={handleRubricFileSelect}
                className="hidden"
              />
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => rubricInputRef.current?.click()}
                  className="flex-1 px-5 py-4 bg-surface-container-lowest border border-outline-variant/20 rounded-lg text-frost-muted hover:text-violet-primary hover:border-violet-primary/30 transition-all flex items-center justify-between"
                >
                  <span className="text-sm font-medium">
                    {rubricFile ? rubricFile.name : 'Choose .json file...'}
                  </span>
                  <span className="material-symbols-outlined text-[20px] text-violet-primary">upload_file</span>
                </button>
                {rubricFile && (
                  <button
                    type="button"
                    onClick={() => setRubricFile(null)}
                    className="px-4 bg-coral/10 border border-coral/20 rounded-lg text-coral hover:bg-coral/20 transition-all"
                  >
                    <span className="material-symbols-outlined text-[20px]">close</span>
                  </button>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
