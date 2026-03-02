import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    TrendingUp, Award, Flame, Zap, ChevronRight, PlayCircle, BookOpen, AlertCircle
} from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import Card from '../components/Card'
import { ProgressRing } from '../components/ProgressBar'
import ThemeToggle from '../components/ThemeToggle'
import PageTransition from '../components/PageTransition'
import { useCountUp, useInView } from '../hooks'
import { fetchDashboardSummary } from '../lib/api'

// Simple default icon map for subjects
const getIconForSubject = (name) => {
    return BookOpen; // fallback
}

const getSubjectColor = (name) => {
    const colors = ['#6C63FF', '#22C55E', '#F59E0B', '#06B6D4', '#EC4899'];
    // just pick a color based on string length for consistency map
    return colors[name.length % colors.length];
}

const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.08 } },
}
const item = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0 },
}

function StatCard({ label, value, icon: Icon, color, suffix = '' }) {
    const { ref, isInView } = useInView()
    const { count } = useCountUp(value, 1500, isInView)
    return (
        <motion.div variants={item} ref={ref}>
            <Card className="flex items-center gap-4">
                <div
                    className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                    style={{ background: `${color}15` }}
                >
                    <Icon size={22} style={{ color }} />
                </div>
                <div>
                    <p className="text-sm text-surface-500 dark:text-surface-400">{label}</p>
                    <p className="text-2xl font-heading font-bold text-surface-900 dark:text-white">
                        {count}{suffix}
                    </p>
                </div>
            </Card>
        </motion.div>
    )
}

