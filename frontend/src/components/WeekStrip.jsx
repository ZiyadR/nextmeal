import React from 'react';

/**
 * Compact horizontal week strip showing planned meals.
 * Sits below the action buttons — understated, not dominant.
 */
function WeekStrip({ plannedMeals, activeTargetDate, onDayClick, onRemoveMeal }) {
  const today = new Date();
  today.setHours(0, 0, 0, 0);

  // Build 7 days starting from today
  const days = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(today);
    d.setDate(d.getDate() + i);
    return d;
  });

  const formatDateKey = (d) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  };

  const dayAbbr = (d) =>
    d.toLocaleDateString('en-US', { weekday: 'short' }).toUpperCase();

  const dayNum = (d) => d.getDate();

  // Map planned meals by date string for quick lookup
  const mealsByDate = {};
  if (plannedMeals) {
    plannedMeals.forEach((m) => {
      mealsByDate[m.date] = m;
    });
  }

  return (
    <div className="week-strip">
      <div className="week-strip-label">This week</div>
      <div className="week-strip-days">
        {days.map((d, i) => {
          const key = formatDateKey(d);
          const meal = mealsByDate[key];
          const isToday = i === 0;

          const isActive = key === activeTargetDate;

          return (
            <div
              key={key}
              className={`week-day ${isToday ? 'week-day--today' : ''} ${meal ? 'week-day--planned' : 'week-day--empty'} ${isActive ? 'week-day--active' : ''}`}
              onClick={() => onDayClick(key)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onDayClick(key);
                }
              }}
              tabIndex="0"
              aria-label={meal ? `Planned for ${dayAbbr(d)} ${dayNum(d)}: ${meal.recipe?.name || 'Manual entry'}. Press enter to view or select.` : `Empty day, ${dayAbbr(d)} ${dayNum(d)}. Press enter to plan a meal.`}
              title={meal ? `${meal.recipe?.name || 'Planned'} — click to remove or select` : `Plan a meal for ${dayAbbr(d)}`}
            >
              <span className="week-day-abbr">{dayAbbr(d)}</span>
              <span className="week-day-num-wrapper">
                <span className="week-day-num">{dayNum(d)}</span>
              </span>
              {meal && (
                <div className="week-day-meal">
                  <span className="week-day-recipe">{meal.recipe?.name || '—'}</span>
                  <button
                    className="week-day-remove"
                    onClick={(e) => {
                      e.stopPropagation();
                      onRemoveMeal(meal.id);
                    }}
                    title="Remove"
                    aria-label={`Remove planned meal for ${dayAbbr(d)}`}
                  >
                    ×
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default WeekStrip;
