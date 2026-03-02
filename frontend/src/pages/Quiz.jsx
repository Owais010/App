import { useState, useEffect, useCallback } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Clock, ArrowRight, ChevronLeft, Star, Loader2 } from 'lucide-react'
import Card from '../components/Card'
import Button from '../components/Button'
import ProgressBar from '../components/ProgressBar'
import PageTransition from '../components/PageTransition'
import { startAssessment } from '../lib/api'
import { useAuth } from '../context/AuthContext'

export default function Quiz() {
    const { user } = useAuth()
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const subject = searchParams.get('subject') || ''
    const count = Math.min(Number(searchParams.get('count')) || 5, 10)
    const difficulty = searchParams.get('difficulty') || 'medium'
    const type = 'diagnostic' // Can dynamically set based on params if needed

    const [questions, setQuestions] = useState([])
    const [assessmentId, setAssessmentId] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const initQuiz = async () => {
            if (!user?.sessionToken) return;
            try {
                const payload = {
                    type: subject ? 'practice' : type,
                    numQuestions: count,
                };
                // If a valid UUID subject is passed, include it
                if (subject && subject.length > 20) {
                    payload.subjectId = subject;
                } else if (subject) {
                    // Slug-based subject — pass as subjectFilter for backend name matching
                    payload.subjectFilter = subject;
                }
                if (difficulty) {
                    payload.difficulty = difficulty;
                }
                const res = await startAssessment(user.sessionToken, payload);
                if (res.success) {
                    setQuestions(res.questions || []);
                    setAssessmentId(res.assessmentId);
                } else {
                    setError(res.error || 'Failed to start assessment');
                }
            } catch (err) {
                setError('Failed to fetch questions');
            } finally {
                setLoading(false);
            }
        };
        initQuiz();
    }, [user?.sessionToken, count, subject, type]);

    const [currentIndex, setCurrentIndex] = useState(0)
    const [selected, setSelected] = useState(null)
    const [answers, setAnswers] = useState([])
    const [timeLeft, setTimeLeft] = useState(count * 45)
    const [direction, setDirection] = useState(1)
    const [questionStartTime, setQuestionStartTime] = useState(Date.now())
    const [responseTimes, setResponseTimes] = useState([])
    const [showFeedback, setShowFeedback] = useState(false)
    const [confidence, setConfidence] = useState(0.5)
    const [difficultyRating, setDifficultyRating] = useState(3)

    const totalTime = count * 45

    // Timer
    useEffect(() => {
        if (loading || error || questions.length === 0) return;

        if (timeLeft <= 0) {
            navigate(`/results?subject=${subject}`, {
                state: { answers, assessmentId, timeSpent: totalTime },
            })
            return
        }
        const timer = setInterval(() => setTimeLeft((t) => t - 1), 1000)
        return () => clearInterval(timer)
    }, [timeLeft, navigate, subject, answers, assessmentId, totalTime, loading, error, questions])

    // Convert numeric index (0,1,2,3) to letter (A,B,C,D) for backend format
    const getOptionLetter = (index) => ['A', 'B', 'C', 'D'][index] || 'A';

    const handleKey = useCallback(
        (e) => {
            if (showFeedback) return
            const key = e.key
            if (['1', '2', '3', '4'].includes(key)) {
                setSelected(Number(key) - 1)
            }
            if (key === 'Enter' && selected !== null) {
                handleNext()
            }
        },
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [selected, currentIndex, showFeedback, questions, answers, responseTimes, confidence, questionStartTime]
    )

    useEffect(() => {
        window.addEventListener('keydown', handleKey)
        return () => window.removeEventListener('keydown', handleKey)
    }, [handleKey])

    const handleNext = () => {
        if (selected === null) return

        const timeTaken = (Date.now() - questionStartTime) / 1000
        const newResponseTimes = [...responseTimes, timeTaken]
        setResponseTimes(newResponseTimes)

        const currentQ = questions[currentIndex];
        const newAnswers = [...answers, {
            questionId: currentQ.questionId,
            assessmentQuestionId: currentQ.assessmentQuestionId,
            selectedOption: getOptionLetter(selected),
            timeTakenSeconds: timeTaken,
            confidenceRating: confidence // will update later when submitting, but just placeholder for now
        }]
        setAnswers(newAnswers)

        if (currentIndex >= questions.length - 1) {
            setShowFeedback(true)
        } else {
            setDirection(1)
            setSelected(null)
            setCurrentIndex((i) => i + 1)
            setQuestionStartTime(Date.now())
        }
    }

    const handleFinish = () => {
        const avgResponseTime = responseTimes.reduce((a, b) => a + b, 0) / (responseTimes.length || 1)

        // Update all answers with final confidence rating
        const finalAnswers = answers.map(a => ({
            ...a,
            confidenceRating: confidence
        }))

        navigate(`/results`, {
            state: {
                answers: finalAnswers,
                assessmentId,
                timeSpentSeconds: totalTime - timeLeft,
                telemetry: {
                    avg_response_time: avgResponseTime,
                    difficulty_feedback: difficultyRating
                }
            },
        })
    }

    const formatTime = (s) => {
        const m = Math.floor(s / 60)
        const sec = s % 60
        return `${m}:${sec.toString().padStart(2, '0')}`
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
                <p className="text-surface-500 font-heading">Generating your assessment...</p>
            </div>
        )
    }

    if (error || questions.length === 0) {
        return (
            <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center p-6 text-center">
                <h3 className="text-xl font-heading font-bold mb-2">Oops! Something went wrong</h3>
                <p className="text-surface-500 mb-6">{error || 'No questions currently available for this subject.'}</p>
                <Button onClick={() => navigate('/quiz-setup')}>Go Back</Button>
            </div>
        )
    }

    const q = questions[currentIndex] || {
        questionText: 'Error loading question.',
        options: [],
        difficulty: 'medium'
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
                        {showFeedback ? (
                            <motion.div
                                initial={{ opacity: 0, y: 20 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="bg-white dark:bg-surface-900 rounded-2xl p-8 border border-surface-200 dark:border-white/[0.04] text-center"
                            >
                                <h3 className="text-2xl font-heading font-bold mb-2 text-surface-900 dark:text-white">
                                    Quiz Complete!
                                </h3>
                                <p className="text-surface-500 mb-8">
                                    Help us personalize your next session by sharing your experience.
                                </p>

                                <div className="space-y-8 text-left">
                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-4">
                                            How confident did you feel about these questions?
                                        </label>
                                        <div className="flex items-center gap-4">
                                            <span className="text-xs text-surface-400">Guessed mostly</span>
                                            <input
                                                type="range"
                                                min="0"
                                                max="1"
                                                step="0.1"
                                                value={confidence}
                                                onChange={(e) => setConfidence(parseFloat(e.target.value))}
                                                className="w-full h-2 bg-surface-200 rounded-lg appearance-none cursor-pointer dark:bg-surface-700"
                                            />
                                            <span className="text-xs text-surface-400">Very confident</span>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-4">
                                            How would you rate the difficulty? (1-5)
                                        </label>
                                        <div className="flex justify-center gap-2">
                                            {[1, 2, 3, 4, 5].map((star) => (
                                                <button
                                                    key={star}
                                                    onClick={() => setDifficultyRating(star)}
                                                    className={`p-2 rounded-full transition-colors ${difficultyRating >= star
                                                            ? 'text-yellow-400'
                                                            : 'text-surface-300 dark:text-surface-600 hover:text-yellow-400/50'
                                                        }`}
                                                >
                                                    <Star fill={difficultyRating >= star ? 'currentColor' : 'none'} size={32} />
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                <div className="mt-10 pt-6 border-t border-surface-100 dark:border-white/[0.04]">
                                    <Button onClick={handleFinish} size="lg" className="w-full justify-center">
                                        See Results
                                        <ArrowRight size={18} />
                                    </Button>
                                </div>
                            </motion.div>
                        ) : (
                            <>
                                <div className="mb-2">
                                    <span className="text-xs font-medium text-primary bg-primary/10 px-2.5 py-1 rounded-md capitalize">
                                        Level: {q.difficulty || 'Medium'}
                                    </span>
                                </div>

                                <h2 className="text-xl md:text-2xl font-heading font-bold text-surface-900 dark:text-white mb-8 leading-relaxed">
                                    {q.questionText}
                                </h2>

                                <div className="space-y-3">
                                    {q.options?.map((option, i) => (
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
                            </>
                        )}
                    </motion.div>
                </AnimatePresence>
            </div>
        </PageTransition>
    )
}
