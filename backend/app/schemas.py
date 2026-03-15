from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional, List


# Category Schemas
class CategoryBase(BaseModel):
    name: str


class CategoryCreate(CategoryBase):
    pass


class Category(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Recipe Schemas
class RecipeBase(BaseModel):
    name: str
    like_score: Optional[int] = Field(None, ge=1, le=5)
    effort_score: int = Field(..., ge=1, le=5)
    prep_time_minutes: int = Field(default=0, ge=0)
    cook_time_minutes: int = Field(default=0, ge=0)
    cleanup_effort: str = Field(default='medium', pattern='^(low|medium|high)$')


class RecipeCreate(RecipeBase):
    category_ids: List[int] = []


class Recipe(RecipeBase):
    id: int
    last_cooked_date: Optional[date]
    last_suggested_date: Optional[date]
    skip_count: int
    created_at: datetime
    updated_at: datetime
    categories: List[Category] = []

    class Config:
        from_attributes = True


# MealHistory Schemas
class MealHistoryBase(BaseModel):
    date: date
    recipe_id: Optional[int]
    meal_type: str = 'dinner'
    cooked: bool = True


class MealHistoryCreate(MealHistoryBase):
    pass


class MealHistory(MealHistoryBase):
    id: int
    created_at: datetime
    recipe: Optional[Recipe]

    class Config:
        from_attributes = True


# Skip Schemas
class SkipCreate(BaseModel):
    recipe_id: int
    reason: Optional[str] = Field(None, pattern='^(missing_ingredients|not_in_mood|too_complex|already_had|no_time|too_much_effort|dont_like)$')


# Recommendation Schemas
class ContextSignals(BaseModel):
    time_of_day: str
    is_late: bool
    recent_skip_count: int
    fatigue_inferred: bool
    last_meal_effort: int
    recent_categories: List[str]
    planned_categories: List[str] = []


class RecommendationResponse(BaseModel):
    recipe: Recipe
    explanation: str
    context: ContextSignals


# Request Schemas
class AcceptRequest(BaseModel):
    recipe_id: int
    meal_type: str = 'dinner'


class SkipRequest(BaseModel):
    recipe_id: int
    reason: Optional[str] = Field(None, pattern='^(missing_ingredients|not_in_mood|too_complex|already_had|no_time|too_much_effort|dont_like)$')


class AnotherRequest(BaseModel):
    excluded_recipe_ids: List[int] = []


# Response Schemas
class AcceptResponse(BaseModel):
    success: bool
    meal_history_id: int
    next_recommendation: Optional[RecommendationResponse] = None


class SkipResponse(BaseModel):
    success: bool
    next_suggestion: RecommendationResponse


# Stats Schema
class CookingStats(BaseModel):
    total_meals_cooked: int
    most_cooked_recipes: List[dict]
    category_distribution: dict
    average_effort_score: float


# Pagination Schema
class PaginatedRecipes(BaseModel):
    recipes: List[Recipe]
    total: int
    page: int
    limit: int


# Recipe Update Schema (all fields optional for PATCH)
class RecipeUpdate(BaseModel):
    name: Optional[str] = None
    like_score: Optional[int] = Field(None, ge=1, le=5)
    effort_score: Optional[int] = Field(None, ge=1, le=5)
    prep_time_minutes: Optional[int] = Field(None, ge=0)
    cook_time_minutes: Optional[int] = Field(None, ge=0)
    cleanup_effort: Optional[str] = Field(None, pattern='^(low|medium|high)$')
    category_ids: Optional[List[int]] = None


# CSV Import/Export Schemas
class RecipeCSVRow(BaseModel):
    """Schema for CSV import row"""
    name: str
    like_score: Optional[int] = Field(None, ge=1, le=5)
    effort_score: int = Field(..., ge=1, le=5)
    prep_time_minutes: int = Field(default=0, ge=0)
    cook_time_minutes: int = Field(default=0, ge=0)
    cleanup_effort: str = Field(default='medium', pattern='^(low|medium|high)$')
    categories: str = ""  # Pipe-separated category names


class ImportResult(BaseModel):
    """Result of CSV import operation"""
    success: bool
    total_rows: int
    imported_count: int
    updated_count: int
    skipped_count: int
    errors: List[dict]  # [{row: int, error: str}]


class DeleteRecipeResponse(BaseModel):
    """Response for recipe deletion"""
    success: bool
    message: str
    recipe_id: int
    meal_history_affected: int


class DeleteMealHistoryResponse(BaseModel):
    """Response for planned meal deletion"""
    success: bool
    message: str
