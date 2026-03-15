import React from 'react';

const SKIP_REASONS = [
  { id: 'missing_ingredients', label: "Missing ingredients" },
  { id: 'not_in_mood',        label: "Not in the mood" },
  { id: 'too_complex',        label: "Too complex right now" },
  { id: 'already_had',        label: "Had it recently" },
  { id: 'no_time',            label: "No time today" },
];

/**
 * Modal for skipping a meal recommendation.
 * Reasons shown as horizontal choice pills; cancel below.
 */
function SkipModal({ onSkip, onCancel }) {
  return (
    <div className="modal-overlay" onClick={onCancel}>
      <div
        className="modal-content"
        onClick={(e) => e.stopPropagation()}
      >
        <h3>Skip for now?</h3>
        <p className="modal-subtitle">
          Choose a reason so we can suggest something better next time.
        </p>

        <div className="skip-choices">
          {SKIP_REASONS.map((reason) => (
            <button
              key={reason.id}
              className="modal-button reason-button"
              onClick={() => onSkip(reason.id)}
            >
              {reason.label}
            </button>
          ))}

          <button
            className="modal-button modal-skip-plain"
            onClick={() => onSkip(null)}
          >
            Skip without reason
          </button>
        </div>

        <button className="cancel-button" onClick={onCancel}>
          Keep this suggestion
        </button>
      </div>
    </div>
  );
}

export default SkipModal;
