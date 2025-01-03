import React from 'react';
import { Navigate } from 'react-router-dom';

const PrivateRoute = ({ children }) => {
  const authToken = localStorage.getItem('authToken');
  console.log('authToken:', authToken); // Ajoutez ce log pour vérifier

  return authToken ? children : <Navigate to="/login" />;
};

export default PrivateRoute;
