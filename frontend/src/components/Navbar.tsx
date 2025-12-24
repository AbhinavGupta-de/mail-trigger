import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar: React.FC = () => {
  const { user, logout, isAdmin } = useAuth();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="navbar">
      <div className="nav-brand">
        <Link to="/dashboard">Email Trigger</Link>
      </div>
      <div className="nav-links">
        <Link to="/dashboard" className={isActive('/dashboard') ? 'active' : ''}>
          Dashboard
        </Link>
        <Link to="/send" className={isActive('/send') ? 'active' : ''}>
          Send Email
        </Link>
        <Link to="/templates" className={isActive('/templates') ? 'active' : ''}>
          Templates
        </Link>
        <Link to="/recipients" className={isActive('/recipients') ? 'active' : ''}>
          Recipients
        </Link>
        <Link to="/history" className={isActive('/history') ? 'active' : ''}>
          History
        </Link>
        {isAdmin && (
          <Link to="/admin" className={isActive('/admin') ? 'active' : ''}>
            Admin
          </Link>
        )}
      </div>
      <div className="nav-user">
        <span>{user?.name}</span>
        <button className="btn btn-outline" onClick={logout}>
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
