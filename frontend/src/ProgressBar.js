import React from 'react';

function ProgressBar({ progress }) {
    return (
        <div>
            <div style={{ width: '100%', backgroundColor: '#e0e0e0', borderRadius: '5px', overflow: 'hidden' }}>
                <div style={{ width: `${progress}%`, backgroundColor: '#76c7c0', height: '20px', textAlign: 'center', color: 'white', lineHeight: '20px' }}>
                    {progress}%
                </div>
            </div>
        </div>
    );
}

export default ProgressBar;
