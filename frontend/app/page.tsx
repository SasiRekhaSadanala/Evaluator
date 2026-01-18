import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900">
      {/* Navigation */}
      <nav className="border-b border-indigo-500/20 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 py-5 flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-black bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent">
              Assignment Evaluator
            </h1>
            <p className="text-indigo-300/70 text-sm mt-1">Intelligent Submission Evaluation System</p>
          </div>
          <div className="text-indigo-400/60 font-mono text-xs">v1.0</div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-20">
          <h2 className="text-5xl md:text-6xl font-black text-white mb-6 leading-tight">
            Evaluate Student <br />
            <span className="bg-gradient-to-r from-indigo-400 via-cyan-400 to-indigo-400 bg-clip-text text-transparent">
              Submissions Instantly
            </span>
          </h2>
          <p className="text-indigo-200/80 text-lg md:text-xl max-w-2xl mx-auto leading-relaxed">
            Upload code and content files, get instant AI-powered evaluation with detailed feedback and scores. Perfect for educators who want to save time grading.
          </p>
        </div>

        {/* Main Action Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-16">
          {/* Upload Card */}
          <Link href="/upload" className="group">
            <div className="relative h-full bg-gradient-to-br from-indigo-500/10 to-indigo-500/5 backdrop-blur border border-indigo-500/30 rounded-2xl p-8 cursor-pointer hover:border-indigo-400/60 transition-all duration-300 hover:shadow-2xl hover:shadow-indigo-500/20 hover:-translate-y-1">
              <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-indigo-500/10 to-transparent rounded-full -mr-20 -mt-20 group-hover:scale-150 transition-transform duration-300" />
              
              <div className="relative z-10">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-indigo-500/30 to-indigo-600/20 rounded-xl mb-6 group-hover:scale-110 transition-transform duration-300">
                  <span className="text-3xl">📤</span>
                </div>
                
                <h3 className="text-2xl font-bold text-white mb-3">
                  Upload & Evaluate
                </h3>
                
                <p className="text-indigo-200/70 mb-6 leading-relaxed">
                  Submit student Python code and text files. Specify assignment type and add context for smarter evaluation.
                </p>
                
                <div className="flex items-center text-indigo-300 font-semibold group-hover:text-cyan-400 transition-colors">
                  Start Evaluating
                  <span className="ml-2 text-lg group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </div>
          </Link>

          {/* Results Card */}
          <Link href="/results" className="group">
            <div className="relative h-full bg-gradient-to-br from-cyan-500/10 to-cyan-500/5 backdrop-blur border border-cyan-500/30 rounded-2xl p-8 cursor-pointer hover:border-cyan-400/60 transition-all duration-300 hover:shadow-2xl hover:shadow-cyan-500/20 hover:-translate-y-1">
              <div className="absolute top-0 right-0 w-40 h-40 bg-gradient-to-br from-cyan-500/10 to-transparent rounded-full -mr-20 -mt-20 group-hover:scale-150 transition-transform duration-300" />
              
              <div className="relative z-10">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-cyan-500/30 to-cyan-600/20 rounded-xl mb-6 group-hover:scale-110 transition-transform duration-300">
                  <span className="text-3xl">📊</span>
                </div>
                
                <h3 className="text-2xl font-bold text-white mb-3">
                  View Results
                </h3>
                
                <p className="text-indigo-200/70 mb-6 leading-relaxed">
                  See comprehensive scores, detailed feedback, and export data. Perfect for tracking student progress.
                </p>
                
                <div className="flex items-center text-cyan-300 font-semibold group-hover:text-cyan-300 transition-colors">
                  View Dashboard
                  <span className="ml-2 text-lg group-hover:translate-x-1 transition-transform">→</span>
                </div>
              </div>
            </div>
          </Link>
        </div>

        {/* Features Grid */}
        <div className="mt-24">
          <h3 className="text-3xl font-bold text-white mb-12 text-center">
            Why Choose Our Evaluator?
          </h3>
          
          <div className="grid md:grid-cols-3 gap-6">
            {[
              {
                icon: '⚡',
                title: 'Instant Evaluation',
                desc: 'Get results in seconds, not hours'
              },
              {
                icon: '🎯',
                title: 'Detailed Feedback',
                desc: 'Actionable insights for every submission'
              },
              {
                icon: '📈',
                title: 'Easy Analytics',
                desc: 'Track progress with CSV exports'
              },
              {
                icon: '🔒',
                title: 'Secure & Private',
                desc: 'All data stays on your machine'
              },
              {
                icon: '🛠️',
                title: 'Flexible',
                desc: 'Works with any assignment type'
              },
              {
                icon: '✨',
                title: 'AI-Powered',
                desc: 'Smart evaluation based on rubrics'
              }
            ].map((feature, idx) => (
              <div key={idx} className="bg-gradient-to-br from-indigo-500/10 to-indigo-500/5 backdrop-blur border border-indigo-500/20 rounded-xl p-6 hover:border-indigo-400/40 transition-all hover:shadow-lg hover:shadow-indigo-500/10">
                <div className="text-4xl mb-4">{feature.icon}</div>
                <h4 className="text-white font-bold mb-2">{feature.title}</h4>
                <p className="text-indigo-200/60 text-sm">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>

        {/* How It Works */}
        <div className="mt-24">
          <h3 className="text-3xl font-bold text-white mb-12 text-center">
            How It Works
          </h3>
          
          <div className="bg-gradient-to-r from-indigo-500/10 via-transparent to-cyan-500/10 backdrop-blur border border-indigo-500/20 rounded-2xl p-12">
            <div className="grid md:grid-cols-4 gap-8">
              {[
                { num: '1', title: 'Upload', desc: 'Select student files' },
                { num: '2', title: 'Configure', desc: 'Set assignment type' },
                { num: '3', title: 'Evaluate', desc: 'AI powers analysis' },
                { num: '4', title: 'Review', desc: 'View results & export' }
              ].map((step, idx) => (
                <div key={idx} className="text-center">
                  <div className="inline-flex items-center justify-center w-12 h-12 bg-gradient-to-br from-indigo-500 to-cyan-500 text-white font-bold rounded-full mb-4 text-lg">
                    {step.num}
                  </div>
                  <h4 className="text-white font-bold text-lg mb-2">{step.title}</h4>
                  <p className="text-indigo-200/60 text-sm">{step.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-indigo-500/20 backdrop-blur mt-24 py-8">
        <div className="max-w-7xl mx-auto px-6 text-center text-indigo-300/60 text-sm">
          <p>Assignment Evaluator • Intelligent Submission Evaluation System</p>
        </div>
      </footer>
    </main>
  )
}
