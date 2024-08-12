// Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
// SPDX-License-Identifier: MIT.

import React from 'react';
import App from './App';
import { Route, Routes } from 'react-router-dom';

export const Routing = () => {
  return (
    <div>
      <Routes>
        <Route path="/" element={<App model={"Anthropic"}/>} />
        <Route path="/Anthropic" element={<App model={"Anthropic"}/>} />
        <Route path="/Amazon" element={<App model={"Amazon"}/>} />
        <Route path="/AI21" element={<App model={"AI21"}/>} />
      </Routes>
    </div>
  );
};

