import Link from 'next/link'

export default function CTASection() {
  return (
    <section className="py-24">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <div className="relative rounded-3xl bg-slate_surface glass-edge p-12 md:p-16 overflow-hidden">
          {/* Background glow */}
          <div className="absolute inset-0 bg-hero-glow opacity-40" />
          <div className="absolute -bottom-20 -right-20 w-60 h-60 rounded-full bg-violet-deep/10 blur-[80px]" />

          <div className="relative z-10">
            <h2 className="text-3xl md:text-4xl font-bold text-frost mb-4">
              Ready to upgrade your department&apos;s throughput?
            </h2>
            <p className="text-frost-muted text-base max-w-lg mx-auto mb-8">
              Join 40+ institutions automating their technical feedback loop.
            </p>
            <Link
              href="/login"
              className="inline-flex items-center gap-2 px-8 py-4 rounded-full bg-violet-gradient text-white font-semibold text-base btn-glow transition-all duration-300 hover:scale-105 hover:shadow-violet-glow-lg"
            >
              Get Started Free
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </Link>
          </div>
        </div>
      </div>
    </section>
  )
}
