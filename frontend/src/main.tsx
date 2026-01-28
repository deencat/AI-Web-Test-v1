import ReactDOM from 'react-dom/client';
import App from './App.tsx';
import './index.css';

// Note: StrictMode disabled to prevent double initialization of debug sessions
// which would create two browser windows. Re-enable for development of non-debug features.
ReactDOM.createRoot(document.getElementById('root')!).render(
  <App />,
);
