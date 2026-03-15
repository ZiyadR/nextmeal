import React, { useState } from 'react';
import { importRecipes } from '../api/client';

/**
 * CSV import modal
 */
function ImportCSVModal({ onClose, onSuccess }) {
  const [file, setFile] = useState(null);
  const [updateExisting, setUpdateExisting] = useState(true);
  const [importing, setImporting] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setError(null);
    setResult(null);
  };

  const handleImport = async () => {
    if (!file) {
      setError('Please select a CSV file');
      return;
    }

    setImporting(true);
    setError(null);

    try {
      const importResult = await importRecipes(file, updateExisting);
      setResult(importResult);
      if (importResult.imported_count > 0 || importResult.updated_count > 0) {
        setTimeout(() => {
          onSuccess();
        }, 2000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <h3>Import Recipes from CSV</h3>

        <div className="form-group">
          <label className="form-label">CSV File</label>
          <input type="file" accept=".csv" onChange={handleFileChange} />
          <p className="form-help">
            Expected columns: name, like_score, effort_score, prep_time_minutes,
            cook_time_minutes, cleanup_effort, categories (pipe-separated)
          </p>
        </div>

        <div className="form-group">
          <label className="checkbox-label">
            <input
              type="checkbox"
              checked={updateExisting}
              onChange={(e) => setUpdateExisting(e.target.checked)}
            />
            Update existing recipes with same name
          </label>
        </div>

        {error && <div className="error-message">{error}</div>}

        {result && (
          <div className="import-results">
            <h4>Import Complete</h4>
            <div className="import-stats">
              <div className="import-stat">
                <span className="import-stat-label">Total Rows</span>
                <span className="import-stat-value">{result.total_rows}</span>
              </div>
              <div className="import-stat">
                <span className="import-stat-label">Imported</span>
                <span className="import-stat-value success">
                  {result.imported_count}
                </span>
              </div>
              <div className="import-stat">
                <span className="import-stat-label">Updated</span>
                <span className="import-stat-value">{result.updated_count}</span>
              </div>
              <div className="import-stat">
                <span className="import-stat-label">Skipped</span>
                <span className="import-stat-value">{result.skipped_count}</span>
              </div>
            </div>

            {result.errors && result.errors.length > 0 && (
              <div className="import-errors">
                <h5>Errors:</h5>
                {result.errors.map((err, idx) => (
                  <div key={idx} className="import-error-item">
                    Row {err.row}: {err.error}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="modal-actions">
          <button className="btn-secondary" onClick={onClose} disabled={importing}>
            Close
          </button>
          <button
            className="btn-primary"
            onClick={handleImport}
            disabled={!file || importing}
          >
            {importing ? 'Importing...' : 'Import'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ImportCSVModal;
