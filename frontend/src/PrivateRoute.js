import React from 'react';
import { Redirect } from 'react-router-dom';

const PrivateRoute = ({ children }) => {
  const authToken = localStorage.getItem('authToken');
  return authToken ? children : <Redirect to="/login" />;
};

export default PrivateRoute;
