import React from 'react';

/**
 * Card displaying meal recommendation with editorial layout
 */
function RecommendationCard({ recommendation, headerLabel }) {
  if (!recommendation) {
    return null;
  }

  const { recipe, explanation } = recommendation;
  const totalTime = recipe.prep_time_minutes + recipe.cook_time_minutes;

  const effortLabels = {
    1: 'Very Easy',
    2: 'Easy',
    3: 'Moderate',
    4: 'Takes Effort',
    5: 'Challenging',
  };

  const effortEmoji = {
    1: '🌿',
    2: '🌿',
    3: '🍳',
    4: '🔥',
    5: '🔥',
  };

  return (
    <div className="recommendation-card">
      <div className="card-eyebrow">{headerLabel || 'Tonight\u2019s suggestion'}</div>

      <h1 className="recipe-name">{recipe.name}</h1>

      {explanation && (
        <p className="explanation">{explanation}</p>
      )}

      {/* Quick-stats pill row */}
      <div className="recipe-stats">
        <span className="stat-pill">
          <span className="stat-icon" role="img" aria-label="Total time">⏱</span>
          {totalTime} min
        </span>
        <span className="stat-pill">
          <span className="stat-icon" role="img" aria-label="Effort level">{effortEmoji[recipe.effort_score]}</span>
          {effortLabels[recipe.effort_score]}
        </span>
        <span className="stat-pill">
          <span className="stat-icon" role="img" aria-label="Cleanup effort">🧹</span>
          {recipe.cleanup_effort} cleanup
        </span>
      </div>

      {/* Detail rows */}
      <div className="recipe-details">
        {recipe.prep_time_minutes > 0 && (
          <div className="detail-item">
            <span className="detail-label">Prep + Cook</span>
            <span className="detail-value">
              {recipe.prep_time_minutes} min prep
              <span className="detail-subtext"> + {recipe.cook_time_minutes} min cook</span>
            </span>
          </div>
        )}

        {recipe.categories && recipe.categories.length > 0 && (
          <div className="detail-item categories">
            <span className="detail-label">Tags</span>
            <div className="category-tags">
              {recipe.categories.map((cat) => (
                <span key={cat.id} className="category-tag">
                  {cat.name}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default RecommendationCard;
