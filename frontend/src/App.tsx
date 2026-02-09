import MainLayout from './components/Layout/MainLayout';
import ErrorBoundary from './components/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary>
      <MainLayout />
    </ErrorBoundary>
  );
}

export default App;
