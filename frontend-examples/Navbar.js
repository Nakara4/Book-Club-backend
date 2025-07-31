import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar = () => {
  const { user, isAuthenticated, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  return (
    <nav className="navbar" style={{ padding: '1rem', borderBottom: '1px solid #ccc' }}>
      <div className="nav-brand">
        <Link to="/" style={{ textDecoration: 'none', fontWeight: 'bold' }}>
          Book Club
        </Link>
      </div>

      <div className="nav-links" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <Link to="/">Home</Link>

        {/* Show these links only for authenticated users */}
        {isAuthenticated && (
          <>
            <Link to="/clubs">My Clubs</Link>
            <Link to="/discover">Discover</Link>
          </>
        )}

        {/* Show admin navigation ONLY if user is staff/superuser */}
        {isAuthenticated && isAdmin && (
          <div data-cy="admin-nav" style={{ display: 'flex', gap: '0.5rem' }}>
            <Link 
              to="/admin/dashboard" 
              style={{ 
                backgroundColor: '#007bff', 
                color: 'white', 
                padding: '0.25rem 0.5rem', 
                borderRadius: '4px',
                textDecoration: 'none'
              }}
            >
              Admin Dashboard
            </Link>
          </div>
        )}

        {/* Authentication links */}
        {isAuthenticated ? (
          <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
            <span>Welcome, {user?.first_name || user?.username}!</span>
            {user?.is_staff && <span style={{ color: 'green', fontSize: '0.8em' }}>(Admin)</span>}
            <button onClick={handleLogout} style={{ padding: '0.25rem 0.5rem' }}>
              Logout
            </button>
          </div>
        ) : (
          <Link to="/login">Login</Link>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
