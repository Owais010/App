import { useState } from 'react'
import { motion } from 'framer-motion'
import {
    Trophy, Flame, Star, Zap, GraduationCap, Brain,
    ChevronLeft, Lock,
} from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import Sidebar from '../components/Sidebar'
import Card from '../components/Card'
import PageTransition from '../components/PageTransition'
import ThemeToggle from '../components/ThemeToggle'
import { achievements } from '../data'

const iconMap = { Trophy, Flame, Star, Zap, GraduationCap, Brain }

const container = {
    hidden: { opacity: 0 },
    show: { opacity: 1, transition: { staggerChildren: 0.1 } },
}
const item = {
    hidden: { opacity: 0, y: 16 },
    show: { opacity: 1, y: 0 },
}

export default function Achievements() {
    const navigate = useNavigate()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)

    const unlocked = achievements.filter((a) => a.unlocked).length
    const total = achievements.length

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
                className="min-h-screen max-lg:!ml-0"
            >
                <PageTransition>
                    <div className="sticky top-0 z-20 bg-surface-50/80 dark:bg-surface-950/80 backdrop-blur-xl border-b border-surface-200 dark:border-white/[0.04]">
                        <div className="px-6 lg:px-8 py-4 flex items-center justify-between">
                            <div className="flex items-center gap-3 pl-12 lg:pl-0">
                                <button
                                    onClick={() => navigate('/dashboard')}
                                    className="p-2 rounded-xl hover:bg-surface-100 dark:hover:bg-white/5 cursor-pointer transition-colors"
                                >
                                    <ChevronLeft size={20} className="text-surface-500" />
                                </button>
                                <h1 className="text-xl font-heading font-bold text-surface-900 dark:text-white">
                                    Achievements
                                </h1>
                            </div>
                            <ThemeToggle />
                        </div>
                    </div>

                    <div className="px-6 lg:px-8 py-8 max-w-4xl mx-auto">
                        {/* Progress Header */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mb-8"
                        >
                            <Card glass className="text-center py-8">
                                <div className="w-16 h-16 rounded-2xl bg-hero-gradient flex items-center justify-center mx-auto mb-4">
                                    <Trophy size={28} className="text-white" />
                                </div>
                                <h2 className="text-2xl font-heading font-bold text-surface-900 dark:text-white mb-2">
                                    {unlocked} of {total} Unlocked
                                </h2>
                                <p className="text-surface-500 dark:text-surface-400 text-sm">
                                    Keep going to unlock all achievements!
                                </p>
                                <div className="mt-4 max-w-xs mx-auto">
                                    <div className="h-2.5 bg-surface-200 dark:bg-white/[0.06] rounded-full overflow-hidden">
                                        <motion.div
                                            initial={{ width: 0 }}
                                            animate={{ width: `${(unlocked / total) * 100}%` }}
                                            transition={{ duration: 1, ease: 'easeOut', delay: 0.3 }}
                                            className="h-full rounded-full bg-gradient-to-r from-primary via-accent to-cyan-400"
                                        />
                                    </div>
                                </div>
                            </Card>
                        </motion.div>

                        {/* Badges Grid */}
                        <motion.div
                            variants={container}
                            initial="hidden"
                            animate="show"
                            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
                        >
                            {achievements.map((achievement) => {
                                const Icon = iconMap[achievement.icon] || Trophy
                                return (
                                    <motion.div key={achievement.id} variants={item}>
                                        <Card
                                            className={`relative text-center py-8 ${!achievement.unlocked ? 'opacity-60' : ''
                                                }`}
                                        >
                                            {!achievement.unlocked && (
                                                <div className="absolute top-3 right-3">
                                                    <Lock size={14} className="text-surface-400" />
                                                </div>
                                            )}
                                            <div
                                                className={`w-14 h-14 rounded-2xl flex items-center justify-center mx-auto mb-4 ${achievement.unlocked
                                                        ? 'bg-primary/10 dark:bg-primary/20'
                                                        : 'bg-surface-100 dark:bg-white/[0.04]'
                                                    }`}
                                            >
                                                <Icon
                                                    size={24}
                                                    className={
                                                        achievement.unlocked
                                                            ? 'text-primary'
                                                            : 'text-surface-400'
                                                    }
                                                />
                                            </div>
                                            <h4 className="font-heading font-semibold text-surface-900 dark:text-white mb-1">
                                                {achievement.name}
                                            </h4>
                                            <p className="text-xs text-surface-400">{achievement.desc}</p>
                                            {achievement.unlocked && (
                                                <motion.div
                                                    initial={{ scale: 0 }}
                                                    animate={{ scale: 1 }}
                                                    transition={{ delay: 0.5, type: 'spring' }}
                                                    className="mt-3 inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-accent/10 text-accent text-xs font-medium"
                                                >
                                                    <Star size={12} className="fill-accent" />
                                                    Unlocked
                                                </motion.div>
                                            )}
                                        </Card>
                                    </motion.div>
                                )
                            })}
                        </motion.div>
                    </div>
                </PageTransition>
            </motion.main>
        </div>
    )
}
