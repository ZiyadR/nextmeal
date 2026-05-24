/**
 * API client for communicating with the NextMeal backend.
 *
 * Auth strategy:
 *  - Access token is stored in-memory (see AuthContext.jsx)
 *  - Refresh token is stored in an httpOnly cookie managed by the browser
 *  - On 401 we attempt a single token refresh, then retry the original request
 *  - On a second 401 we redirect to /login
 */

import { getAccessToken, setAccessToken } from '../contexts/AuthContext';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

let _isRefreshing = false;
let _refreshQueue = []; // Pending requests waiting for the refresh to finish

function _processQueue(error, token = null) {
  _refreshQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  _refreshQueue = [];
}

/**
 * Fetch wrapper that:
 *  1. Adds Authorization: Bearer header
 *  2. Retries once after refreshing the token on 401
 *  3. Redirects to /login if the refresh also fails
 */
async function apiFetch(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };
  const token = getAccessToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(url, { ...options, headers, credentials: 'include' });

  if (res.status !== 401) return res;

  // --- 401 handling: attempt refresh ---
  if (_isRefreshing) {
    // Another request already kicked off a refresh — wait for it
    return new Promise((resolve, reject) => {
      _refreshQueue.push({
        resolve: (newToken) => {
          headers['Authorization'] = `Bearer ${newToken}`;
          resolve(fetch(url, { ...options, headers, credentials: 'include' }));
        },
        reject,
      });
    });
  }

  _isRefreshing = true;
  try {
    const refreshRes = await fetch('/auth/refresh', { method: 'POST', credentials: 'include' });
    if (!refreshRes.ok) throw new Error('Refresh failed');

    const data = await refreshRes.json();
    setAccessToken(data.access_token);
    _processQueue(null, data.access_token);

    // Retry the original request with the new token
    headers['Authorization'] = `Bearer ${data.access_token}`;
    return fetch(url, { ...options, headers, credentials: 'include' });
  } catch (err) {
    _processQueue(err);
    setAccessToken(null);
    window.location.href = '/login';
    throw err;
  } finally {
    _isRefreshing = false;
  }
}

async function apiJSON(url, options = {}) {
  const res = await apiFetch(url, options);
  if (!res.ok) {
    let msg = `Request failed: ${res.status}`;
    try {
      const body = await res.json();
      msg = body.detail || body.error?.message || msg;
    } catch { /* body not JSON */ }
    throw new Error(msg);
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Auth helpers (used by AuthContext — don't need the interceptor)
// -------------------------------------------------------------------------

export async function apiLogin(email, password) {
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
  return res.json();
}

// -------------------------------------------------------------------------
// Recommendations
// -------------------------------------------------------------------------

export async function getRecommendation() {
  return apiJSON(`${API_BASE}/recommendation?_t=${Date.now()}`);
}

export async function acceptMeal(recipeId, mealType = 'dinner') {
  return apiJSON(`${API_BASE}/recommendation/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId, meal_type: mealType }),
  });
}

export async function skipMeal(recipeId, reason = null) {
  return apiJSON(`${API_BASE}/recommendation/skip`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recipe_id: recipeId, reason }),
  });
}

export async function getAnotherMeal(excludedIds = []) {
  return apiJSON(`${API_BASE}/recommendation/another`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ excluded_recipe_ids: excludedIds }),
  });
}

// -------------------------------------------------------------------------
// Meal history
// -------------------------------------------------------------------------

export async function getMealHistory(limit = 50) {
  return apiJSON(`${API_BASE}/history?limit=${limit}`);
}

export async function getCookingStats() {
  return apiJSON(`${API_BASE}/history/stats`);
}

export async function addMealHistory(mealData) {
  return apiJSON(`${API_BASE}/history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mealData),
  });
}

export async function getPlannedMeals() {
  return apiJSON(`${API_BASE}/history/planned?_t=${Date.now()}`);
}

export async function deletePlannedMeal(mealId) {
  return apiJSON(`${API_BASE}/history/${mealId}`, { method: 'DELETE' });
}

// -------------------------------------------------------------------------
// Recipes
// -------------------------------------------------------------------------

export async function getRecipes(page = 1, limit = 50, categoryId = null) {
  let url = `${API_BASE}/recipes?page=${page}&limit=${limit}`;
  if (categoryId) url += `&category_id=${categoryId}`;
  return apiJSON(url);
}

export async function getRecipe(recipeId) {
  return apiJSON(`${API_BASE}/recipes/${recipeId}`);
}

export async function createRecipe(recipeData) {
  return apiJSON(`${API_BASE}/recipes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(recipeData),
  });
}

export async function updateRecipe(recipeId, recipeData) {
  return apiJSON(`${API_BASE}/recipes/${recipeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(recipeData),
  });
}

export async function deleteRecipe(recipeId) {
  return apiJSON(`${API_BASE}/recipes/${recipeId}`, { method: 'DELETE' });
}

export async function searchRecipes(query, page = 1, limit = 50) {
  return apiJSON(
    `${API_BASE}/recipes/search/${encodeURIComponent(query)}?page=${page}&limit=${limit}`
  );
}

export async function importRecipes(file, updateExisting = true) {
  const formData = new FormData();
  formData.append('file', file);
  return apiJSON(`${API_BASE}/recipes/import?update_existing=${updateExisting}`, {
    method: 'POST',
    body: formData,
  });
}

export async function exportRecipes(categoryId = null) {
  let url = `${API_BASE}/recipes/export`;
  if (categoryId) url += `?category_id=${categoryId}`;
  const res = await apiFetch(url);
  if (!res.ok) throw new Error('Failed to export recipes');
  const blob = await res.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = 'recipes.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

// -------------------------------------------------------------------------
// Categories
// -------------------------------------------------------------------------

export async function getCategories() {
  return apiJSON(`${API_BASE}/categories`);
}

export async function createCategory(name) {
  return apiJSON(`${API_BASE}/categories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
}
