'use client';

import MainLayout from '@/components/Layout/MainLayout';
import ErrorBoundary from '@/components/ErrorBoundary';

export default function HomePage() {
  return (
    <ErrorBoundary>
      <MainLayout />
    </ErrorBoundary>
  );
}
