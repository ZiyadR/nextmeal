import React, { useState, useEffect } from 'react';
import { getRecipes } from '../api/client';

/**
 * Modal for manually adding a past meal to history
 */
function AddMealHistoryModal({ onClose, onAdd }) {
  const [formData, setFormData] = useState({
    recipe_id: '',
    date: new Date().toISOString().split('T')[0], // Today's date in YYYY-MM-DD format
    meal_type: 'dinner',
    cooked: true,
  });
  const [recipes, setRecipes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    loadRecipes();
  }, []);

  const loadRecipes = async () => {
    try {
      const data = await getRecipes(1, 100); // Load up to 100 recipes (API limit)
      setRecipes(data.recipes);
    } catch (err) {
      setError('Failed to load recipes');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      // Convert recipe_id to integer or null
      const mealData = {
        ...formData,
        recipe_id: formData.recipe_id ? parseInt(formData.recipe_id) : null,
      };

      await onAdd(mealData);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content form-modal" onClick={(e) => e.stopPropagation()}>
        <h3>Add Past Meal</h3>
        <p className="modal-subtitle">Log a meal you forgot to record</p>

        {error && <div className="error-message">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="recipe_id">Recipe</label>
            <select
              id="recipe_id"
              name="recipe_id"
              value={formData.recipe_id}
              onChange={handleChange}
              required
              disabled={loading}
            >
              <option value="">Select a recipe</option>
              {recipes.map((recipe) => (
                <option key={recipe.id} value={recipe.id}>
                  {recipe.name}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="date">Date</label>
            <input
              type="date"
              id="date"
              name="date"
              value={formData.date}
              onChange={handleChange}
              max={new Date().toISOString().split('T')[0]} // Can't add future meals
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="meal_type">Meal Type</label>
            <select
              id="meal_type"
              name="meal_type"
              value={formData.meal_type}
              onChange={handleChange}
              required
            >
              <option value="breakfast">Breakfast</option>
              <option value="lunch">Lunch</option>
              <option value="dinner">Dinner</option>
              <option value="snack">Snack</option>
            </select>
          </div>

          <div className="form-group checkbox-group">
            <label>
              <input
                type="checkbox"
                name="cooked"
                checked={formData.cooked}
                onChange={handleChange}
              />
              <span>I actually cooked this meal</span>
            </label>
          </div>

          <div className="modal-buttons">
            <button
              type="submit"
              className="modal-button primary-button"
              disabled={submitting || loading}
            >
              {submitting ? 'Adding...' : 'Add Meal'}
            </button>
            <button
              type="button"
              className="modal-button cancel-button"
              onClick={onClose}
              disabled={submitting}
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default AddMealHistoryModal;
