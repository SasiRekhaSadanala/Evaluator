const steps = [
  {
    num: '01',
    title: 'Ingest & Parse',
    description: 'Upload raw codebases, essays, or technical documents. Our ingestion agent sanitizes data and prepares it for multi-modal analysis.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    num: '02',
    title: 'Multi-Agent Critique',
    description: 'Three specialized LLM agents debate the quality of the work based on your rubric. This consensus-based approach eliminates individual model hallucination.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5" />
      </svg>
    ),
  },
  {
    num: '03',
    title: 'Quantified Insights',
    description: 'Receive a detailed JSON report and a visual dashboard featuring percentage-based scoring, qualitative feedback, and actionable improvement steps.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
      </svg>
    ),
  },
]

export default function WorkflowSection() {
  return (
    <section id="workflow" className="py-24 bg-slate-surface/30">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <span className="text-emerald-trust font-grotesk text-sm font-medium uppercase tracking-[0.15em]">
            Automated Workflow
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-frost mt-3">
            From submission to insight
          </h2>
          <p className="text-frost-muted text-base max-w-xl mx-auto mt-4">
            Three non-linear steps powered by asynchronous compute.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {steps.map((step, i) => (
            <div key={i} className="relative group">
              {/* Connecting line on desktop */}
              {i < steps.length - 1 && (
                <div className="hidden md:block absolute top-10 left-[60%] w-full h-px bg-gradient-to-r from-ghost/30 to-transparent" />
              )}

              <div className="relative rounded-2xl bg-obsidian glass-edge p-8 transition-all duration-300 hover:shadow-ambient hover:-translate-y-1">
                {/* Step number */}
                <div className="flex items-center gap-4 mb-6">
                  <div className="w-10 h-10 rounded-full bg-violet-gradient flex items-center justify-center shadow-violet-glow">
                    <span className="text-white text-xs font-bold font-grotesk">{step.num}</span>
                  </div>
                  <div className="w-8 h-8 rounded-lg bg-slate-surface-high flex items-center justify-center text-violet-primary">
                    {step.icon}
                  </div>
                </div>

                <h3 className="text-xl font-bold text-frost mb-3">{step.title}</h3>
                <p className="text-frost-muted text-sm leading-relaxed">{step.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
