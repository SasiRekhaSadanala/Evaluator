'use client'

import React from 'react'

interface FileItemProps {
  file: File
  onRemove: () => void
}

export const FileItem: React.FC<FileItemProps> = ({ file, onRemove }) => {
  const formatSize = (bytes: number) => {
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  /**
   * Strip Moodle metadata from filename for display.
   * "Nitin M_34610.html"          → "Nitin M"
   * "Deepak Paul Tirkey_35222.html" → "Deepak Paul Tirkey"
   * "student_alice.py"             → "student_alice" (unchanged)
   */
  const cleanDisplayName = (name: string) => {
    const dotIdx = name.lastIndexOf('.')
    const stem = dotIdx > 0 ? name.substring(0, dotIdx) : name
    // Match: Name_4-6digits at end of stem (Moodle ID pattern)
    const cleaned = stem.replace(/_\d{4,6}$/, '')
    return cleaned
  }

  const getFileTypeLabel = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'py': return 'Python'
      case 'cpp':
      case 'cc':
      case 'cxx': return 'C++'
      case 'h':
      case 'hpp': return 'Header'
      case 'pdf': return 'PDF'
      case 'txt': return 'Text'
      default: return 'File'
    }
  }

  const getFileColor = (fileName: string) => {
    const ext = fileName.split('.').pop()?.toLowerCase()
    switch (ext) {
      case 'py': return 'text-emerald-trust bg-emerald-trust/10 border-emerald-trust/20'
      case 'cpp':
      case 'cc':
      case 'cxx':
      case 'h':
      case 'hpp': return 'text-violet-primary bg-violet-primary/10 border-violet-primary/20'
      case 'pdf': return 'text-coral bg-coral/10 border-coral/20'
      default: return 'text-frost-muted bg-frost-muted/10 border-frost-muted/20'
    }
  }

  return (
    <div className="flex items-center justify-between p-3.5 bg-surface-container-low rounded-lg border border-outline-variant/10 group hover:border-outline-variant/20 transition-all">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-surface-container-highest flex items-center justify-center text-violet-primary shrink-0">
          <span className="material-symbols-outlined text-[18px]">description</span>
        </div>
        <div className="min-w-0">
          <p className="text-sm font-medium text-frost truncate">
            {cleanDisplayName(file.name)}
          </p>
          <div className="flex items-center gap-2 mt-0.5">
            <span className={`text-[10px] font-medium px-1.5 py-0.5 rounded border ${getFileColor(file.name)}`}>
              {getFileTypeLabel(file.name)}
            </span>
            <span className="text-[10px] text-frost-muted">
              {formatSize(file.size)}
            </span>
          </div>
        </div>
      </div>
      <button
        type="button"
        onClick={onRemove}
        className="p-1.5 text-frost-muted hover:text-coral hover:bg-coral/10 rounded-md transition-all opacity-0 group-hover:opacity-100"
        title="Remove file"
      >
        <span className="material-symbols-outlined text-[18px]">close</span>
      </button>
    </div>
  )
}
