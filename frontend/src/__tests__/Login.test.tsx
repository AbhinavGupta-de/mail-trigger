import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import Login from '../pages/Login';

const mockLogin = vi.fn();

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    login: mockLogin
  })
}));

describe('Login', () => {
  it('renders login page with features', () => {
    render(<Login />);

    expect(screen.getByText('Email Trigger')).toBeInTheDocument();
    expect(screen.getByText('Pre-built email templates')).toBeInTheDocument();
    expect(screen.getByText('Save default recipients & CC')).toBeInTheDocument();
    expect(screen.getByText('Auto-fill variables like name & date')).toBeInTheDocument();
  });

  it('calls login when sign in button is clicked', () => {
    render(<Login />);

    const signInButton = screen.getByText('Sign in with Google');
    fireEvent.click(signInButton);

    expect(mockLogin).toHaveBeenCalled();
  });
});
