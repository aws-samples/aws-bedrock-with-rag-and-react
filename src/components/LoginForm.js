import React, { useState } from 'react';
import './LoginForm.css'; 

const LoginForm = ({ onUserValidation }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [userValidated, setUserValidated] = useState(false);

  const handleUsernameChange = (e) => {
    setUsername(e.target.value);
  };

  const handlePasswordChange = (e) => {
    setPassword(e.target.value);
  };

  const handleSubmit = (e) => {
    e.preventDefault();

    if (username.toLowerCase() === 'teuser' && password === 'TEL.meCapAws') {
        onUserValidation(true);
    } else {
      onUserValidation(false);
      setError('Invalid username or password.');
    }

    setUsername('');
    setPassword('');
  };

  return (
    <div className="container">
      {userValidated ? (
        <div className="welcome-message">
          <p>Welcome, {username}!</p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="login-form">
          <label htmlFor="username">User name:</label>
          <input
            type="text"
            id="username"
            value={username}
            onChange={handleUsernameChange}
          />

          <label htmlFor="password">Password:</label>
          <input
            type="password"
            id="password"
            value={password}
            onChange={handlePasswordChange}
          />

          {error && <div className="error-message">{error}</div>}

          <button type="submit">Login</button>
        </form>
      )}
    </div>
  );
};

export default LoginForm;
