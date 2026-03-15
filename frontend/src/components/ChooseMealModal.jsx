import React, { useState, useEffect, useRef } from 'react';

/**
 * Modal for choosing a specific recipe to plan on a given date.
 * Reuses the skip-modal visual pattern (blurred backdrop, floating card).
 */
function ChooseMealModal({ isOpen, onClose, onSelect, recipes, targetDate }) {
  const [search, setSearch] = useState('');
  const inputRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      setSearch('');
      // Auto-focus search input after a tick
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const filtered = recipes.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  const effortLabels = { 1: 'Very Easy', 2: 'Easy', 3: 'Moderate', 4: 'Effort', 5: 'Hard' };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr + 'T00:00:00');
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    if (d.getTime() === today.getTime()) return 'today';
    if (d.getTime() === tomorrow.getTime()) return 'tomorrow';
    return d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content choose-meal-modal" onClick={(e) => e.stopPropagation()}>
        <div className="choose-meal-header">
          <h2>Pick a meal{targetDate ? ` for ${formatDate(targetDate)}` : ''}</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div className="choose-meal-search">
          <input
            ref={inputRef}
            type="text"
            placeholder="Search recipes…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="choose-meal-input"
          />
        </div>

        <div className="choose-meal-list">
          {filtered.length === 0 ? (
            <div className="choose-meal-empty">No recipes match your search</div>
          ) : (
            filtered.map((recipe) => (
              <button
                key={recipe.id}
                className="choose-meal-item"
                onClick={() => onSelect(recipe)}
              >
                <span className="choose-meal-name">{recipe.name}</span>
                <span className="choose-meal-effort">
                  {effortLabels[recipe.effort_score] || ''}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

export default ChooseMealModal;
