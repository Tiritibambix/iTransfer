import React from 'react';
import { BrowserRouter as Router, Route, Switch } from 'react-router-dom';
import Admin from './Admin';
import Upload from './Upload';
import FileManager from './FileManager';
import Settings from './Settings';

function App() {
    return (
        <Router>
            <Switch>
                <Route path="/admin" component={Admin} />
                <Route path="/upload" component={Upload} />
                <Route path="/files" component={FileManager} />
                <Route path="/settings" component={Settings} />
            </Switch>
        </Router>
    );
}

export default App;
