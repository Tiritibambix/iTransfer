import React from 'react';
import './ProgressBar.css';

const ProgressBar = ({ progress }) => {
  return (
    <div className="progress-container">
      <div className="progress-bar">
        <div
          className="progress-fill"
          style={{
            width: `${progress}%`,
          }}
        >
          <span className="progress-text">{progress}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
