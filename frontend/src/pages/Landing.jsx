import { Link } from 'react-router-dom'
import { Briefcase, Sparkles, Target, Users, ArrowRight, CheckCircle2, TrendingUp, GraduationCap } from 'lucide-react'

export default function Landing() {
  return (
    <div className="flex-1">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-b from-[#e6f7f7] to-white pt-20 pb-24 px-6">
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 bg-white border border-[#1AA29F]/20 rounded-full px-4 py-1.5 mb-6 shadow-sm">
            <Sparkles size={14} className="text-[#1AA29F]" />
            <span className="text-xs font-semibold text-[#1AA29F]">AI-powered internship matching</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold text-gray-800 leading-tight mb-5">
            Find the internship that<br className="hidden sm:block" /> actually fits <span className="text-[#1AA29F]">you</span>
          </h1>

          <p className="text-gray-500 text-base sm:text-lg max-w-xl mx-auto mb-8">
            Smart Internship matches students to opportunities using AI —
            no more scrolling through hundreds of listings that don't fit your skills.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/register"
              className="flex items-center gap-2 bg-[#1AA29F] hover:bg-[#158a87] text-white px-6 py-3 rounded-xl font-semibold text-sm shadow-lg shadow-[#1AA29F]/20 transition-all hover:shadow-xl hover:-translate-y-0.5"
            >
              Get started free <ArrowRight size={16} />
            </Link>
            <Link
              to="/internships"
              className="flex items-center gap-2 bg-white border border-gray-200 text-gray-700 px-6 py-3 rounded-xl font-semibold text-sm hover:bg-gray-50 transition-colors"
            >
              Browse internships
            </Link>
          </div>
        </div>

        {/* Decorative background blobs */}
        <div className="absolute top-10 -left-20 w-72 h-72 bg-[#1AA29F]/10 rounded-full blur-3xl" />
        <div className="absolute bottom-0 -right-20 w-96 h-96 bg-amber-100/40 rounded-full blur-3xl" />
      </section>

      {/* Stats strip */}
      <section className="border-y border-gray-100 bg-white py-8 px-6">
        <div className="max-w-4xl mx-auto grid grid-cols-3 gap-4 text-center">
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-gray-800">AI-Matched</p>
            <p className="text-xs sm:text-sm text-gray-400 mt-1">Hybrid semantic scoring</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-gray-800">Real-time</p>
            <p className="text-xs sm:text-sm text-gray-400 mt-1">New listings, instantly ranked</p>
          </div>
          <div>
            <p className="text-2xl sm:text-3xl font-bold text-gray-800">Skill Gaps</p>
            <p className="text-xs sm:text-sm text-gray-400 mt-1">See what to learn next</p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20 px-6 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">Built for both sides of the table</h2>
            <p className="text-gray-500 text-sm sm:text-base">Whether you're hiring or applying, matching does the heavy lifting.</p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            <FeatureCard
              icon={<Target size={20} className="text-[#1AA29F]" />}
              title="Smart matching"
              description="Your profile is compared against every listing using AI — not just keyword search."
            />
            <FeatureCard
              icon={<TrendingUp size={20} className="text-[#1AA29F]" />}
              title="See your skill gaps"
              description="Know exactly which skills separate you from a perfect match, with resources to close the gap."
            />
            <FeatureCard
              icon={<Users size={20} className="text-[#1AA29F]" />}
              title="Ranked applicants"
              description="Employers see candidates ranked by genuine fit, not just who applied first."
            />
            <FeatureCard
              icon={<CheckCircle2 size={20} className="text-[#1AA29F]" />}
              title="CV auto-parsing"
              description="Upload your CV once — your profile, skills, and certifications fill in automatically."
            />
            <FeatureCard
              icon={<GraduationCap size={20} className="text-[#1AA29F]" />}
              title="Learning resources"
              description="Missing a skill? Get curated courses, videos, and guides matched to exactly what you need."
            />
            <FeatureCard
              icon={<Briefcase size={20} className="text-[#1AA29F]" />}
              title="Direct feedback"
              description="Employers can share interview times and start dates right through the platform."
            />
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-gray-800 mb-3">Ready to find your fit?</h2>
          <p className="text-gray-500 text-sm sm:text-base mb-8">
            Join as a student or post your first internship in under two minutes.
          </p>
          <Link
            to="/register"
            className="inline-flex items-center gap-2 bg-[#1AA29F] hover:bg-[#158a87] text-white px-7 py-3 rounded-xl font-semibold text-sm shadow-lg shadow-[#1AA29F]/20 transition-all hover:shadow-xl hover:-translate-y-0.5"
          >
            Create your account <ArrowRight size={16} />
          </Link>
        </div>
      </section>
    </div>
  )
}

function FeatureCard({ icon, title, description }) {
  return (
    <div className="bg-white rounded-2xl border border-gray-100 p-5 hover:shadow-md hover:-translate-y-0.5 transition-all">
      <div className="bg-[#e6f7f7] w-10 h-10 rounded-xl flex items-center justify-center mb-3">
        {icon}
      </div>
      <h3 className="font-bold text-gray-800 text-sm mb-1.5">{title}</h3>
      <p className="text-gray-500 text-xs leading-relaxed">{description}</p>
    </div>
  )
}