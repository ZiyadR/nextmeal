/**
 * API client for communicating with NextMeal backend
 */

const API_BASE = '/api';

/**
 * Get a meal recommendation
 * @returns {Promise<Object>} Recommendation response
 */
export async function getRecommendation() {
  const response = await fetch(`${API_BASE}/recommendation?_t=${Date.now()}`);
  if (!response.ok) {
    throw new Error('Failed to get recommendation');
  }
  return response.json();
}

/**
 * Accept the current recommendation
 * @param {number} recipeId - Recipe ID to accept
 * @param {string} mealType - Type of meal (default: 'dinner')
 * @returns {Promise<Object>} Accept response with next recommendation
 */
export async function acceptMeal(recipeId, mealType = 'dinner') {
  const response = await fetch(`${API_BASE}/recommendation/accept`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      recipe_id: recipeId,
      meal_type: mealType,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to accept meal');
  }
  return response.json();
}

/**
 * Skip the current recommendation
 * @param {number} recipeId - Recipe ID to skip
 * @param {string|null} reason - Optional skip reason ('too_much_effort' or 'dont_like')
 * @returns {Promise<Object>} Skip response with next suggestion
 */
export async function skipMeal(recipeId, reason = null) {
  const response = await fetch(`${API_BASE}/recommendation/skip`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      recipe_id: recipeId,
      reason: reason,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to skip meal');
  }
  return response.json();
}

/**
 * Get another meal suggestion, excluding specified recipes
 * @param {number[]} excludedIds - Array of recipe IDs to exclude
 * @returns {Promise<Object>} Another recommendation
 */
export async function getAnotherMeal(excludedIds = []) {
  const response = await fetch(`${API_BASE}/recommendation/another`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      excluded_recipe_ids: excludedIds,
    }),
  });

  if (!response.ok) {
    throw new Error('Failed to get another recommendation');
  }
  return response.json();
}

/**
 * Get meal history
 * @param {number} limit - Number of entries to fetch
 * @returns {Promise<Object[]>} Meal history
 */
export async function getMealHistory(limit = 50) {
  const response = await fetch(`${API_BASE}/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error('Failed to get meal history');
  }
  return response.json();
}

/**
 * Get cooking statistics
 * @returns {Promise<Object>} Cooking stats
 */
export async function getCookingStats() {
  const response = await fetch(`${API_BASE}/history/stats`);
  if (!response.ok) {
    throw new Error('Failed to get cooking stats');
  }
  return response.json();
}

/**
 * Manually add a meal history entry
 * @param {Object} mealData - Meal data (date, recipe_id, meal_type, cooked)
 * @returns {Promise<Object>} Created meal history entry
 */
export async function addMealHistory(mealData) {
  const response = await fetch(`${API_BASE}/history`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(mealData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to add meal history');
  }
  return response.json();
}

/**
 * Get all recipes with pagination and filtering
 * @param {number} page - Page number
 * @param {number} limit - Items per page
 * @param {number|null} categoryId - Optional category filter
 * @returns {Promise<Object>} Paginated recipes
 */
export async function getRecipes(page = 1, limit = 50, categoryId = null) {
  let url = `${API_BASE}/recipes?page=${page}&limit=${limit}`;
  if (categoryId) {
    url += `&category_id=${categoryId}`;
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to get recipes');
  }
  return response.json();
}

/**
 * Get a single recipe by ID
 * @param {number} recipeId - Recipe ID
 * @returns {Promise<Object>} Recipe details
 */
export async function getRecipe(recipeId) {
  const response = await fetch(`${API_BASE}/recipes/${recipeId}`);
  if (!response.ok) {
    throw new Error('Failed to get recipe');
  }
  return response.json();
}

/**
 * Create a new recipe
 * @param {Object} recipeData - Recipe data
 * @returns {Promise<Object>} Created recipe
 */
export async function createRecipe(recipeData) {
  const response = await fetch(`${API_BASE}/recipes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(recipeData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create recipe');
  }
  return response.json();
}

/**
 * Update an existing recipe
 * @param {number} recipeId - Recipe ID
 * @param {Object} recipeData - Recipe data to update
 * @returns {Promise<Object>} Updated recipe
 */
export async function updateRecipe(recipeId, recipeData) {
  const response = await fetch(`${API_BASE}/recipes/${recipeId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(recipeData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update recipe');
  }
  return response.json();
}

/**
 * Delete a recipe
 * @param {number} recipeId - Recipe ID
 * @returns {Promise<Object>} Delete result
 */
export async function deleteRecipe(recipeId) {
  const response = await fetch(`${API_BASE}/recipes/${recipeId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete recipe');
  }
  return response.json();
}

/**
 * Search recipes by name
 * @param {string} query - Search query
 * @param {number} page - Page number
 * @param {number} limit - Items per page
 * @returns {Promise<Object[]>} Matching recipes
 */
export async function searchRecipes(query, page = 1, limit = 50) {
  const response = await fetch(
    `${API_BASE}/recipes/search/${encodeURIComponent(query)}?page=${page}&limit=${limit}`
  );
  if (!response.ok) {
    throw new Error('Failed to search recipes');
  }
  return response.json();
}

/**
 * Get all categories
 * @returns {Promise<Object[]>} Categories
 */
export async function getCategories() {
  const response = await fetch(`${API_BASE}/categories`);
  if (!response.ok) {
    throw new Error('Failed to get categories');
  }
  return response.json();
}

/**
 * Create a new category
 * @param {string} name - Category name
 * @returns {Promise<Object>} Created category
 */
export async function createCategory(name) {
  const response = await fetch(`${API_BASE}/categories`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create category');
  }
  return response.json();
}

/**
 * Import recipes from CSV file
 * @param {File} file - CSV file
 * @param {boolean} updateExisting - Update existing recipes
 * @returns {Promise<Object>} Import result
 */
export async function importRecipes(file, updateExisting = true) {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(
    `${API_BASE}/recipes/import?update_existing=${updateExisting}`,
    {
      method: 'POST',
      body: formData,
    }
  );

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to import recipes');
  }
  return response.json();
}

/**
 * Export recipes to CSV
 * @param {number|null} categoryId - Optional category filter
 */
export async function exportRecipes(categoryId = null) {
  let url = `${API_BASE}/recipes/export`;
  if (categoryId) {
    url += `?category_id=${categoryId}`;
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to export recipes');
  }

  // Trigger download
  const blob = await response.blob();
  const downloadUrl = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = downloadUrl;
  a.download = 'recipes.csv';
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(downloadUrl);
}

/**
 * Get planned meals for the next 7 days
 * @returns {Promise<Object[]>} Planned meals
 */
export async function getPlannedMeals() {
  const response = await fetch(`${API_BASE}/history/planned?_t=${Date.now()}`);
  if (!response.ok) {
    throw new Error('Failed to get planned meals');
  }
  return response.json();
}

/**
 * Delete a planned meal
 * @param {number} mealId - Meal history ID to delete
 * @returns {Promise<Object>} Delete result
 */
export async function deletePlannedMeal(mealId) {
  const response = await fetch(`${API_BASE}/history/${mealId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to delete planned meal');
  }
  return response.json();
}