export default function Dashboard() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const [loading, setLoading] = useState(true)
    const [dashboardData, setDashboardData] = useState(null)

    const firstName = user?.fullName?.split(' ')[0]
        || user?.email?.split('@')[0]
        || 'Learner'

    useEffect(() => {
        const loadDashboard = async () => {
            if (!user?.sessionToken) return;
            setLoading(true);
            const res = await fetchDashboardSummary(user.sessionToken);
            if (res.success) {
                setDashboardData(res.data);
            }
            setLoading(false);
        };
        loadDashboard();
    }, [user?.sessionToken]);

    const avgScore = dashboardData ? Math.round(dashboardData.overallAccuracy * 100) : 0;
    const lastAssessmentScore = dashboardData?.lastAssessment?.total > 0
        ? Math.round((dashboardData.lastAssessment.score / dashboardData.lastAssessment.total) * 100)
        : 0;

    return (
        <div className="min-h-screen bg-surface-50 dark:bg-surface-950">
            <Sidebar
                collapsed={collapsed}
                setCollapsed={setCollapsed}
                mobileOpen={mobileOpen}
                setMobileOpen={setMobileOpen}
            />

            <motion.main
                initial={false}
                animate={{ marginLeft: collapsed ? 72 : 240 }}
                transition={{ duration: 0.2 }}
                className="min-h-screen transition-[margin] hidden-lg:ml-0 max-lg:!ml-0"
            >
                <PageTransition>
                    {/* Header */}
                    <div className="sticky top-0 z-20 bg-surface-50/80 dark:bg-surface-950/80 backdrop-blur-xl border-b border-surface-200 dark:border-white/[0.04]">
                        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
                            <div className="pl-12 lg:pl-0">
                                <h1 className="text-xl font-heading font-bold text-surface-900 dark:text-white">
                                    Welcome back, <span className="text-gradient">{firstName}</span>
                                </h1>
                                <p className="text-sm text-surface-500 dark:text-surface-400">
                                    Continue your learning journey
                                </p>
                            </div>
                            <div className="flex items-center gap-3">
                                <ThemeToggle />
                                <div className="w-9 h-9 rounded-xl bg-hero-gradient flex items-center justify-center text-white font-heading text-sm font-bold cursor-pointer">
                                    {firstName[0]?.toUpperCase()}
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="px-6 lg:px-8 py-6 space-y-6">
                        {loading ? (
                            <div className="flex bg-surface-100 dark:bg-surface-800 animate-pulse rounded-xl h-40"></div>
                        ) : (
                            <>
                                {/* Stats Row */}
                                <motion.div
                                    variants={container}
                                    initial="hidden"
                                    animate="show"
                                    className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
                                >
                                    <StatCard label="Avg Score" value={avgScore} icon={TrendingUp} color="#22C55E" suffix="%" />
                                    <StatCard label="Last Assessment" value={lastAssessmentScore} icon={Award} color="#6C63FF" suffix="%" />
                                    <StatCard label="Weak Topics" value={dashboardData?.weakTopics?.length || 0} icon={AlertCircle} color="#F59E0B" />
                                </motion.div>

                                {/* Main Layout Grid */}
                                <div className="grid lg:grid-cols-3 gap-6">

                                    {/* Subject Performance & Weak Topics column */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.3 }}
                                        className="lg:col-span-2 space-y-6"
                                    >
                                        <Card hover={false}>
                                            <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4">
                                                Subject Performance
                                            </h3>

                                            {dashboardData?.subjectStats?.length > 0 ? (
                                                <div className="grid sm:grid-cols-2 gap-4">
                                                    {dashboardData.subjectStats.map((subject, idx) => {
                                                        const Icon = getIconForSubject(subject.subject)
                                                        const color = getSubjectColor(subject.subject)
                                                        const progress = Math.round(subject.accuracy * 100);
                                                        return (
                                                            <div
                                                                key={idx}
                                                                className="flex items-center gap-4 bg-surface-50 dark:bg-white/[0.02] p-4 rounded-xl border border-surface-200 dark:border-white/[0.04]"
                                                            >
                                                                <div
                                                                    className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                                                                    style={{ background: `${color}15` }}
                                                                >
                                                                    <Icon size={22} style={{ color: color }} />
                                                                </div>
                                                                <div className="flex-1 min-w-0">
                                                                    <p className="font-heading font-semibold text-surface-900 dark:text-white text-sm truncate">
                                                                        {subject.subject}
                                                                    </p>
                                                                    <p className="text-xs text-surface-400">{progress}% accuracy</p>
                                                                </div>
                                                                <ProgressRing
                                                                    value={progress}
                                                                    size={48}
                                                                    strokeWidth={4}
                                                                    color={color}
                                                                />
                                                            </div>
                                                        )
                                                    })}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-surface-500">Take an assessment to see your subject performance here.</p>
                                            )}
                                        </Card>

                                        {/* Weak Topics */}
                                        <Card hover={false}>
                                            <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4">
                                                Areas to Improve
                                            </h3>
                                            {dashboardData?.weakTopics?.length > 0 ? (
                                                <div className="space-y-3">
                                                    {dashboardData.weakTopics.map((topic, idx) => (
                                                        <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-red-50 dark:bg-red-500/10 border border-red-100 dark:border-red-500/20">
                                                            <div>
                                                                <p className="font-semibold text-sm text-surface-900 dark:text-white">{topic.topic}</p>
                                                                <p className="text-xs opacity-70">Level: <span className="capitalize">{topic.level}</span></p>
                                                            </div>
                                                            <div className="text-red-600 dark:text-red-400 font-bold text-sm">
                                                                {Math.round(topic.accuracy * 100)}%
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-surface-500">You are doing great! Keep practicing to uncover more weak topics.</p>
                                            )}
                                        </Card>
                                    </motion.div>

                                    {/* Sidebar Column (Quick Actions & Recommendations) */}
                                    <motion.div
                                        initial={{ opacity: 0, y: 20 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        transition={{ delay: 0.4 }}
                                        className="space-y-4"
                                    >
                                        <Card
                                            onClick={() => navigate('/quiz-setup')}
                                            className="bg-hero-gradient !border-0 cursor-pointer"
                                        >
                                            <h4 className="font-heading font-semibold text-white mb-1">Start Assessment</h4>
                                            <p className="text-sm text-white/70 mb-3">
                                                Test your knowledge now
                                            </p>
                                            <div className="flex items-center text-white/90 text-sm font-medium">
                                                Begin <ChevronRight size={16} className="ml-1" />
                                            </div>
                                        </Card>

                                        {/* Recommended Playlists */}
                                        <Card hover={false}>
                                            <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4 flex items-center gap-2">
                                                <PlayCircle size={18} className="text-accent" />
                                                Recommended Playlists
                                            </h3>

                                            {dashboardData?.recommendations?.length > 0 ? (
                                                <div className="space-y-3">
                                                    {dashboardData.recommendations.map((rec, idx) => (
                                                        <a
                                                            key={idx}
                                                            href={rec.youtubeUrl}
                                                            target="_blank"
                                                            rel="noopener noreferrer"
                                                            className="block p-3 rounded-lg border border-surface-200 dark:border-white/10 hover:border-accent dark:hover:border-accent transition-colors bg-surface-50 dark:bg-surface-800"
                                                        >
                                                            <p className="text-xs text-accent font-semibold mb-1">{rec.subject}</p>
                                                            <p className="text-sm text-surface-900 dark:text-white font-medium line-clamp-2">{rec.title}</p>
                                                        </a>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-sm text-surface-500">Complete assessments to get tailored video recommendations.</p>
                                            )}
                                        </Card>

                                        {/* Last Assessment */}
                                        {dashboardData?.lastAssessment && dashboardData.lastAssessment.total > 0 && (
                                            <Card className="text-center" glass>
                                                <p className="text-sm text-surface-500 dark:text-surface-400 mb-2">
                                                    Last Assessment Score
                                                </p>
                                                <div className="text-3xl font-heading font-bold text-accent mb-2">
                                                    {dashboardData.lastAssessment.score} / {dashboardData.lastAssessment.total}
                                                </div>
                                                <p className="text-xs text-surface-400">
                                                    {new Date(dashboardData.lastAssessment.completedAt).toLocaleDateString()}
                                                </p>
                                            </Card>
                                        )}
                                    </motion.div>
                                </div>
                            </>
                        )}
                    </div>
                </PageTransition>
            </motion.main>
        </div>
    )
}
