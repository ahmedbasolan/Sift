'use client';
import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocument } from '@/lib/api';

export default function UploadPage() {
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<{ file: string; status: string; id?: string; error?: string }[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    setUploading(true);
    const newResults: typeof results = [];

    for (const file of acceptedFiles) {
      try {
        const result = await uploadDocument(file);
        newResults.push({ file: file.name, status: result.message, id: result.id });
      } catch (err: any) {
        newResults.push({ file: file.name, status: 'error', error: err.message });
      }
    }

    setResults((prev) => [...prev, ...newResults]);
    setUploading(false);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
      'text/markdown': ['.md'],
      'text/html': ['.html'],
    },
  });

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Upload Documents</h1>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition ${
          isDragActive ? 'border-primary-500 bg-primary-50' : 'border-gray-300 hover:border-primary-400'
        }`}
      >
        <input {...getInputProps()} />
        <div className="w-12 h-12 bg-primary-100 rounded-xl flex items-center justify-center mx-auto mb-4">
          <span className="text-2xl">📁</span>
        </div>
        {isDragActive ? (
          <p className="text-primary-600 font-medium">Drop files here...</p>
        ) : (
          <div>
            <p className="text-gray-700 font-medium">Drag & drop files here, or click to browse</p>
            <p className="text-sm text-gray-500 mt-1">PDF, PPTX, DOCX, XLSX, CSV, TXT, MD, HTML</p>
          </div>
        )}
      </div>

      {uploading && (
        <div className="mt-6 flex items-center gap-3 text-primary-600">
          <div className="animate-spin w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full" />
          <span className="text-sm">Processing documents...</span>
        </div>
      )}

      {results.length > 0 && (
        <div className="mt-8 space-y-3">
          <h2 className="text-lg font-semibold text-gray-900">Upload Results</h2>
          {results.map((r, i) => (
            <div
              key={i}
              className={`p-4 rounded-lg border ${
                r.error ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'
              }`}
            >
              <div className="flex items-center justify-between">
                <span className="font-medium text-gray-900">{r.file}</span>
                <span className={`text-sm ${r.error ? 'text-red-600' : 'text-green-600'}`}>
                  {r.error || r.status}
                </span>
              </div>
              {r.id && (
                <div className="mt-2 flex gap-2">
                  <a
                    href={`/analysis/${r.id}`}
                    className="text-xs px-3 py-1 bg-primary-600 text-white rounded-full hover:bg-primary-700"
                  >
                    Analyze
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
