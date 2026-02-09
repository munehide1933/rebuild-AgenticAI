@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  * {
    @apply border-gray-200;
  }
  
  body {
    @apply bg-gray-50 text-gray-900;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
      'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
      sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }

  code {
    font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
      monospace;
  }
}

@layer components {
  /* Scrollbar styles */
  .scrollbar-thin::-webkit-scrollbar {
    @apply w-2;
  }

  .scrollbar-thin::-webkit-scrollbar-track {
    @apply bg-gray-100;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb {
    @apply bg-gray-300 rounded-full;
  }

  .scrollbar-thin::-webkit-scrollbar-thumb:hover {
    @apply bg-gray-400;
  }

  /* Markdown styles override */
  .prose {
    @apply max-w-none;
  }

  .prose code {
    @apply bg-gray-800 text-gray-100 px-1 py-0.5 rounded text-sm;
  }

  .prose pre {
    @apply bg-gray-900 rounded-lg my-4;
  }

  .prose pre code {
    @apply bg-transparent p-0;
  }

  .prose h1,
  .prose h2,
  .prose h3,
  .prose h4 {
    @apply font-semibold text-gray-800 mt-6 mb-3;
  }

  .prose p {
    @apply my-2 leading-relaxed;
  }

  .prose ul,
  .prose ol {
    @apply my-3 ml-6;
  }

  .prose li {
    @apply my-1;
  }

  .prose a {
    @apply text-primary-600 hover:text-primary-700 underline;
  }

  .prose blockquote {
    @apply border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4;
  }

  .prose table {
    @apply w-full my-4 border-collapse;
  }

  .prose th,
  .prose td {
    @apply border border-gray-300 px-4 py-2;
  }

  .prose th {
    @apply bg-gray-100 font-semibold;
  }
}

/* Custom animations */
@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-0.5rem);
  }
}

.animate-bounce {
  animation: bounce 1s infinite;
}
/* 确保根元素和 body 占满全屏 */
html, body, #root {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
  overflow: hidden;
}

/* 修复 prose 样式导致的间距问题 */
.prose p {
  margin-top: 0.5rem !important;
  margin-bottom: 0.5rem !important;
}

.prose ul,
.prose ol {
  margin-top: 0.5rem !important;
  margin-bottom: 0.5rem !important;
}

/* 修复代码块样式 */
.prose pre {
  margin-top: 0.75rem !important;
  margin-bottom: 0.75rem !important;
  max-width: 100%;
  overflow-x: auto;
}

/* 确保滚动条可见且可用 */
.overflow-y-auto {
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch;
}

/* 自定义滚动条样式（可选） */
.overflow-y-auto::-webkit-scrollbar {
  width: 8px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background: #555;
}

/* 修复 Markdown 渲染导致的白色文本问题 */
.prose.text-white * {
  color: white !important;
}

.prose.text-white a {
  color: #93c5fd !important;
  text-decoration: underline;
}

.prose.text-white code {
  background-color: rgba(255, 255, 255, 0.2) !important;
  color: white !important;
}