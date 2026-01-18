import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Assignment Evaluator',
  description: 'Teacher interface for evaluating student submissions',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        {children}
      </body>
    </html>
  )
}
