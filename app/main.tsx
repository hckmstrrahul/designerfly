import React from 'react';
import { createRoot } from 'react-dom/client';
import DesignerFly from './page';
import './globals.css';

const Feedback = import.meta.env.DEV ? React.lazy(() => import('agentation').then(module => ({ default: module.Agentation }))) : null;

createRoot(document.getElementById('root')!).render(<React.StrictMode><DesignerFly />{Feedback && <React.Suspense fallback={null}><Feedback /></React.Suspense>}</React.StrictMode>);
