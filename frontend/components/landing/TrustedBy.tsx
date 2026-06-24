export default function TrustedBy() {
  const institutions = [
    'Stanford', 'MIT', 'Harvard', 'Oxford', 'Cambridge', 'ETH Zürich'
  ]

  return (
    <section className="py-12 border-y border-ghost/10">
      <div className="max-w-5xl mx-auto px-6">
        <p className="text-center text-frost-steel text-xs font-grotesk uppercase tracking-[0.2em] mb-8">
          Empowering Uncompromising Excellence At
        </p>
        <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16">
          {institutions.map((name, i) => (
            <span
              key={i}
              className="text-frost-muted/40 text-lg md:text-xl font-bold tracking-wide hover:text-frost-muted/70 transition-colors duration-300 cursor-default"
            >
              {name}
            </span>
          ))}
        </div>
      </div>
    </section>
  )
}
