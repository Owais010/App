import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '../lib/supabase'
import { fetchProfile } from '../lib/api'

const AuthContext = createContext({})

export const useAuth = () => useContext(AuthContext)

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null)
    const [loading, setLoading] = useState(true)

    const handleUserSession = async (sessionUser, token) => {
        try {
            const profileRes = await fetchProfile(token);
            setUser({
                ...sessionUser,
                userId: sessionUser.id,
                sessionToken: token,
                fullName: profileRes?.profile?.full_name || sessionUser.user_metadata?.full_name || 'Learner',
                profile: profileRes?.profile || null
            })
        } catch (err) {
            console.error("Profile fetch failed", err);
            setUser({
                ...sessionUser,
                userId: sessionUser.id,
                sessionToken: token,
                fullName: sessionUser.user_metadata?.full_name || 'Learner'
            })
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        const initializeAuth = async () => {
            try {
                const { data: { session } } = await supabase.auth.getSession()
                if (session?.user) {
                    await handleUserSession(session.user, session.access_token)
                } else {
                    setUser(null)
                    setLoading(false)
                }
            } catch (err) {
                setUser(null)
                setLoading(false)
            }
        }

        initializeAuth()

        const { data: { subscription } } = supabase.auth.onAuthStateChange(async (_event, session) => {
            if (session?.user) {
                await handleUserSession(session.user, session.access_token)
            } else {
                setUser(null)
                setLoading(false)
            }
        })

        return () => subscription.unsubscribe()
    }, [])

    const signUp = async (email, password) => {
        const { data, error } = await supabase.auth.signUp({ email, password })
        if (error) throw error
        return data
    }

    const signIn = async (email, password) => {
        const { data, error } = await supabase.auth.signInWithPassword({ email, password })
        if (error) throw error
        setUser(data.user)
        return data
    }

    const signInWithGoogle = async () => {
        const { data, error } = await supabase.auth.signInWithOAuth({ provider: 'google' })
        if (error) throw error
        return data
    }

    const signOut = async () => {
        const { error } = await supabase.auth.signOut()
        if (error) throw error
    }

    const value = { user, loading, signUp, signIn, signInWithGoogle, signOut }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
