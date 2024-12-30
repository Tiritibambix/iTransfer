import React from 'react';
import { useLocation } from 'react-router-dom';
import ProgressBar from './ProgressBar';

function Progress() {
    const location = useLocation();
    const { progress } = location.state || { progress: 0 };

    return (
        <div>
            <h1>Upload Progress</h1>
            <ProgressBar progress={progress} />
        </div>
    );
}

export default Progress;
