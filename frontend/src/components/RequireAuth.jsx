import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

/**
 * Route guard: renders children only if the user is authenticated.
 * Shows a loading spinner while auth state is being initialised (prevents
 * flashing the login page on refresh when the user actually has a valid session).
 */
export default function RequireAuth() {
    const { user, authLoading } = useAuth();

    if (authLoading) {
        return (
            <div className="loading">
                <div className="loading-dots">
                    <span /><span /><span />
                </div>
                <div className="loading-text">Loading…</div>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    return <Outlet />;
}
