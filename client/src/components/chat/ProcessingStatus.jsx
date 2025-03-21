import React from 'react';

/**
 * ProcessingStatus component - Displays current processing steps and status messages
 *
 * @param {Object} props
 * @param {Array} props.processingSteps - List of processing steps
 * @param {string} props.status - Current status message
 * @returns {JSX.Element} - The rendered component
 */
const ProcessingStatus = ({ processingSteps, status }) => {
  return (
    <>
      {/* Processing steps display */}
      {processingSteps && processingSteps.length > 0 && (
        <div className="processing-steps">
          {processingSteps.map((step, index) => (
            <div key={index} className="processing-step">
              <span className="step-icon">{step.icon || '⚙️'}</span>
              <span className="step-status">{step.status}</span>
            </div>
          ))}
        </div>
      )}

      {/* Status message */}
      {status && <div className="status-message">{status}</div>}
    </>
  );
};

export default ProcessingStatus;
