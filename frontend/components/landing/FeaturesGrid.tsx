const features = [
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
      </svg>
    ),
    title: 'Custom Rubrics',
    description: 'Define complex, weighted grading criteria. Our agents adapt to specific tone, formatting, and technical requirements per assignment.',
    accent: 'violet',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
    title: 'Polyglot Analysis',
    description: 'Deep execution trace for Python, C++, and Java. We detect logic flaws and algorithmic efficiency, not just syntax errors.',
    accent: 'emerald',
  },
  {
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
      </svg>
    ),
    title: 'Plagiarism Detection',
    description: 'Beyond string matching. Our AI identifies semantic structural theft and latent paraphrasing patterns from major LLMs.',
    accent: 'coral',
  },
]

export default function FeaturesGrid() {
  const accentMap: Record<string, { iconBg: string; dot: string }> = {
    violet: { iconBg: 'bg-violet-deep/20 text-violet-primary', dot: 'bg-violet-primary' },
    emerald: { iconBg: 'bg-emerald-trust/15 text-emerald-trust', dot: 'bg-emerald-trust' },
    coral: { iconBg: 'bg-coral-container/15 text-coral', dot: 'bg-coral-container' },
  }

  return (
    <section id="features" className="py-24">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center mb-16">
          <span className="text-violet-primary font-grotesk text-sm font-medium uppercase tracking-[0.15em]">
            Core Infrastructure
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-frost mt-3">
            Precision tools for high-stakes academia
          </h2>
          <p className="text-frost-muted text-base max-w-xl mx-auto mt-4">
            Where consistency is the primary metric.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {features.map((feature, i) => {
            const colors = accentMap[feature.accent]
            return (
              <div
                key={i}
                className="group relative rounded-2xl bg-slate_surface glass-edge p-8 transition-all duration-300 hover:-translate-y-1 hover:shadow-ambient"
              >
                {/* AI dot indicator */}
                <div className={`absolute top-5 right-5 w-2 h-2 rounded-full ${colors.dot} opacity-60`} />

                <div className={`inline-flex items-center justify-center w-12 h-12 rounded-xl ${colors.iconBg} mb-6 transition-transform duration-300 group-hover:scale-110`}>
                  {feature.icon}
                </div>

                <h3 className="text-xl font-bold text-frost mb-3">{feature.title}</h3>
                <p className="text-frost-muted text-sm leading-relaxed">{feature.description}</p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
