import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Sift - AI Due Diligence',
  description: 'Analyze financial documents with AI-powered risk assessment and executive summaries.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="min-h-screen bg-gray-50">
          <nav className="bg-white border-b border-gray-200 px-6 py-3">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <a href="/" className="flex items-center gap-2">
                <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-sm">S</span>
                </div>
                <span className="text-lg font-semibold text-gray-900">Sift</span>
              </a>
              <div className="flex items-center gap-6">
                <a href="/upload" className="text-sm text-gray-600 hover:text-primary-600">Upload</a>
                <a href="/dashboard" className="text-sm text-gray-600 hover:text-primary-600">Dashboard</a>
                <a href="/chat" className="text-sm text-gray-600 hover:text-primary-600">Chat</a>
              </div>
            </div>
          </nav>
          <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
        </div>
      </body>
    </html>
  );
}
