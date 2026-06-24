'use client'

import React from 'react'

interface StatsCardProps {
  label: string
  value: string | number
  color?: string
}

const StatsCard: React.FC<StatsCardProps> = ({ label, value, color }) => {
  return (
    <div className="bg-surface-container-low rounded-xl border border-outline-variant/10 p-6 hover:border-outline-variant/20 transition-all">
      <span className="text-xs font-semibold uppercase tracking-wider text-frost-muted block mb-3">
        {label}
      </span>
      <span className={`text-4xl font-bold font-mono tracking-tight ${color === 'coral' ? 'text-coral' : 'text-violet-primary'}`}>
        {value}
      </span>
    </div>
  )
}

interface ResultsDashboardProps {
  total: number | string
  average: number | string
  highest: number | string
  passRate?: number | string
  integrityAlerts?: number | string
}

export const ResultsDashboard: React.FC<ResultsDashboardProps> = ({
  total,
  average,
  highest,
  passRate = '0%',
  integrityAlerts = 0
}) => {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-10 animate-slide-up">
      <StatsCard label="Total Submissions" value={total} />
      <StatsCard label="Average / Highest" value={`${average} / ${highest}`} />
      <StatsCard label="Pass Rate" value={passRate} />
      <StatsCard label="Integrity Alerts" value={integrityAlerts} color="coral" />
    </div>
  )
}
