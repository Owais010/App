import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    Calculator, Atom, FlaskConical, Flame, TrendingUp,
    Clock, ChevronRight, Award, Code, BookOpen, Sigma,
    Zap, PenTool, Network, Cpu, Database, Terminal, Leaf,
    BarChart3, Server, MonitorPlay, Coffee, GitGraph,
    Globe, BrainCircuit, LayoutTemplate, Brain, Cloud,
    LineChart, Shield, Wifi, Rocket
} from 'lucide-react'
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts'
import { useAuth } from '../context/AuthContext'
import Sidebar from '../components/Sidebar'
import Card from '../components/Card'
import { ProgressRing } from '../components/ProgressBar'
import ThemeToggle from '../components/ThemeToggle'
import PageTransition from '../components/PageTransition'
import { useCountUp, useInView } from '../hooks'
import { subjects, weeklyProgress, recentActivity } from '../data'

const iconMap = {
    Calculator, Atom, FlaskConical, Code, BookOpen, Sigma,
    Zap, PenTool, Network, Cpu, Database, Terminal, Leaf,
    BarChart3, Server, MonitorPlay, Coffee, GitGraph,
    Globe, BrainCircuit, LayoutTemplate, Brain, Cloud,
    LineChart, Shield, Wifi, Rocket
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

const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null
    return (
        <div className="bg-white dark:bg-surface-800 rounded-xl px-4 py-3 shadow-xl border border-surface-200 dark:border-white/[0.08]">
            <p className="text-xs text-surface-400 mb-1">{label}</p>
            <p className="text-sm font-heading font-semibold text-surface-900 dark:text-white">
                Score: {payload[0].value}%
            </p>
        </div>
    )
}

