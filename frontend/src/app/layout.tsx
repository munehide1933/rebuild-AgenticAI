import './globals.css';
import type { ReactNode } from 'react';

export const metadata = {
  title: 'Meta-Agent',
  description: 'Agentic development system with streaming chat and patch generation.',
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
