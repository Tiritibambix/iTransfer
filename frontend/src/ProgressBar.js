import React from 'react';

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
      <style jsx>{`
        .progress-container {
          width: 100%;
          max-width: 400px;
          margin: 20px auto;
          padding: 0 20px;
        }
        
        .progress-bar {
          width: 100%;
          height: 12px;
          background-color: var(--clr-surface-a20);
          border-radius: 6px;
          overflow: hidden;
          box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
        }
        
        .progress-fill {
          height: 100%;
          background: linear-gradient(90deg, var(--clr-primary-a30) 0%, var(--clr-primary-a40) 100%);
          border-radius: 6px;
          transition: width 0.3s ease-in-out;
          position: relative;
        }
        
        .progress-text {
          position: absolute;
          right: 8px;
          top: 50%;
          transform: translateY(-50%);
          font-size: 10px;
          color: white;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
      `}</style>
    </div>
  );
};

export default ProgressBar;
