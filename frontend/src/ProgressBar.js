import React from 'react';

const ProgressBar = ({ progress }) => {
  return (
    <div style={{ width: '80%', margin: '20px auto', backgroundColor: '#f3f3f3', borderRadius: '5px' }}>
      <div
        style={{
          width: `${progress}%`,
          height: '10px',
          backgroundColor: '#4caf50',
          borderRadius: '5px',
          transition: 'width 0.3s ease-in-out',
        }}
      ></div>
    </div>
  );
};

export default ProgressBar;
