import React, { createContext, useContext, useState, useRef, useEffect, useCallback } from 'react';

const AuthContext = createContext(null);

/**
 * In-memory access token — NOT stored in localStorage.
 * This ref lives outside component state so it's accessible inside closures
 * without triggering re-renders on every write.
 */
let _accessToken = null;

export function getAccessToken() {
    return _accessToken;
}

export function setAccessToken(token) {
    _accessToken = token;
}

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [authLoading, setAuthLoading] = useState(true);

    /**
     * Attempt to restore the session on mount by exchanging the httpOnly
     * refresh cookie for a new access token.
     */
    useEffect(() => {
        (async () => {
            try {
                const res = await fetch('/auth/refresh', { method: 'POST', credentials: 'include' });
                if (res.ok) {
                    const data = await res.json();
                    setAccessToken(data.access_token);
                    // Decode user info from the token payload (just the ID — we don't need more)
                    const payload = _decodePayload(data.access_token);
                    setUser({ id: payload.sub });
                }
            } catch {
                // No valid refresh cookie — remain logged out
            } finally {
                setAuthLoading(false);
            }
        })();
    }, []);

    const login = useCallback(async (email, password) => {
        const res = await fetch('/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ email, password }),
        });
        if (!res.ok) {
            const body = await res.json().catch(() => ({}));
            throw new Error(body.detail || 'Login failed');
        }
        const data = await res.json();
        setAccessToken(data.access_token);
        const payload = _decodePayload(data.access_token);
        setUser({ id: payload.sub, email });
    }, []);

    const logout = useCallback(async () => {
        try {
            await fetch('/auth/logout', { method: 'POST', credentials: 'include' });
        } catch {
            // Ignore network errors on logout — we clear state regardless
        }
        setAccessToken(null);
        setUser(null);
    }, []);

    /**
     * Refresh the access token using the httpOnly cookie.
     * Called automatically by the API client on 401 responses.
     */
    const refreshToken = useCallback(async () => {
        const res = await fetch('/auth/refresh', { method: 'POST', credentials: 'include' });
        if (!res.ok) {
            setAccessToken(null);
            setUser(null);
            throw new Error('Session expired — please log in again');
        }
        const data = await res.json();
        setAccessToken(data.access_token);
        return data.access_token;
    }, []);

    return (
        <AuthContext.Provider value={{ user, authLoading, login, logout, refreshToken }}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
    return ctx;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function _decodePayload(token) {
    try {
        return JSON.parse(atob(token.split('.')[1]));
    } catch {
        return {};
    }
}
