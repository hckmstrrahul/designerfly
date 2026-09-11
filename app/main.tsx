import React from 'react';
import { createRoot } from 'react-dom/client';
import DesignerFly from './page';
import './globals.css';

createRoot(document.getElementById('root')!).render(<React.StrictMode><DesignerFly /></React.StrictMode>);
