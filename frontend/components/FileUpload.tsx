'use client'

import { useState, useRef } from 'react'
import { FileItem } from './upload/FileItem'
import { UploadCard } from './upload/UploadCard'
import { AssignmentTypeToggle } from './upload/AssignmentTypeToggle'
import { ContextInputs } from './upload/ContextInputs'

interface FileUploadProps {
  onSubmit?: (data: FileUploadData) => void
  onFileChange?: (files: File[]) => void
  loading?: boolean
}

export interface FileUploadData {
  files: File[]
  problemStatement: string
  assignmentType: 'code' | 'content' | 'mixed' | 'transcript'
  rubric: string | null
  rubricSource: 'text' | 'file'
  topic: string
  testCases: string
  transcriptText: string
}

export default function FileUpload({ onSubmit, onFileChange, loading }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const rubricInputRef = useRef<HTMLInputElement>(null)

  const [problemStatement, setProblemStatement] = useState('')
  const [assignmentType, setAssignmentType] = useState<'code' | 'content' | 'mixed' | 'transcript'>('code')
  const [topic, setTopic] = useState('')
  const [testCases, setTestCases] = useState('')
  const [transcriptText, setTranscriptText] = useState('')
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
    const allowedExtensions = ['.py', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.txt', '.pdf', '.html', '.htm', '.zip']

    Array.from(selectedFiles).forEach((file) => {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase()
      if (!allowedExtensions.includes(ext)) {
        setErrors((prev) => [...prev, `Unsupported file type: ${file.name}`])
        return
      }

      // For folder uploads: derive student name from webkitRelativePath
      // e.g. "MLP Live Session/A Ananya_35470_assignsubmission_onlinetext/onlinetext.html"
      //  → rename to "A Ananya_35470.html"
      let finalFile = file
      const relativePath = (file as any).webkitRelativePath as string | undefined

      if (relativePath && relativePath.includes('/')) {
        const parts = relativePath.split('/')
        // Find the Moodle-style folder: "StudentName_ID_assignsubmission_onlinetext"
        const studentFolder = parts.find(p => p.includes('_assignsubmission'))
        if (studentFolder) {
          const studentName = studentFolder.split('_assignsubmission')[0]
          const newName = `${studentName}${ext}`
          finalFile = new File([file], newName, { type: file.type })
        } else if (parts.length >= 2) {
          // Non-Moodle folder: use parent folder name
          const parentFolder = parts[parts.length - 2]
          const newName = `${parentFolder}_${file.name}`
          finalFile = new File([file], newName, { type: file.type })
        }
      }

      // Skip duplicates by name
      if (!files.some((f) => f.name === finalFile.name) &&
          !newFiles.some((f) => f.name === finalFile.name)) {
        newFiles.push(finalFile)
      }
    })

    if (newFiles.length > 0) {
      const updatedFiles = [...files, ...newFiles]
      setFiles(updatedFiles)
      onFileChange?.(updatedFiles)
      setErrors((prev) => prev.filter((e) => !e.startsWith('Unsupported')))
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
        setErrors((prev) => [...prev, 'Rubric must be a .json file'])
      }
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const formErrors: string[] = []
    if (files.length === 0) formErrors.push('Please upload at least one student submission')

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
        JSON.parse(finalRubric)
      } catch {
        setErrors(['Invalid JSON in rubric file'])
        return
      }
    }

    if (onSubmit) {
      onSubmit({
        files,
        problemStatement,
        assignmentType,
        rubric: finalRubric,
        rubricSource,
        topic,
        testCases,
        transcriptText,
      })
    }
  }

  const handleReset = () => {
    setFiles([])
    setProblemStatement('')
    setTopic('')
    setTestCases('')
    setTranscriptText('')
    setRubricText('')
    setRubricFile(null)
    setErrors([])
    if (fileInputRef.current) fileInputRef.current.value = ''
    if (rubricInputRef.current) rubricInputRef.current.value = ''
  }

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">

        {/* Error Messages */}
        {errors.length > 0 && (
          <div className="bg-coral/5 border border-coral/20 p-4 rounded-xl animate-fade-in">
            <div className="flex items-start gap-3">
              <span className="material-symbols-outlined text-coral text-[20px] mt-0.5">error</span>
              <div>
                <h3 className="text-sm font-semibold text-coral mb-1">Please fix the following</h3>
                <ul className="text-xs text-coral/80 list-disc list-inside space-y-0.5">
                  {errors.map((error, idx) => (
                    <li key={idx}>{error}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}

        {/* Main Form Card */}
        <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-8 space-y-6">
          <AssignmentTypeToggle
            assignmentType={assignmentType}
            setAssignmentType={setAssignmentType}
          />

          <ContextInputs
            assignmentType={assignmentType}
            problemStatement={problemStatement}
            setProblemStatement={setProblemStatement}
            topic={topic}
            setTopic={setTopic}
            testCases={testCases}
            setTestCases={setTestCases}
            transcriptText={transcriptText}
            setTranscriptText={setTranscriptText}
            rubricSource={rubricSource}
            setRubricSource={setRubricSource}
            rubricText={rubricText}
            setRubricText={setRubricText}
            rubricFile={rubricFile}
            setRubricFile={setRubricFile}
            rubricInputRef={rubricInputRef}
            handleRubricFileSelect={handleRubricFileSelect}
          />

          <div className="pt-4">
            <UploadCard
              onFileSelect={handleFileSelect}
              dragActive={dragActive}
              onDrag={handleDrag}
              onDrop={handleDrop}
              inputRef={fileInputRef}
              filesCount={files.length}
            />

            {files.length > 0 && (
              <div className="space-y-2 animate-fade-in mt-4">
                <div className="grid gap-2 max-h-[240px] overflow-y-auto pr-1 scrollbar-thin">
                  {files.map((file, idx) => (
                    <FileItem
                      key={idx}
                      file={file}
                      onRemove={() => removeFile(idx)}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex justify-between items-center gap-4 pt-6 border-t border-outline-variant/10">
            <button
              type="button"
              disabled={loading}
              onClick={handleReset}
              className="px-5 py-2.5 rounded-lg text-sm font-medium text-frost-muted hover:text-frost hover:bg-surface-container-high/50 transition-all disabled:opacity-30 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">restart_alt</span>
              Reset
            </button>

            <button
              type="submit"
              disabled={loading || files.length === 0}
              className="px-8 py-2.5 rounded-lg font-semibold text-sm bg-gradient-to-r from-violet-primary to-violet-container text-obsidian shadow-violet hover:shadow-lg active:scale-[0.98] transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
            >
              {loading ? (
                <>
                  <span className="material-symbols-outlined animate-spin text-[18px]">progress_activity</span>
                  Evaluating...
                </>
              ) : (
                <>
                  <span className="material-symbols-outlined text-[18px]">play_arrow</span>
                  Evaluate Submissions
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
