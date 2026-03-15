import React from 'react';

/**
 * Category filter dropdown
 */
function FilterBar({ categories, selectedCategoryId, onCategoryChange }) {
  return (
    <select
      className="filter-select"
      value={selectedCategoryId || ''}
      onChange={(e) => onCategoryChange(e.target.value ? parseInt(e.target.value) : null)}
    >
      <option value="">All Categories</option>
      {categories.map((category) => (
        <option key={category.id} value={category.id}>
          {category.name}
        </option>
      ))}
    </select>
  );
}

export default FilterBar;
