// src/App.jsx
import { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Provider } from 'react-redux';
import { store } from './store/store';
import Layout from './components/layout';
import ProtectedRoute from './components/ProtectedRoute';
import Homepage from './pages/Homepage';
import Login from './pages/Login';
import Signup from './pages/Signup';
import EmailVerification from './pages/EmailVerification';
import Restaurants from './pages/Restaurants';
import csrfService from './services/csrf';

function App() {
  useEffect(() =>{
    const initializeCSRF = async () =>{
      try {
        await csrfService.ensureToken();
      }
      catch (error) {
        console.warn('CSRF token initialization failed:', error);
      }
    };
    initializeCSRF();
  }, []);

  return (
    <Provider store={store}>
      <Router>
        <Routes>
          <Route path="/" element={<Layout/>}>
            <Route index element={
              <ProtectedRoute>
                <Homepage/>
              </ProtectedRoute>
              }/>
            <Route path="/login" element={
              <ProtectedRoute requireAuth={false}>
                <Login/>
              </ProtectedRoute>
            }/>
            <Route path="/signup" element={
              <ProtectedRoute requireAuth={false}>
                <Signup />
              </ProtectedRoute>
            }/>
            <Route path="/verify-email" element={
              <ProtectedRoute requireAuth={false}>
                <EmailVerification />
              </ProtectedRoute>
            }/>
            <Route path='/restaurants' element={
              <ProtectedRoute>
                <Restaurants/>
              </ProtectedRoute>
            }/>
          </Route>
        </Routes>
      </Router>
    </Provider>
  );
}

export default App;