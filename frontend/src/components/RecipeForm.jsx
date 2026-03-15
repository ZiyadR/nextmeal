import React, { useState, useEffect } from 'react';
import { createRecipe, updateRecipe, getCategories, createCategory } from '../api/client';

/**
 * Recipe create/edit form modal
 */
function RecipeForm({ recipe, onClose, onSuccess }) {
  const isEdit = !!recipe;

  const [formData, setFormData] = useState({
    name: recipe?.name || '',
    like_score: recipe?.like_score || null,
    effort_score: recipe?.effort_score || 3,
    prep_time_minutes: recipe?.prep_time_minutes || 0,
    cook_time_minutes: recipe?.cook_time_minutes || 0,
    cleanup_effort: recipe?.cleanup_effort || 'medium',
    category_ids: recipe?.categories?.map(c => c.id) || [],
  });

  const [categories, setCategories] = useState([]);
  const [newCategoryName, setNewCategoryName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadCategories();
  }, []);

  const loadCategories = async () => {
    try {
      const cats = await getCategories();
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handleChange = (field, value) => {
    setFormData({ ...formData, [field]: value });
  };

  const toggleCategory = (categoryId) => {
    const newCategoryIds = formData.category_ids.includes(categoryId)
      ? formData.category_ids.filter(id => id !== categoryId)
      : [...formData.category_ids, categoryId];
    handleChange('category_ids', newCategoryIds);
  };

  const handleAddCategory = async () => {
    if (!newCategoryName.trim()) return;

    try {
      const newCat = await createCategory(newCategoryName.trim());
      setCategories([...categories, newCat]);
      handleChange('category_ids', [...formData.category_ids, newCat.id]);
      setNewCategoryName('');
    } catch (err) {
      setError('Failed to create category: ' + err.message);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    // Validation
    if (!formData.name.trim()) {
      setError('Recipe name is required');
      setLoading(false);
      return;
    }

    if (!formData.effort_score || formData.effort_score < 1 || formData.effort_score > 5) {
      setError('Effort score must be between 1 and 5');
      setLoading(false);
      return;
    }

    try {
      const data = {
        ...formData,
        like_score: formData.like_score || null,
      };

      if (isEdit) {
        await updateRecipe(recipe.id, data);
      } else {
        await createRecipe(data);
      }

      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content modal-large">
        <h3>{isEdit ? 'Edit Recipe' : 'Create New Recipe'}</h3>

        <form className="recipe-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label className="form-label">Name *</label>
            <input
              type="text"
              className="form-input"
              value={formData.name}
              onChange={(e) => handleChange('name', e.target.value)}
              required
            />
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Like Score (1-5)</label>
              <input
                type="number"
                className="form-input"
                value={formData.like_score || ''}
                onChange={(e) => handleChange('like_score', e.target.value ? parseInt(e.target.value) : null)}
                min="1"
                max="5"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Effort Score (1-5) *</label>
              <input
                type="number"
                className="form-input"
                value={formData.effort_score}
                onChange={(e) => handleChange('effort_score', parseInt(e.target.value))}
                min="1"
                max="5"
                required
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Prep Time (minutes)</label>
              <input
                type="number"
                className="form-input"
                value={formData.prep_time_minutes}
                onChange={(e) => handleChange('prep_time_minutes', parseInt(e.target.value) || 0)}
                min="0"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Cook Time (minutes)</label>
              <input
                type="number"
                className="form-input"
                value={formData.cook_time_minutes}
                onChange={(e) => handleChange('cook_time_minutes', parseInt(e.target.value) || 0)}
                min="0"
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Cleanup Effort</label>
            <select
              className="form-input"
              value={formData.cleanup_effort}
              onChange={(e) => handleChange('cleanup_effort', e.target.value)}
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Categories</label>
            <div className="category-multiselect">
              {categories.map((cat) => (
                <span
                  key={cat.id}
                  className={`category-option ${formData.category_ids.includes(cat.id) ? 'selected' : ''}`}
                  onClick={() => toggleCategory(cat.id)}
                >
                  {cat.name}
                </span>
              ))}
            </div>
            <div className="add-category">
              <input
                type="text"
                className="form-input-inline"
                placeholder="Add new category..."
                value={newCategoryName}
                onChange={(e) => setNewCategoryName(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), handleAddCategory())}
              />
              <button
                type="button"
                className="btn-add-category"
                onClick={handleAddCategory}
              >
                Add
              </button>
            </div>
          </div>

          {error && <div className="error-message">{error}</div>}

          <div className="modal-actions">
            <button
              type="button"
              className="btn-secondary"
              onClick={onClose}
              disabled={loading}
            >
              Cancel
            </button>
            <button type="submit" className="btn-primary" disabled={loading}>
              {loading ? 'Saving...' : isEdit ? 'Update Recipe' : 'Create Recipe'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default RecipeForm;
