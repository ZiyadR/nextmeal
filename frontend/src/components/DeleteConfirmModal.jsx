import React from 'react';

/**
 * Delete confirmation modal
 */
function DeleteConfirmModal({ recipe, onConfirm, onCancel }) {
  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Delete Recipe?</h3>
        <p>
          Are you sure you want to delete <strong>{recipe.name}</strong>?
        </p>
        <p className="warning-text">
          This action cannot be undone. Meal history will be preserved but
          associated with "deleted recipe".
        </p>
        <div className="modal-actions">
          <button className="btn-secondary" onClick={onCancel}>
            Cancel
          </button>
          <button className="btn-danger" onClick={onConfirm}>
            Delete
          </button>
        </div>
      </div>
    </div>
  );
}

export default DeleteConfirmModal;
