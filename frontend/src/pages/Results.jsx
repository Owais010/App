import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
    Trophy, Target, RotateCcw, ArrowRight, Star, TrendingUp, Loader2
} from 'lucide-react'
import confetti from 'canvas-confetti'
import Card from '../components/Card'
import Button from '../components/Button'
import { ProgressRing } from '../components/ProgressBar'
import PageTransition from '../components/PageTransition'
import { useAuth } from '../context/AuthContext'
import { finishAssessment } from '../lib/api'
import { predictLevel, predictDifficulty } from '../lib/mlService'

function getBadge(scorePercent) {
    if (scorePercent >= 90) return { label: 'Outstanding', color: '#6C63FF', icon: Trophy }
    if (scorePercent >= 70) return { label: 'Great Job', color: '#22C55E', icon: Star }
    if (scorePercent >= 50) return { label: 'Keep Going', color: '#F59E0B', icon: TrendingUp }
    return { label: 'Needs Practice', color: '#EF4444', icon: Target }
}

export default function Results() {
    const navigate = useNavigate()
    const [searchParams] = useSearchParams()
    const location = useLocation()
    const { user } = useAuth()
    const subject = searchParams.get('subject') || 'mathematics'
    const { answers = [], assessmentId, timeSpentSeconds = 0, telemetry } = location.state || {}

    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [resultData, setResultData] = useState(null)
    const [displayScorePercent, setDisplayScorePercent] = useState(0)

    const [mlData, setMlData] = useState(null)
    const [mlLoading, setMlLoading] = useState(false)
    const [mlError, setMlError] = useState(null)

    useEffect(() => {
        const submitAssessment = async () => {
            if (!user?.sessionToken || !assessmentId) {
                setError("Missing assessment data.");
                setLoading(false);
                return;
            }

            try {
                const payload = {
                    assessmentId,
                    answers,
                    timeSpentSeconds
                };
                const res = await finishAssessment(user.sessionToken, payload);
                if (res.success) {
                    setResultData(res);
                } else {
                    setError(res.error || 'Failed to submit assessment');
                }
            } catch (err) {
                setError('Failed to calculate results');
            } finally {
                setLoading(false);
            }
        };

        submitAssessment();
    }, [user?.sessionToken, assessmentId, answers, timeSpentSeconds]);

    useEffect(() => {
        // Fetch ML predictions after results are loaded
        const fetchMLData = async () => {
            if (!user || !resultData) return;
            setMlLoading(true);
            try {
                const userId = user.id || 'anonymous_user';
                const topicId = subject;
                const accuracy = resultData.total > 0 ? resultData.score / resultData.total : 0;
                const avgTime = answers.length > 0 && timeSpentSeconds > 0
                    ? timeSpentSeconds / answers.length : 10;

                // Build a feature vector from the actual quiz results
                const features = {
                    total_attempts: answers.length,
                    correct_attempts: resultData.score,
                    accuracy: accuracy,
                    weighted_score: accuracy * 100,
                    recent_accuracy: accuracy,
                    accuracy_trend: 0.0,
                    streak_length: 0,
                    avg_time_per_q: avgTime,
                    days_since_last: 0,
                    easy_accuracy: accuracy,
                    medium_accuracy: accuracy,
                    hard_accuracy: accuracy,
                    global_accuracy: accuracy,
                    topics_attempted: 1
                };

                // Call both endpoints in parallel
                const [levelRes, diffRes] = await Promise.all([
                    predictLevel(userId, topicId, features),
                    predictDifficulty(userId, topicId, features)
                ]);

                // Derive recommended action from level + actual accuracy
                const level = levelRes?.predicted_level;
                const conf = levelRes?.confidence || 0;
                let action = 'Continue Practicing';
                if (accuracy >= 0.9) action = 'Try Harder Topics';
                else if (accuracy >= 0.7) action = 'Level Up';
                else if (level === 'beginner' && conf > 0.5) action = 'Focus on Basics';
                else if (accuracy < 0.5) action = 'Focus on Basics';
                else action = 'Keep Practicing';

                // Compute skill gap from accuracy vs. advanced threshold
                const advProb = levelRes?.probabilities?.advanced || 0;
                const skillGap = Math.max(0, 1 - advProb - accuracy);
                const isWeak = accuracy < 0.5;

                // Topic ranking based on difficulty confidence and success prob
                const rankScore = diffRes
                    ? (diffRes.predicted_success_prob || 0) * 0.6 + (diffRes.confidence || 0) * 0.4
                    : 0;

                setMlData({
                    action,
                    predicted_level: levelRes?.predicted_level || 'unknown',
                    level_confidence: levelRes?.confidence || 0,
                    skill_gap: skillGap,
                    is_weak: isWeak,
                    difficulty_level: diffRes?.recommended_difficulty || 'medium',
                    success_prob: diffRes?.predicted_success_prob || 0,
                    rank_score: rankScore,
                    model_used: levelRes?.model_used || diffRes?.model_used || 'rules'
                });
            } catch (err) {
                setMlError(err.message);
            } finally {
                setMlLoading(false);
            }
        };

        fetchMLData();
    }, [user, resultData, subject, answers, timeSpentSeconds]);

    const scorePercent = resultData && resultData.total > 0
        ? Math.round((resultData.score / resultData.total) * 100)
        : 0;

    useEffect(() => {
        if (!resultData) return;

        // Animate score from 0 to actual score
        const duration = 1500;
        const start = Date.now();
        const end = start + duration;

        const animateScore = () => {
            const now = Date.now();
            const progress = Math.min((now - start) / duration, 1);
            // Ease out cubic
            const easeProgress = 1 - Math.pow(1 - progress, 3);
            setDisplayScorePercent(Math.round(scorePercent * easeProgress));

            if (progress < 1) {
                requestAnimationFrame(animateScore);
            }
        };
        requestAnimationFrame(animateScore);

        if (scorePercent >= 80) {
            const endConfetti = Date.now() + 2000
            const frame = () => {
                confetti({
                    particleCount: 3,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0, y: 0.7 },
                    colors: ['#6C63FF', '#22C55E', '#06B6D4'],
                })
                confetti({
                    particleCount: 3,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1, y: 0.7 },
                    colors: ['#6C63FF', '#22C55E', '#06B6D4'],
                })
                if (Date.now() < endConfetti) requestAnimationFrame(frame)
            }
            frame()
        }
    }, [scorePercent, resultData])

    const formatTime = (s) => {
        const m = Math.floor(s / 60)
        const sec = s % 60
        return `${m}m ${sec}s`
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center">
                <Loader2 className="w-8 h-8 text-primary animate-spin mb-4" />
                <p className="text-surface-500 font-heading">Analyzing your results...</p>
            </div>
        )
    }

    if (error || !resultData) {
        return (
            <div className="min-h-screen bg-surface-50 dark:bg-surface-950 flex flex-col items-center justify-center p-6 text-center">
                <h3 className="text-xl font-heading font-bold mb-2">Oops! Something went wrong</h3>
                <p className="text-surface-500 mb-6">{error || 'Could not load your results.'}</p>
                <Button onClick={() => navigate('/dashboard')}>Go to Dashboard</Button>
            </div>
        )
    }

    const badge = getBadge(scorePercent)
    const BadgeIcon = badge.icon

    // Use backend recommendations if provided, else fallback to standard
    const recommendations = resultData.recommendations?.length > 0
        ? resultData.recommendations
        : [
            {
                title: 'Review Weak Areas',
                desc: 'Focus on topics where you struggled',
                action: 'View Topics',
                link: '#'
            },
            {
                title: 'Practice Daily',
                desc: 'Consistent practice improves retention by 40%',
                action: 'Set Reminder',
                link: '#'
            },
        ];

    return (
        <PageTransition className="min-h-screen bg-surface-50 dark:bg-surface-950 py-12 px-6">
            <div className="max-w-4xl mx-auto">
                {/* Score Section */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.6, type: 'spring' }}
                    className="text-center mb-10"
                >
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
                        className="inline-block mb-6"
                    >
                        <ProgressRing value={scorePercent} size={140} strokeWidth={8} color={badge.color} />
                    </motion.div>

                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 }}
                    >
                        <div
                            className="inline-flex items-center gap-2 px-4 py-2 rounded-full mb-4"
                            style={{ background: `${badge.color}15` }}
                        >
                            <BadgeIcon size={16} style={{ color: badge.color }} />
                            <span className="text-sm font-heading font-semibold" style={{ color: badge.color }}>
                                {badge.label}
                            </span>
                        </div>

                        <h1 className="text-3xl md:text-4xl font-heading font-bold text-surface-900 dark:text-white mb-2">
                            {scorePercent >= 80 ? 'Excellent Work!' : scorePercent >= 50 ? 'Good Effort!' : 'Keep Practicing!'}
                        </h1>
                        <p className="text-surface-500 dark:text-surface-400">
                            You scored {displayScorePercent}% ({resultData.score} out of {resultData.total}) · {formatTime(timeSpentSeconds)}
                        </p>
                    </motion.div>
                </motion.div>

                {/* Stats Grid */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.6 }}
                    className="grid grid-cols-3 gap-4 mb-8"
                >
                    {[
                        { label: 'Correct', value: resultData.score, total: resultData.total, color: '#22C55E' },
                        { label: 'Incorrect', value: resultData.total - resultData.score, total: resultData.total, color: '#EF4444' },
                        { label: 'Time', value: formatTime(timeSpentSeconds), color: '#6C63FF' },
                    ].map((stat, i) => (
                        <Card key={i} className="text-center">
                            <p className="text-2xl font-heading font-bold" style={{ color: stat.color }}>
                                {typeof stat.value === 'number' && stat.total ? `${stat.value}/${stat.total}` : stat.value}
                            </p>
                            <p className="text-xs text-surface-400 mt-1">{stat.label}</p>
                        </Card>
                    ))}
                </motion.div>

                {/* ML Insights */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.65 }}
                    className="mb-8"
                >
                    <Card hover={false} className="relative overflow-hidden">
                        <div className="absolute top-0 left-0 w-2 shrink-0 bg-primary h-full"></div>
                        <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4 ml-2">
                            AdaptiQ Engine Insights 🧠
                        </h3>
                        {mlLoading ? (
                            <div className="flex justify-center items-center h-24 ml-2">
                                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                            </div>
                        ) : mlError ? (
                            <p className="text-red-500 text-sm ml-2">Failed to load AI insights: {mlError}</p>
                        ) : mlData ? (
                            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 ml-2">
                                <div className="bg-surface-50 dark:bg-surface-800 p-4 rounded-xl border border-surface-200 dark:border-white/[0.04]">
                                    <p className="text-xs text-surface-400 mb-1">Recommended Action</p>
                                    <p className="font-heading font-semibold text-primary capitalize">
                                        {mlData.action}
                                    </p>
                                </div>
                                <div className="bg-surface-50 dark:bg-surface-800 p-4 rounded-xl border border-surface-200 dark:border-white/[0.04]">
                                    <p className="text-xs text-surface-400 mb-1">Estimated Skill Gap</p>
                                    <p className={`font-heading font-semibold ${mlData.is_weak ? 'text-red-500' : 'text-green-500'}`}>
                                        {(mlData.skill_gap * 100).toFixed(1)}%
                                    </p>
                                </div>
                                <div className="bg-surface-50 dark:bg-surface-800 p-4 rounded-xl border border-surface-200 dark:border-white/[0.04]">
                                    <p className="text-xs text-surface-400 mb-1">Difficulty Fit</p>
                                    <p className="font-heading font-semibold text-surface-700 dark:text-surface-300 capitalize">
                                        {mlData.difficulty_level}
                                    </p>
                                </div>
                                <div className="bg-surface-50 dark:bg-surface-800 p-4 rounded-xl border border-surface-200 dark:border-white/[0.04]">
                                    <p className="text-xs text-surface-400 mb-1">Next Topic Rank</p>
                                    <p className="font-heading font-semibold text-purple-500">
                                        {(mlData.rank_score * 10).toFixed(1)} / 10
                                    </p>
                                </div>
                            </div>
                        ) : (
                            <p className="text-xs text-surface-400 ml-2">No AI insights generated. Please complete a quiz with telemetry data to see predictions.</p>
                        )}
                    </Card>
                </motion.div>

                {/* Recommendations */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.8 }}
                    className="mb-8"
                >
                    <h3 className="font-heading font-semibold text-surface-900 dark:text-white mb-4">
                        Recommendations based on weak topics
                    </h3>
                    <div className="grid sm:grid-cols-3 gap-4">
                        {recommendations.map((rec, i) => (
                            <Card key={i} className="cursor-pointer" onClick={() => rec.youtubeUrl && window.open(rec.youtubeUrl, '_blank')}>
                                <h4 className="font-heading font-semibold text-sm text-surface-900 dark:text-white mb-1">
                                    {rec.title}
                                </h4>
                                <p className="text-xs text-surface-400 mb-3">{rec.subject || rec.desc}</p>
                                <span className="text-xs font-medium text-primary">
                                    {rec.youtubeUrl ? 'Watch Tutorial →' : `${rec.action || 'View'} →`}
                                </span>
                            </Card>
                        ))}
                    </div>
                </motion.div>

                {/* Actions */}
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.9 }}
                    className="flex flex-col sm:flex-row gap-3 justify-center"
                >
                    <Button
                        variant="secondary"
                        size="lg"
                        onClick={() => navigate(`/quiz-setup?subject=${subject}`)}
                    >
                        <RotateCcw size={18} />
                        Retry Quiz
                    </Button>
                    <Button size="lg" onClick={() => navigate('/dashboard')}>
                        Back to Dashboard
                        <ArrowRight size={18} />
                    </Button>
                </motion.div>
            </div>
        </PageTransition>
    )
}