export default function Dashboard() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    const firstName = user?.user_metadata?.full_name?.split(' ')[0]
        || user?.email?.split('@')[0]
        || 'Learner'

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
                        {/* Stats Row */}
                        <motion.div
                            variants={container}
                            initial="hidden"
                            animate="show"
                            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4"
                        >
                            <StatCard label="Total Quizzes" value={47} icon={Award} color="#6C63FF" />
                            <StatCard label="Avg Score" value={78} icon={TrendingUp} color="#22C55E" suffix="%" />
                            <StatCard label="Day Streak" value={12} icon={Flame} color="#F59E0B" />
                            <StatCard label="Total XP" value={2450} icon={Zap} color="#06B6D4" suffix=" XP" />
                        </motion.div>

                        {/* Main Grid */}
                        <div className="grid lg:grid-cols-3 gap-6">
                            {/* Progress Chart */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.3 }}
                                className="lg:col-span-2"
                            >
                                <Card hover={false}>
                                    <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4">
                                        Weekly Performance
                                    </h3>
                                    <div className="h-64">
                                        <ResponsiveContainer width="100%" height="100%">
                                            <AreaChart data={weeklyProgress}>
                                                <defs>
                                                    <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                                                        <stop offset="0%" stopColor="#6C63FF" stopOpacity={0.3} />
                                                        <stop offset="100%" stopColor="#6C63FF" stopOpacity={0} />
                                                    </linearGradient>
                                                </defs>
                                                <XAxis
                                                    dataKey="day"
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fontSize: 12, fill: '#94A3B8' }}
                                                />
                                                <YAxis
                                                    axisLine={false}
                                                    tickLine={false}
                                                    tick={{ fontSize: 12, fill: '#94A3B8' }}
                                                    domain={[0, 100]}
                                                />
                                                <Tooltip content={<CustomTooltip />} />
                                                <Area
                                                    type="monotone"
                                                    dataKey="score"
                                                    stroke="#6C63FF"
                                                    strokeWidth={2.5}
                                                    fill="url(#scoreGradient)"
                                                    dot={{ r: 4, fill: '#6C63FF', strokeWidth: 2, stroke: '#fff' }}
                                                    activeDot={{ r: 6, fill: '#6C63FF' }}
                                                    isAnimationActive={true}
                                                    animationDuration={1500}
                                                    animationEasing="ease-out"
                                                />
                                            </AreaChart>
                                        </ResponsiveContainer>
                                    </div>
                                </Card>
                            </motion.div>

                            {/* Streak / Quick Actions */}
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ delay: 0.4 }}
                                className="space-y-4"
                            >
                                <Card className="text-center" glass>
                                    <div className="inline-flex items-center gap-2 mb-3">
                                        <Flame size={20} className="text-amber-400" />
                                        <span className="font-heading font-semibold text-surface-900 dark:text-white">
                                            12 Day Streak
                                        </span>
                                    </div>
                                    <p className="text-sm text-surface-500 dark:text-surface-400 mb-4">
                                        Keep going! You&apos;re on fire!
                                    </p>
                                    <div className="flex justify-center gap-1">
                                        {[...Array(7)].map((_, i) => (
                                            <div
                                                key={i}
                                                className={`w-7 h-7 rounded-md flex items-center justify-center text-xs font-heading font-medium ${i < 5
                                                    ? 'bg-accent/20 text-accent'
                                                    : 'bg-surface-100 dark:bg-white/[0.04] text-surface-400'
                                                    }`}
                                            >
                                                {['M', 'T', 'W', 'T', 'F', 'S', 'S'][i]}
                                            </div>
                                        ))}
                                    </div>
                                </Card>

                                <Card
                                    onClick={() => navigate('/quiz-setup')}
                                    className="bg-hero-gradient !border-0 cursor-pointer"
                                >
                                    <h4 className="font-heading font-semibold text-white mb-1">Start a Quiz</h4>
                                    <p className="text-sm text-white/70 mb-3">
                                        Test your knowledge now
                                    </p>
                                    <div className="flex items-center text-white/90 text-sm font-medium">
                                        Begin <ChevronRight size={16} className="ml-1" />
                                    </div>
                                </Card>
                            </motion.div>
                        </div>

                        {/* Subjects */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.5 }}
                        >
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="font-heading font-semibold text-surface-900 dark:text-white">
                                    Your Subjects
                                </h3>
                                <button
                                    onClick={() => navigate('/quiz-setup')}
                                    className="text-sm text-accent hover:text-accent-light transition-colors font-medium"
                                >
                                    View All Curriculum
                                </button>
                            </div>
                            <div className="grid sm:grid-cols-3 gap-4">
                                {subjects.flatMap(s => s.courses).slice(0, 6).map((subject) => {
                                    const Icon = iconMap[subject.icon] || Calculator
                                    return (
                                        <Card
                                            key={subject.id}
                                            onClick={() => navigate(`/quiz-setup?subject=${subject.id}`)}
                                            className="flex items-center gap-4 cursor-pointer"
                                        >
                                            <div
                                                className="w-12 h-12 rounded-xl flex items-center justify-center flex-shrink-0"
                                                style={{ background: `${subject.color}15` }}
                                            >
                                                <Icon size={22} style={{ color: subject.color }} />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <p className="font-heading font-semibold text-surface-900 dark:text-white text-sm truncate">
                                                    {subject.name}
                                                </p>
                                                <p className="text-xs text-surface-400">{subject.progress}% complete</p>
                                            </div>
                                            <ProgressRing
                                                value={subject.progress}
                                                size={48}
                                                strokeWidth={4}
                                                color={subject.color}
                                            />
                                        </Card>
                                    )
                                })}
                            </div>
                        </motion.div>

                        {/* Recent Activity */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.6 }}
                        >
                            <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4">
                                Recent Activity
                            </h3>
                            <Card hover={false} padding="p-0">
                                <div className="divide-y divide-surface-100 dark:divide-white/[0.04]">
                                    {recentActivity.map((act) => (
                                        <div
                                            key={act.id}
                                            className="flex items-center justify-between px-6 py-4 hover:bg-surface-50 dark:hover:bg-white/[0.02] transition-colors cursor-pointer"
                                        >
                                            <div>
                                                <p className="font-medium text-sm text-surface-900 dark:text-white">
                                                    {act.subject} — {act.topic}
                                                </p>
                                                <p className="text-xs text-surface-400 mt-0.5">
                                                    {act.questions} questions · {act.date}
                                                </p>
                                            </div>
                                            <div className={`text-sm font-heading font-bold ${act.score >= 80 ? 'text-accent' : act.score >= 60 ? 'text-amber-400' : 'text-red-400'
                                                }`}>
                                                {act.score}%
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </Card>
                        </motion.div>
                    </div>
                </PageTransition>
            </motion.main>
        </div>
    )
}
