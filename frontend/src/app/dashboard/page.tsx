'use client';
import { useEffect, useState } from 'react';
import { listDocuments, deleteDocument, type Document } from '@/lib/api';

export default function DashboardPage() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDocuments();
  }, []);

  async function loadDocuments() {
    try {
      const docs = await listDocuments();
      setDocuments(docs);
    } catch (err) {
      console.error('Failed to load documents:', err);
    }
    setLoading(false);
  }

  async function handleDelete(id: string) {
    if (!confirm('Delete this document?')) return;
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      console.error('Delete failed:', err);
    }
  }

  function formatSize(bytes: number) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <a href="/upload" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
          + Upload
        </a>
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-500">Loading...</div>
      ) : documents.length === 0 ? (
        <div className="text-center py-16">
          <div className="w-16 h-16 bg-gray-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <span className="text-3xl">📄</span>
          </div>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">No documents yet</h2>
          <p className="text-gray-500 mb-4">Upload your first document to get started</p>
          <a href="/upload" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">
            Upload Documents
          </a>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">File</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Type</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Size</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Pages</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Chunks</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Status</th>
                <th className="text-left px-6 py-3 text-xs font-semibold text-gray-500 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {documents.map((doc) => (
                <tr key={doc.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <span className="font-medium text-gray-900">{doc.filename}</span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500 uppercase">{doc.doc_type}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{formatSize(doc.file_size)}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{doc.page_count ?? '—'}</td>
                  <td className="px-6 py-4 text-sm text-gray-500">{doc.chunk_count}</td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      doc.status === 'ready' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'
                    }`}>
                      {doc.status}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      <a
                        href={`/analysis/${doc.id}`}
                        className="text-xs px-3 py-1 bg-primary-600 text-white rounded-full hover:bg-primary-700"
                      >
                        Analyze
                      </a>
                      <button
                        onClick={() => handleDelete(doc.id)}
                        className="text-xs px-3 py-1 bg-red-100 text-red-600 rounded-full hover:bg-red-200"
                      >
                        Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
