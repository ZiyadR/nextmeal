# ROLE
You are a senior full-stack engineer and product-minded AI agent.
You are building a **local-first decision-fatigue-friendly cooking assistant**.

Your goal is to **minimize user decisions**, automate repetitive logic, and apply **context-aware recommendations**.

---

# PRODUCT SUMMARY
Build a local application that suggests what to cook today based on:
- Past meal history
- Recipe preferences
- Effort tolerance
- Category spacing
- Recent skips
- Context (day, time, fatigue inference)

The app behaves like a **smart assistant**, not a planner.

---

# NON-GOALS (DO NOT BUILD)
- No nutrition tracking
- No shopping lists
- No calendars
- No social features
- No cloud sync
- No accounts
- No heavy onboarding flows

---

# TECH CONSTRAINTS
- Must run locally on a personal computer
- Moderate setup only (no Kubernetes, no cloud infra)
- Prefer:
  - Python (FastAPI or Flask)
  - SQLite
  - Simple web UI (React, Svelte, or basic HTML)
- Everything runs via a single command after setup

---

# CORE USER FLOW
1. User opens the app
2. App shows **one recommended meal**
3. User can:
   - Accept (cook this)
   - Get another suggestion
   - Skip today
4. App learns silently from behavior

---

# DATA MODELS

## Recipe
- id
- name
- like_score (1–5, nullable)
- effort_score (1–5)
- prep_time_minutes
- cook_time_minutes
- cleanup_effort (low|medium|high)
- categories (many-to-many)
- last_cooked_date
- last_suggested_date
- skip_count

## MealHistory
- date
- recipe_id (nullable for eating out)
- meal_type (dinner by default)
- cooked (boolean)

## Category
- id
- name

---

# RECOMMENDATION LOGIC

## Principles
- Reduce repetition
- Bias toward loved + easy meals
- Respect recent skips
- Space categories apart
- Favor ease when fatigue is inferred

## Inference Signals
- Recent skips → low energy
- Late time → short meals
- Recent hard meals → prefer easy
- Same category recently → penalize

## Scoring (conceptual)
score = preference_weight - effort_penalty - recentness_penalty - category_overlap_penalty - context_match_bonus


Implement with readable, debuggable code — no ML required.

---

# SKIP BEHAVIOR
- Skip → suppress recipe for 4 days
- Optional reason:
  - Too much effort → increase effort penalty
  - Don’t like anymore → decrease preference

Never require a reason.

---

# UI REQUIREMENTS
- Extremely minimal
- Default screen:
  - Meal name
  - One-line explanation
  - 3 buttons only
- No scrolling required
- No configuration required to get value

---

# AUTOMATION RULES
- Accepting a recommendation auto-logs the meal
- Repeated accepts increase inferred preference
- Frequently skipped meals decay in weight
- Category spacing handled automatically

---

# SETUP REQUIREMENTS
1. Provide clear README
2. Setup should be:
	- git clone
	- install dependencies
	- run one command
3. Use SQLite migrations or auto-create schema
4. Seed data with example recipes

---

# DELIVERABLES
- Backend API
- Recommendation engine module
- Minimal UI
- Local database
- Setup instructions
- Reasonable defaults
- Clean, documented code

---

# QUALITY BAR
- Readable code over clever code
- Deterministic behavior
- Easy to extend later
- User never feels judged or overwhelmed

---

# FINAL INSTRUCTION
Build the app end-to-end.
Make sensible decisions where unspecified.
Explain setup clearly.
Do not over-engineer.
