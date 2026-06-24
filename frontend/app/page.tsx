import Navbar from '@/components/landing/Navbar'
import HeroSection from '@/components/landing/HeroSection'
import TrustedBy from '@/components/landing/TrustedBy'
import FeaturesGrid from '@/components/landing/FeaturesGrid'
import WorkflowSection from '@/components/landing/WorkflowSection'
import CTASection from '@/components/landing/CTASection'
import Footer from '@/components/landing/Footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-obsidian">
      <Navbar />
      <HeroSection />
      <TrustedBy />
      <FeaturesGrid />
      <WorkflowSection />
      <CTASection />
      <Footer />
    </main>
  )
}
