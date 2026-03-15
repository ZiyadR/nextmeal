import React, { useState, useEffect, useCallback } from 'react';
import { getRecipes, searchRecipes, deleteRecipe as deleteRecipeAPI, getCategories, exportRecipes } from '../api/client';
import SearchBar from '../components/SearchBar';
import FilterBar from '../components/FilterBar';
import RecipeListItem from '../components/RecipeListItem';
import RecipeForm from '../components/RecipeForm';
import DeleteConfirmModal from '../components/DeleteConfirmModal';
import ImportCSVModal from '../components/ImportCSVModal';

/**
 * Main recipe management page
 */
function ManageRecipes() {
  const [recipes, setRecipes] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters and search
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategoryId, setSelectedCategoryId] = useState(null);
  const [page, setPage] = useState(1);
  const [totalRecipes, setTotalRecipes] = useState(0);
  const limit = 50;

  // Modals
  const [showRecipeForm, setShowRecipeForm] = useState(false);
  const [editingRecipe, setEditingRecipe] = useState(null);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deletingRecipe, setDeletingRecipe] = useState(null);
  const [showImportModal, setShowImportModal] = useState(false);

  useEffect(() => {
    loadCategories();
  }, []);

  useEffect(() => {
    loadRecipes();
  }, [page, selectedCategoryId]);

  const loadCategories = async () => {
    try {
      const cats = await getCategories();
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const loadRecipes = async () => {
    setLoading(true);
    setError(null);

    try {
      let data;
      if (searchQuery.trim()) {
        // Search mode
        data = await searchRecipes(searchQuery, page, limit);
        // Search doesn't return pagination info, so approximate
        setRecipes(data);
        setTotalRecipes(data.length);
      } else {
        // Normal list mode
        data = await getRecipes(page, limit, selectedCategoryId);
        setRecipes(data.recipes);
        setTotalRecipes(data.total);
      }
    } catch (err) {
      setError('Failed to load recipes: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = useCallback((query) => {
    setSearchQuery(query);
    setPage(1);
    // Trigger reload on next render
    setTimeout(() => loadRecipes(), 0);
  }, []);

  const handleCategoryChange = (categoryId) => {
    setSelectedCategoryId(categoryId);
    setPage(1);
  };

  const handleCreateNew = () => {
    setEditingRecipe(null);
    setShowRecipeForm(true);
  };

  const handleEdit = (recipe) => {
    setEditingRecipe(recipe);
    setShowRecipeForm(true);
  };

  const handleDeleteClick = (recipe) => {
    setDeletingRecipe(recipe);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (!deletingRecipe) return;

    try {
      await deleteRecipeAPI(deletingRecipe.id);
      setShowDeleteConfirm(false);
      setDeletingRecipe(null);
      loadRecipes();
    } catch (err) {
      setError('Failed to delete recipe: ' + err.message);
    }
  };

  const handleFormSuccess = () => {
    setShowRecipeForm(false);
    setEditingRecipe(null);
    loadRecipes();
  };

  const handleImportSuccess = () => {
    setShowImportModal(false);
    loadRecipes();
  };

  const handleExport = async () => {
    try {
      await exportRecipes(selectedCategoryId);
    } catch (err) {
      setError('Failed to export recipes: ' + err.message);
    }
  };

  const totalPages = Math.ceil(totalRecipes / limit);

  return (
    <div className="manage-recipes">
      <div className="manage-header">
        <h2>Manage Recipes</h2>
        <div className="manage-actions">
          <button className="btn-primary" onClick={handleCreateNew}>
            Create Recipe
          </button>
          <button className="btn-secondary" onClick={() => setShowImportModal(true)}>
            Import CSV
          </button>
          <button className="btn-secondary" onClick={handleExport}>
            Export CSV
          </button>
        </div>
      </div>

      <div className="search-filter-bar">
        <SearchBar onSearch={handleSearch} />
        <FilterBar
          categories={categories}
          selectedCategoryId={selectedCategoryId}
          onCategoryChange={handleCategoryChange}
        />
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading recipes...</div>
      ) : recipes.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">🍽️</div>
          <div className="empty-state-text">
            {searchQuery
              ? 'No recipes found matching your search'
              : 'No recipes yet'}
          </div>
          <button className="btn-primary" onClick={handleCreateNew}>
            Create Your First Recipe
          </button>
        </div>
      ) : (
        <>
          <div className="recipe-table">
            <div className="recipe-table-header">
              <div>Name</div>
              <div>Like</div>
              <div>Effort</div>
              <div>Total Time</div>
              <div>Cleanup</div>
              <div>Actions</div>
            </div>
            {recipes.map((recipe) => (
              <RecipeListItem
                key={recipe.id}
                recipe={recipe}
                onEdit={handleEdit}
                onDelete={handleDeleteClick}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className="pagination">
              <button
                onClick={() => setPage(page - 1)}
                disabled={page === 1}
              >
                Previous
              </button>
              <span className="page-info">
                Page {page} of {totalPages}
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= totalPages}
              >
                Next
              </button>
            </div>
          )}
        </>
      )}

      {showRecipeForm && (
        <RecipeForm
          recipe={editingRecipe}
          onClose={() => setShowRecipeForm(false)}
          onSuccess={handleFormSuccess}
        />
      )}

      {showDeleteConfirm && deletingRecipe && (
        <DeleteConfirmModal
          recipe={deletingRecipe}
          onConfirm={handleDeleteConfirm}
          onCancel={() => setShowDeleteConfirm(false)}
        />
      )}

      {showImportModal && (
        <ImportCSVModal
          onClose={() => setShowImportModal(false)}
          onSuccess={handleImportSuccess}
        />
      )}
    </div>
  );
}

export default ManageRecipes;
