export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center">
      <div className="w-16 h-16 bg-primary-600 rounded-2xl flex items-center justify-center mb-6">
        <span className="text-white font-bold text-2xl">DD</span>
      </div>
      <h1 className="text-4xl font-bold text-gray-900 mb-4">AI Due Diligence Copilot</h1>
      <p className="text-lg text-gray-600 max-w-xl mb-8">
        Upload financial documents. Get source-backed risk assessments, growth opportunities,
        and executive summaries in seconds.
      </p>
      <div className="flex gap-4">
        <a href="/upload" className="px-6 py-3 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition">
          Upload Documents
        </a>
        <a href="/dashboard" className="px-6 py-3 bg-white text-gray-700 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition">
          View Dashboard
        </a>
      </div>
      <div className="mt-12 grid grid-cols-3 gap-8 max-w-2xl">
        <div className="text-center">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <span className="text-xl">📄</span>
          </div>
          <h3 className="font-medium text-gray-900">Multi-Format</h3>
          <p className="text-sm text-gray-500">PDF, PPTX, DOCX, XLSX, CSV, TXT</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <span className="text-xl">🔍</span>
          </div>
          <h3 className="font-medium text-gray-900">Hybrid RAG</h3>
          <p className="text-sm text-gray-500">Dense + BM25 search with citations</p>
        </div>
        <div className="text-center">
          <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center mx-auto mb-2">
            <span className="text-xl">⚠️</span>
          </div>
          <h3 className="font-medium text-gray-900">Risk Engine</h3>
          <p className="text-sm text-gray-500">5-category risk scoring with evidence</p>
        </div>
      </div>
    </div>
  );
}
