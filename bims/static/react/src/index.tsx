/**
 * SPDX-FileCopyrightText: Kartoza
 * SPDX-License-Identifier: AGPL-3.0
 *
 * Entry point for BIMS React frontend.
 *
 * Made with love by Kartoza | https://kartoza.com
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// Import MapLibre CSS
import 'maplibre-gl/dist/maplibre-gl.css';

// Mount the React application
const container = document.getElementById('react-app');

if (container) {
  const root = createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
} else {
  console.error('Could not find #react-app element to mount React application');
}
