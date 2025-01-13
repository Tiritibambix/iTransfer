import React from 'react';

const styles = {
  progressContainer: {
    width: '100%',
    maxWidth: '400px',
    margin: '20px auto',
    padding: '0 20px'
  },
  progressBar: {
    width: '100%',
    height: '12px',
    backgroundColor: 'var(--clr-surface-a20)',
    borderRadius: '6px',
    overflow: 'hidden',
    boxShadow: 'inset 0 1px 3px rgba(0, 0, 0, 0.2)'
  },
  progressFill: {
    height: '100%',
    background: 'linear-gradient(90deg, var(--clr-primary-a30) 0%, var(--clr-primary-a40) 100%)',
    borderRadius: '6px',
    transition: 'width 0.3s ease-in-out',
    position: 'relative'
  },
  progressText: {
    position: 'absolute',
    right: '8px',
    top: '50%',
    transform: 'translateY(-50%)',
    fontSize: '10px',
    color: 'white',
    textShadow: '0 1px 2px rgba(0, 0, 0, 0.3)'
  }
};

const ProgressBar = ({ progress }) => {
  return (
    <div style={styles.progressContainer}>
      <div style={styles.progressBar}>
        <div
          style={{
            ...styles.progressFill,
            width: `${progress}%`
          }}
        >
          <span style={styles.progressText}>{progress}%</span>
        </div>
      </div>
    </div>
  );
};

export default ProgressBar;
