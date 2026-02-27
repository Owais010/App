import { useState, useEffect, useCallback, useMemo } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, ArrowRight, ChevronLeft } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import ProgressBar from '../components/ProgressBar'
import PageTransition from '../components/PageTransition'
import { quizQuestions } from '../data'

export default function Quiz() {
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const subject = searchParams.get('subject') || 'mathematics'
    const count = Math.min(Number(searchParams.get('count')) || 5, 10)

    const questions = useMemo(() => {
        // Find questions for the subject, fallback to 'data-structures' if it exists to prevent crashes
        const qList = quizQuestions[subject] || quizQuestions['data-structures'] || []
        return qList.slice(0, count)
    }, [subject, count])

    const [currentIndex, setCurrentIndex] = useState(0)
    const [selected, setSelected] = useState(null)
    const [answers, setAnswers] = useState([])
    const [timeLeft, setTimeLeft] = useState(count * 45)
    const [direction, setDirection] = useState(1)

    const totalTime = count * 45

    // Timer
    useEffect(() => {
        if (timeLeft <= 0) {
            navigate(`/results?subject=${subject}`, {
                state: { answers, questions, timeSpent: totalTime },
            })
            return
        }
        const timer = setInterval(() => setTimeLeft((t) => t - 1), 1000)
        return () => clearInterval(timer)
    }, [timeLeft, navigate, subject, answers, questions, totalTime])

    // Keyboard nav
    const handleKey = useCallback(
        (e) => {
            const key = e.key
            if (['1', '2', '3', '4'].includes(key)) {
                setSelected(Number(key) - 1)
            }
            if (key === 'Enter' && selected !== null) {
                handleNext()
            }
        },
        [selected, currentIndex]
    )

    useEffect(() => {
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [handleKey])

    const handleNext = () => {
        if (selected === null) return
        const newAnswers = [...answers, { questionId: questions[currentIndex].id, selected }]
        setAnswers(newAnswers)

        if (currentIndex >= questions.length - 1) {
            navigate(`/results?subject=${subject}`, {
                state: { answers: newAnswers, questions, timeSpent: totalTime - timeLeft },
            })
        } else {
            setDirection(1)
            setSelected(null)
            setCurrentIndex((i) => i + 1)
        }
    }

    const formatTime = (s) => {
        const m = Math.floor(s / 60)
        const sec = s % 60
        return `${m}:${sec.toString().padStart(2, '0')}`
    }

    const q = questions[currentIndex] || {
        id: -1,
        question: 'No questions available for this subject yet.',
        options: ['Return to Setup'],
        topic: 'Error',
        correct: 0
    }
    const timerWarning = timeLeft < 30

    const slideVariants = {
        enter: (d) => ({ x: d > 0 ? 200 : -200, opacity: 0 }),
        center: { x: 0, opacity: 1 },
        exit: (d) => ({ x: d > 0 ? -200 : 200, opacity: 0 }),
    }

    return (
        <PageTransition className="min-h-screen bg-surface-50 dark:bg-surface-950">
            {/* Top Bar */}
            <div className="sticky top-0 z-20 bg-surface-50/80 dark:bg-surface-950/80 backdrop-blur-xl border-b border-surface-200 dark:border-white/[0.04]">
                <div className="max-w-3xl mx-auto px-6 py-4">
                    <div className="flex items-center justify-between mb-3">
                        <button
                            onClick={() => navigate('/quiz-setup')}
                            className="flex items-center gap-1 text-sm text-surface-400 hover:text-surface-600 dark:hover:text-surface-300 cursor-pointer transition-colors"
                        >
                            <ChevronLeft size={16} />
                            Exit
                        </button>
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg ${timerWarning
                            ? 'bg-red-500/10 text-red-400'
                            : 'bg-surface-100 dark:bg-white/[0.04] text-surface-600 dark:text-surface-300'
                            }`}>
                            <Clock size={14} className={timerWarning ? 'animate-pulse' : ''} />
                            <span className="font-heading text-sm font-semibold">
                                {formatTime(timeLeft)}
                            </span>
                        </div>
                        <span className="text-sm font-heading font-medium text-surface-500">
                            {currentIndex + 1}/{questions.length}
                        </span>
                    </div>
                    <ProgressBar
                        value={currentIndex + 1}
                        max={questions.length}
                        color="gradient"
                        size="sm"
                        animated={false}
                    />
                </div>
            </div>

            {/* Question Area */}
            <div className="max-w-3xl mx-auto px-6 py-10">
                <AnimatePresence mode="wait" custom={direction}>
                    <motion.div
                        key={currentIndex}
                        custom={direction}
                        variants={slideVariants}
                        initial="enter"
                        animate="center"
                        exit="exit"
                        transition={{ duration: 0.3, ease: 'easeOut' }}
                    >
                        <div className="mb-2">
                            <span className="text-xs font-medium text-primary bg-primary/10 px-2.5 py-1 rounded-md">
                                {q.topic}
                            </span>
                        </div>

                        <h2 className="text-xl md:text-2xl font-heading font-bold text-surface-900 dark:text-white mb-8 leading-relaxed">
                            {q.question}
                        </h2>

                        <div className="space-y-3">
                            {q.options.map((option, i) => (
                                <motion.button
                                    key={i}
                                    whileHover={{ scale: 1.01 }}
                                    whileTap={{ scale: 0.99 }}
                                    onClick={() => setSelected(i)}
                                    className={`w-full text-left px-5 py-4 rounded-xl border-2 cursor-pointer transition-all duration-200 flex items-center gap-4 ${selected === i
                                        ? 'border-primary bg-primary/5 dark:bg-primary/10 shadow-glow/20'
                                        : 'border-surface-200 dark:border-white/[0.06] hover:border-primary/30 bg-white dark:bg-surface-800/40'
                                        }`}
                                >
                                    <span
                                        className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-heading font-bold flex-shrink-0 transition-colors ${selected === i
                                            ? 'bg-primary text-white'
                                            : 'bg-surface-100 dark:bg-white/[0.06] text-surface-500'
                                            }`}
                                    >
                                        {i + 1}
                                    </span>
                                    <span className="font-body text-surface-700 dark:text-surface-300">
                                        {option}
                                    </span>
                                </motion.button>
                            ))}
                        </div>

                        <div className="mt-8 flex justify-end">
                            <Button
                                onClick={handleNext}
                                disabled={selected === null}
                                size="lg"
                            >
                                {currentIndex >= questions.length - 1 ? 'Finish' : 'Next'}
                                <ArrowRight size={18} />
                            </Button>
                        </div>

                        <p className="mt-4 text-xs text-center text-surface-400">
                            Press 1-4 to select, Enter to continue
                        </p>
                    </motion.div>
                </AnimatePresence>
            </div>
        </PageTransition>
    )
}
