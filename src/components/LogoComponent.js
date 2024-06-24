// LogoComponent.js

import React from 'react';
import appLogo from "../te-connectivity-logo.png";
import './LogoComponent.css';

const LogoComponent = () => {
  return (
    <div className="logo-container">
      <img src={appLogo} alt="Logo" className="logo-image" />
    </div>
  );
};

export default LogoComponent;
