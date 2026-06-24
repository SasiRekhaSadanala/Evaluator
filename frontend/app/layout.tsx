import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Evaluator 2.0 | Intelligent AI-Powered Academic Assessment',
  description: 'Automate rigorous academic grading with our proprietary multi-agent approach. Conditional Scoring, Strict Relevance Checks, and LLM-powered feedback.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/icon?family=Material+Symbols+Outlined" rel="stylesheet" />
      </head>
      <body className="font-inter antialiased">
        {children}
      </body>
    </html>
  )
}
