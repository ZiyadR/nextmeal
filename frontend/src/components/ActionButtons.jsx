import React from 'react';

/**
 * Three-action buttons for the recommendation view.
 * Hierarchy: Accept (terracotta primary) → Another (sage outline) → Skip (ghost)
 * Plus a subtle "Pick a meal" link for manual selection.
 * If onAdvance is provided, shows a "Plan next day →" link to move forward.
 */
function ActionButtons({ onAccept, onAnother, onSkip, onPickMeal, onAdvance, disabled, acceptLabel }) {
  return (
    <div className="action-buttons">
      <button
        className="action-button accept-button"
        onClick={onAccept}
        disabled={disabled}
      >
        {acceptLabel || 'Cook this tonight'}
      </button>

      <button
        className="action-button another-button"
        onClick={onAnother}
        disabled={disabled}
      >
        Try another suggestion
      </button>

      <button
        className="action-button skip-button"
        onClick={onSkip}
        disabled={disabled}
      >
        Skip for now
      </button>

      <div className="action-links">
        {onPickMeal && (
          <button
            className="pick-meal-link"
            onClick={onPickMeal}
            disabled={disabled}
          >
            Pick a meal
          </button>
        )}
        {onAdvance && (
          <button
            className="pick-meal-link advance-link"
            onClick={onAdvance}
            disabled={disabled}
          >
            Plan next day →
          </button>
        )}
      </div>
    </div>
  );
}

export default ActionButtons;
