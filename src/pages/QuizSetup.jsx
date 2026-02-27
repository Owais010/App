import { useState, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Clock, HelpCircle, Zap, ArrowRight, ChevronLeft } from 'lucide-react'
import Sidebar from '../components/Sidebar'
import Card from '../components/Card'
import Button from '../components/Button'
import PageTransition from '../components/PageTransition'
import ThemeToggle from '../components/ThemeToggle'
import { subjects } from '../data'

const difficulties = [
    { id: 'easy', label: 'Easy', color: '#22C55E', desc: 'Fundamental concepts' },
    { id: 'medium', label: 'Medium', color: '#F59E0B', desc: 'Application level' },
    { id: 'hard', label: 'Hard', color: '#EF4444', desc: 'Advanced problems' },
]

export default function QuizSetup() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const [collapsed, setCollapsed] = useState(false)
    const [mobileOpen, setMobileOpen] = useState(false)
    const [selectedSubject, setSelectedSubject] = useState(searchParams.get('subject') || subjects[0].courses[0].id)
    const [difficulty, setDifficulty] = useState('medium')
    const [questionCount, setQuestionCount] = useState(5)

    const estimatedTime = useMemo(() => {
        const perQ = difficulty === 'easy' ? 30 : difficulty === 'medium' ? 45 : 60
        const total = perQ * questionCount
        const mins = Math.floor(total / 60)
        const secs = total % 60
        return `${mins}:${secs.toString().padStart(2, '0')}`
    }, [difficulty, questionCount])

    const startQuiz = () => {
        navigate(`/quiz?subject=${selectedSubject}&difficulty=${difficulty}&count=${questionCount}`)
    }

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
                                    Quiz Setup
                                </h1>
                            </div>
                            <ThemeToggle />
                        </div>
                    </div>

                    <div className="px-6 lg:px-8 py-8 max-w-3xl mx-auto space-y-8">
                        {/* Subject */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                        >
                            <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-3">
                                Choose Subject
                            </h3>
                            <div className="space-y-6">
                                {subjects.map((semester) => (
                                    <div key={semester.semester}>
                                        <h4 className="text-sm font-semibold text-surface-500 dark:text-surface-400 mb-3 ml-1 uppercase tracking-wider">
                                            {semester.semester}
                                        </h4>
                                        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                                            {semester.courses.map((s) => (
                                                <motion.button
                                                    key={s.id}
                                                    whileHover={{ scale: 1.02 }}
                                                    whileTap={{ scale: 0.98 }}
                                                    onClick={() => setSelectedSubject(s.id)}
                                                    className={`p-3 rounded-xl border-2 cursor-pointer transition-all duration-200 text-center flex flex-col items-center justify-center gap-2 h-24 ${selectedSubject === s.id
                                                        ? 'border-primary bg-primary/5 dark:bg-primary/10'
                                                        : 'border-surface-200 dark:border-white/[0.06] hover:border-primary/30'
                                                        }`}
                                                >
                                                    <p className="font-heading font-semibold text-xs sm:text-sm text-surface-900 dark:text-white line-clamp-2 leading-tight">
                                                        {s.name}
                                                    </p>
                                                </motion.button>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </motion.div>

                        {/* Difficulty */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.1 }}
                        >
                            <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-3">
                                Difficulty
                            </h3>
                            <div className="grid grid-cols-3 gap-3">
                                {difficulties.map((d) => (
                                    <motion.button
                                        key={d.id}
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={() => setDifficulty(d.id)}
                                        className={`p-4 rounded-xl border-2 cursor-pointer transition-all duration-200 ${difficulty === d.id
                                            ? 'border-primary bg-primary/5 dark:bg-primary/10'
                                            : 'border-surface-200 dark:border-white/[0.06] hover:border-primary/30'
                                            }`}
                                    >
                                        <div
                                            className="w-3 h-3 rounded-full mx-auto mb-2"
                                            style={{ background: d.color }}
                                        />
                                        <p className="font-heading font-semibold text-sm text-surface-900 dark:text-white">
                                            {d.label}
                                        </p>
                                        <p className="text-xs text-surface-400 mt-1">{d.desc}</p>
                                    </motion.button>
                                ))}
                            </div>
                        </motion.div>

                        {/* Question Count */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.2 }}
                        >
                            <div className="flex items-center justify-between mb-3">
                                <h3 className="font-heading font-semibold text-surface-900 dark:text-white">
                                    Questions
                                </h3>
                                <span className="text-2xl font-heading font-bold text-primary">{questionCount}</span>
                            </div>
                            <input
                                type="range"
                                min={3}
                                max={10}
                                value={questionCount}
                                onChange={(e) => setQuestionCount(Number(e.target.value))}
                                className="w-full h-2 rounded-full appearance-none cursor-pointer bg-surface-200 dark:bg-white/[0.06]
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5
                  [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-primary
                  [&::-webkit-slider-thumb]:shadow-glow [&::-webkit-slider-thumb]:cursor-pointer"
                            />
                            <div className="flex justify-between text-xs text-surface-400 mt-1">
                                <span>3</span>
                                <span>10</span>
                            </div>
                        </motion.div>

                        {/* Preview Card */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.3 }}
                        >
                            <Card glass>
                                <h4 className="font-heading font-semibold text-surface-900 dark:text-white mb-4">
                                    Quiz Preview
                                </h4>
                                <div className="grid grid-cols-3 gap-4 text-center">
                                    <div>
                                        <HelpCircle size={20} className="text-primary mx-auto mb-1" />
                                        <p className="text-lg font-heading font-bold text-surface-900 dark:text-white">
                                            {questionCount}
                                        </p>
                                        <p className="text-xs text-surface-400">Questions</p>
                                    </div>
                                    <div>
                                        <Clock size={20} className="text-accent mx-auto mb-1" />
                                        <p className="text-lg font-heading font-bold text-surface-900 dark:text-white">
                                            {estimatedTime}
                                        </p>
                                        <p className="text-xs text-surface-400">Est. Time</p>
                                    </div>
                                    <div>
                                        <Zap size={20} className="text-amber-400 mx-auto mb-1" />
                                        <p className="text-lg font-heading font-bold text-surface-900 dark:text-white capitalize">
                                            {difficulty}
                                        </p>
                                        <p className="text-xs text-surface-400">Difficulty</p>
                                    </div>
                                </div>
                            </Card>
                        </motion.div>

                        {/* Start Button */}
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: 0.4 }}
                        >
                            <Button size="lg" className="w-full" onClick={startQuiz}>
                                Start Quiz
                                <ArrowRight size={18} />
                            </Button>
                        </motion.div>
                    </div>
                </PageTransition>
            </motion.main>
        </div>
    )
}
