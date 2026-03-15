import React, { useState, useEffect } from 'react';
import { getMealHistory, addMealHistory, getRecipes } from '../api/client';
import AddMealHistoryModal from '../components/AddMealHistoryModal';

/**
 * Meal history page - view and manually add past meals
 */
function MealHistory() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getMealHistory(100);
      setHistory(data);
    } catch (err) {
      setError('Failed to load meal history: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleAddMeal = async (mealData) => {
    try {
      await addMealHistory(mealData);
      setShowAddModal(false);
      loadHistory();
    } catch (err) {
      throw new Error('Failed to add meal: ' + err.message);
    }
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatMealType = (type) => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  // Group history by date
  const groupedHistory = history.reduce((groups, meal) => {
    const dateKey = meal.date;
    if (!groups[dateKey]) {
      groups[dateKey] = [];
    }
    groups[dateKey].push(meal);
    return groups;
  }, {});

  const sortedDates = Object.keys(groupedHistory).sort((a, b) => b.localeCompare(a));

  return (
    <div className="meal-history">
      <div className="manage-header">
        <h2>Meal History</h2>
        <button className="btn-primary" onClick={() => setShowAddModal(true)}>
          Add Past Meal
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      {loading ? (
        <div className="loading">Loading meal history...</div>
      ) : history.length === 0 ? (
        <div className="empty-state">
          <div className="empty-state-icon">📅</div>
          <div className="empty-state-text">No meal history yet</div>
          <p>Start by accepting recommendations or add past meals manually</p>
          <button className="btn-primary" onClick={() => setShowAddModal(true)}>
            Add Your First Meal
          </button>
        </div>
      ) : (
        <div className="history-list">
          {sortedDates.map((dateKey) => (
            <div key={dateKey} className="history-date-group">
              <div className="history-date-header">{formatDate(dateKey)}</div>
              <div className="history-meals">
                {groupedHistory[dateKey].map((meal) => (
                  <div key={meal.id} className="history-meal-item">
                    <div className="meal-type-badge">{formatMealType(meal.meal_type)}</div>
                    <div className="meal-name">
                      {meal.recipe ? meal.recipe.name : 'Unknown Recipe'}
                    </div>
                    <div className="meal-status">
                      {meal.cooked ? (
                        <span className="status-cooked">Cooked</span>
                      ) : (
                        <span className="status-planned">Planned</span>
                      )}
                    </div>
                    {meal.recipe && (
                      <div className="meal-details">
                        {meal.recipe.effort_score && (
                          <span className="detail-badge">Effort: {meal.recipe.effort_score}/5</span>
                        )}
                        {meal.recipe.categories && meal.recipe.categories.length > 0 && (
                          <span className="detail-badge">
                            {meal.recipe.categories.map((c) => c.name).join(', ')}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {showAddModal && (
        <AddMealHistoryModal
          onClose={() => setShowAddModal(false)}
          onAdd={handleAddMeal}
        />
      )}
    </div>
  );
}

export default MealHistory;
