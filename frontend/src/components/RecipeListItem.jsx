import React from 'react';

/**
 * Recipe table row component with warm editorial styling
 */
function RecipeListItem({ recipe, onEdit, onDelete }) {
  const likeDisplay = recipe.like_score != null
    ? `${recipe.like_score} / 5`
    : '—';

  return (
    <div className="recipe-table-row">
      <div className="recipe-name">
        <strong>{recipe.name}</strong>
        <div className="recipe-categories">
          {recipe.categories && recipe.categories.map((cat) => (
            <span key={cat.id} className="category-tag">
              {cat.name}
            </span>
          ))}
        </div>
      </div>

      <div>{likeDisplay}</div>
      <div>{recipe.effort_score} / 5</div>
      <div>{recipe.prep_time_minutes + recipe.cook_time_minutes} min</div>
      <div>{recipe.cleanup_effort}</div>

      <div className="recipe-actions">
        <button className="btn-edit" onClick={() => onEdit(recipe)}>
          Edit
        </button>
        <button className="btn-danger" onClick={() => onDelete(recipe)}>
          Delete
        </button>
      </div>
    </div>
  );
}

export default RecipeListItem;
