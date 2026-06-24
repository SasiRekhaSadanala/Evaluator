export default function Footer() {
  return (
    <footer className="border-t border-ghost/10 py-10">
      <div className="max-w-6xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          <div className="flex items-center gap-3">
            <div className="w-7 h-7 rounded-lg bg-violet-gradient flex items-center justify-center">
              <span className="text-white font-bold text-xs">E</span>
            </div>
            <span className="text-frost-muted text-sm">
              © 2026 Evaluator 2.0. Released under MIT License.
            </span>
          </div>

          <div className="flex items-center gap-6">
            {['Dashboard', 'API', 'Support', 'Privacy'].map((link) => (
              <a
                key={link}
                href="#"
                className="text-frost-steel text-sm hover:text-violet-primary transition-colors duration-300"
              >
                {link}
              </a>
            ))}
          </div>
        </div>
      </div>
    </footer>
  )
}
