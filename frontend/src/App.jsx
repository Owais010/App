import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
// import { AnimatePresence } from 'framer-motion'
import { AuthProvider } from './context/AuthContext'
import { ThemeProvider } from './context/ThemeContext'
import { ToastProvider } from './components/Toast'
import ProtectedRoute from './components/ProtectedRoute'
import AdminRoute from './components/AdminRoute'
import Landing from './pages/Landing'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import QuizSetup from './pages/QuizSetup'
import Quiz from './pages/Quiz'
import Results from './pages/Results'
import Achievements from './pages/Achievements'
import ForgotPassword from './pages/ForgotPassword'
import ResetPassword from './pages/ResetPassword'

// Admin Panel
import AdminLayout from './components/admin/AdminLayout'
import AdminDashboard from './pages/admin/AdminDashboard'
import UserManagement from './pages/admin/UserManagement'
import QuestionBankManager from './pages/admin/QuestionBankManager'
import LearningResourcesManager from './pages/admin/LearningResourcesManager'

import { useEffect } from 'react'

function ScrollToTop() {
    const { pathname } = useLocation()
    useEffect(() => {
        window.scrollTo(0, 0)
    }, [pathname])
    return null
}

function AnimatedRoutes() {
    const location = useLocation()

    return (
        <>
            <Routes location={location} key={location.pathname}>
                <Route path="/" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />

                {/* Admin Routes grouped under /admin using nested routing */}
                <Route
                    path="/admin"
                    element={
                        <AdminRoute>
                            <AdminLayout />
                        </AdminRoute>
                    }
                >
                    <Route index element={<AdminDashboard />} />
                    <Route path="users" element={<UserManagement />} />
                    <Route path="questions" element={<QuestionBankManager />} />
                    <Route path="resources" element={<LearningResourcesManager />} />
                </Route>

                <Route
                    path="/dashboard"
                    element={
                        <ProtectedRoute>
                            <Dashboard />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/quiz-setup"
                    element={
                        <ProtectedRoute>
                            <QuizSetup />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/quiz"
                    element={
                        <ProtectedRoute>
                            <Quiz />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/results"
                    element={
                        <ProtectedRoute>
                            <Results />
                        </ProtectedRoute>
                    }
                />
                <Route
                    path="/achievements"
                    element={
                        <ProtectedRoute>
                            <Achievements />
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </>
    )
}

export default function App() {
    return (
        <BrowserRouter>
            <ThemeProvider>
                <AuthProvider>
                    <ToastProvider>
                        <ScrollToTop />
                        <AnimatedRoutes />
                    </ToastProvider>
                </AuthProvider>
            </ThemeProvider>
        </BrowserRouter>
    )
}
