import React, { useState, useEffect, useCallback, useMemo } from 'react';
import RecommendationCard from './components/RecommendationCard';
import ActionButtons from './components/ActionButtons';
import SkipModal from './components/SkipModal';
import ChooseMealModal from './components/ChooseMealModal';
import WeekStrip from './components/WeekStrip';
import ManageRecipes from './pages/ManageRecipes';
import MealHistory from './pages/MealHistory';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  getRecommendation, acceptMeal, skipMeal, getAnotherMeal,
  getRecipes, addMealHistory, getPlannedMeals, deletePlannedMeal
} from './api/client';

/** Format a Date to YYYY-MM-DD in the local timezone (avoids UTC shift). */
function toLocalDateStr(d) {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function App() {
  const navigate = useNavigate();
  const location = useLocation();
  const currentView = location.pathname === '/history' ? 'history' : location.pathname === '/recipes' ? 'manage' : 'recommendation';
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);
  const [showSkipModal, setShowSkipModal] = useState(false);
  const [excludedIds, setExcludedIds] = useState([]);

  // Meal planning state
  const [allRecipes, setAllRecipes] = useState([]);
  const [plannedMeals, setPlannedMeals] = useState([]);
  const [showChooseModal, setShowChooseModal] = useState(false);
  const [planTargetDate, setPlanTargetDate] = useState(null);
  // Sticky target: null = auto-detect first empty day, string = locked date
  const [acceptTargetDate, setAcceptTargetDate] = useState(null);

  useEffect(() => {
    fetchRecommendation();
    fetchAllRecipes();
    fetchPlannedMeals();
  }, []);

  // Helper: find the first day without a planned meal
  const findFirstEmptyDay = useCallback((meals) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const plannedDates = new Set(meals.map((m) => m.date));

    for (let i = 0; i < 7; i++) {
      const d = new Date(today);
      d.setDate(d.getDate() + i);
      const key = toLocalDateStr(d);
      if (!plannedDates.has(key)) {
        return { date: key, offset: i, dayObj: d };
      }
    }
    // All 7 days full → default to today
    return { date: toLocalDateStr(today), offset: 0, dayObj: today };
  }, []);

  // Build the accept button label from the effective target date
  const { nextDate, acceptLabel, hasExistingMeal, headerLabel } = useMemo(() => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const plannedDates = new Set(plannedMeals.map((m) => m.date));

    let targetDate;
    if (acceptTargetDate) {
      // Sticky target — use the locked date
      const d = new Date(acceptTargetDate + 'T00:00:00');
      const offset = Math.round((d - today) / 86400000);
      targetDate = { date: acceptTargetDate, offset, dayObj: d };
    } else {
      // Auto-detect first empty day
      targetDate = findFirstEmptyDay(plannedMeals);
    }

    const alreadyPlanned = plannedDates.has(targetDate.date);

    let label;
    let header;
    if (targetDate.offset === 0) {
      label = alreadyPlanned ? 'Swap tonight\u2019s pick' : 'Cook this tonight';
      header = 'Tonight\u2019s suggestion';
    } else if (targetDate.offset === 1) {
      label = alreadyPlanned ? 'Swap tomorrow\u2019s pick' : 'Cook this tomorrow';
      header = 'Tomorrow\u2019s suggestion';
    } else {
      const dayName = targetDate.dayObj.toLocaleDateString('en-US', { weekday: 'long' });
      label = alreadyPlanned ? `Swap ${dayName}\u2019s pick` : `Cook this ${dayName}`;
      header = `${dayName}\u2019s suggestion`;
    }

    return { nextDate: targetDate.date, acceptLabel: label, hasExistingMeal: alreadyPlanned, headerLabel: header };
  }, [plannedMeals, acceptTargetDate, findFirstEmptyDay]);

  // Advance to the next empty day (clear sticky target)
  const advanceToNextDay = useCallback(() => {
    setAcceptTargetDate(null);
  }, []);

  const fetchRecommendation = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getRecommendation();
      setRecommendation(data);
      setExcludedIds([]);
    } catch (err) {
      setError('Could not load a recommendation. Make sure the backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchAllRecipes = async () => {
    try {
      const data = await getRecipes(1, 100);
      setAllRecipes(data.recipes || []);
    } catch (err) {
      console.error('Failed to load recipes for picker:', err);
    }
  };

  const fetchPlannedMeals = useCallback(async () => {
    try {
      const meals = await getPlannedMeals();
      setPlannedMeals(meals);
    } catch (err) {
      console.error('Failed to load planned meals:', err);
    }
  }, []);

  const handleAccept = async () => {
    if (!recommendation) return;
    setLoading(true);
    try {
      // If the target day already has a planned meal, replace it
      const existingMeal = plannedMeals.find((m) => m.date === nextDate);
      if (existingMeal) {
        await deletePlannedMeal(existingMeal.id);
      }

      // Plan the meal on the target date
      await addMealHistory({
        recipe_id: recommendation.recipe.id,
        date: nextDate,
        meal_type: 'dinner',
        cooked: false,
      });

      // Clear the target date to automatically advance to the next empty day
      setAcceptTargetDate(null);
      await fetchPlannedMeals();

      // Get a fresh recommendation for browsing alternatives
      await fetchRecommendation();

      setToast('Meal added to plan!');
      setTimeout(() => setToast(null), 3000);
    } catch (err) {
      setError('Failed to accept meal.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSkipClick = () => {
    setShowSkipModal(true);
  };

  const handleSkipConfirm = async (reason) => {
    setShowSkipModal(false);
    if (!recommendation) return;
    setLoading(true);
    try {
      const response = await skipMeal(recommendation.recipe.id, reason);
      if (response.next_suggestion) {
        setRecommendation(response.next_suggestion);
        setExcludedIds([]);
      } else {
        await fetchRecommendation();
      }
    } catch (err) {
      setError('Failed to skip meal.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnother = async () => {
    if (!recommendation) return;
    setLoading(true);
    try {
      const newExcludedIds = [...excludedIds, recommendation.recipe.id];
      setExcludedIds(newExcludedIds);
      const data = await getAnotherMeal(newExcludedIds);
      setRecommendation(data);
    } catch (err) {
      setError('Failed to get another recommendation.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Meal planning handlers
  const handlePickMealClick = () => {
    setPlanTargetDate(nextDate);
    setShowChooseModal(true);
  };

  const handleDayClick = async (dateStr) => {
    // If the day already has a meal, just set it as active target to browse alternatives
    const existingMeal = plannedMeals.find(m => m.date === dateStr);

    setAcceptTargetDate(dateStr);

    if (!existingMeal) {
      // Empty day, optionally open the modal to pick a specific recipe,
      // or they can just use the "Cook this" button for the default recommendation.
      setPlanTargetDate(dateStr);
      // Wait to fetch recommendation until after state updates
      await fetchRecommendation();
    } else {
      // Existing meal day, just get a fresh recommendation to swap
      await fetchRecommendation();
    }
  };

  const handleRecipeSelect = async (recipe) => {
    setShowChooseModal(false);
    try {
      await addMealHistory({
        recipe_id: recipe.id,
        date: planTargetDate,
        meal_type: 'dinner',
        cooked: false,
      });
      await fetchPlannedMeals();
    } catch (err) {
      console.error('Failed to plan meal:', err);
      setError('Failed to save planned meal.');
    }
  };

  const handleRemovePlannedMeal = async (mealId) => {
    try {
      await deletePlannedMeal(mealId);
      await fetchPlannedMeals();
    } catch (err) {
      console.error('Failed to remove planned meal:', err);
    }
  };

  const isWide = currentView === 'manage' || currentView === 'history';

  return (
    <div className="app">
      <header className="app-header">
        <h2 className="app-title">
          Next<span>Meal</span>
        </h2>
        <nav className="app-nav">
          <button
            className={currentView === 'recommendation' ? 'nav-active' : ''}
            onClick={() => navigate('/')}
          >
            Tonight's Meal
          </button>
          <button
            className={currentView === 'history' ? 'nav-active' : ''}
            onClick={() => navigate('/history')}
          >
            History
          </button>
          <button
            className={currentView === 'manage' ? 'nav-active' : ''}
            onClick={() => navigate('/recipes')}
          >
            Recipes
          </button>
        </nav>
      </header>

      <main className="app-main" style={isWide ? { maxWidth: '1100px' } : undefined}>
        <Routes>
          <Route path="/" element={
            <>
              {loading && !recommendation && (
                <div className="loading">
                  <div className="loading-dots">
                    <span /><span /><span />
                  </div>
                  <div className="loading-text">Finding your meal&hellip;</div>
                </div>
              )}

              {error && (
                <div className="error">
                  <p>{error}</p>
                  <button onClick={fetchRecommendation} className="retry-button">
                    Try Again
                  </button>
                </div>
              )}

              {!loading && !error && recommendation && (
                <>
                  <RecommendationCard recommendation={recommendation} headerLabel={headerLabel} />
                  <ActionButtons
                    onAccept={handleAccept}
                    onAnother={handleAnother}
                    onSkip={handleSkipClick}
                    onPickMeal={handlePickMealClick}
                    onAdvance={hasExistingMeal ? advanceToNextDay : null}
                    disabled={loading}
                    acceptLabel={acceptLabel}
                  />

                  <WeekStrip
                    plannedMeals={plannedMeals}
                    activeTargetDate={nextDate}
                    onDayClick={handleDayClick}
                    onRemoveMeal={handleRemovePlannedMeal}
                  />
                </>
              )}
            </>
          } />
          <Route path="/history" element={<MealHistory />} />
          <Route path="/recipes" element={<ManageRecipes />} />
        </Routes>
      </main>

      {showSkipModal && (
        <SkipModal
          onSkip={handleSkipConfirm}
          onCancel={() => setShowSkipModal(false)}
        />
      )}

      {showChooseModal && (
        <ChooseMealModal
          isOpen={showChooseModal}
          onClose={() => setShowChooseModal(false)}
          onSelect={handleRecipeSelect}
          recipes={allRecipes}
          targetDate={planTargetDate}
        />
      )}

      {toast && (
        <div className="toast-notification">
          {toast}
        </div>
      )}

      <footer className="app-footer">
        <p>Your personal cooking companion</p>
      </footer>
    </div>
  );
}

export default App;
