'use client';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { analyzeDocument, type AnalysisResult } from '@/lib/api';

export default function AnalysisPage() {
  const params = useParams();
  const docId = params?.id as string;
  const [analysis, setAnalysis] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  async function handleAnalyze() {
    setLoading(true);
    setError('');
    try {
      const result = await analyzeDocument(docId);
      setAnalysis(result);
    } catch (err: any) {
      setError(err.message);
    }
    setLoading(false);
  }

  const severityColor: Record<string, string> = {
    low: 'bg-green-100 text-green-700',
    medium: 'bg-yellow-100 text-yellow-700',
    high: 'bg-orange-100 text-orange-700',
    critical: 'bg-red-100 text-red-700',
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Run Analysis'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-6 text-red-700">{error}</div>
      )}

      {loading && (
        <div className="text-center py-16">
          <div className="animate-spin w-8 h-8 border-2 border-primary-600 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-500">Analyzing document... This may take a minute.</p>
        </div>
      )}

      {analysis && (
        <div className="space-y-8">
          {/* Executive Summary */}
          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Executive Summary</h2>
            <div className="space-y-4">
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Overview</h3>
                <p className="text-gray-700">{analysis.executive_summary.company_overview}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-gray-500 mb-1">Financial Health</h3>
                <p className="text-gray-700">{analysis.executive_summary.financial_health}</p>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <h3 className="text-sm font-medium text-green-600 mb-1">Strengths</h3>
                  <ul className="text-sm text-gray-700 space-y-1">
                    {analysis.executive_summary.key_strengths.map((s, i) => (
                      <li key={i}>+ {s}</li>
                    ))}
                    {analysis.executive_summary.key_strengths.length === 0 && <li className="text-gray-400">None identified</li>}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-red-600 mb-1">Risks</h3>
                  <ul className="text-sm text-gray-700 space-y-1">
                    {analysis.executive_summary.key_risks.map((r, i) => (
                      <li key={i}>- {r}</li>
                    ))}
                    {analysis.executive_summary.key_risks.length === 0 && <li className="text-gray-400">None identified</li>}
                  </ul>
                </div>
                <div>
                  <h3 className="text-sm font-medium text-blue-600 mb-1">Opportunities</h3>
                  <ul className="text-sm text-gray-700 space-y-1">
                    {analysis.executive_summary.growth_opportunities.map((o, i) => (
                      <li key={i}>* {o}</li>
                    ))}
                    {analysis.executive_summary.growth_opportunities.length === 0 && <li className="text-gray-400">None identified</li>}
                  </ul>
                </div>
              </div>
              <div className="pt-3 border-t border-gray-100">
                <h3 className="text-sm font-medium text-gray-500 mb-1">Recommendation</h3>
                <p className="text-gray-700">{analysis.executive_summary.recommendation}</p>
                <div className="mt-2">
                  <span className="text-xs text-gray-400">Confidence: </span>
                  <span className="text-sm font-semibold text-gray-700">
                    {(analysis.executive_summary.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* Financial Metrics */}
          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Financial Metrics</h2>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {Object.entries(analysis.financial_metrics).filter(([k]) => k !== 'custom').map(([key, value]) => (
                <div key={key} className="bg-gray-50 rounded-lg p-3">
                  <div className="text-xs text-gray-500 mb-1">
                    {key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                  </div>
                  <div className="text-lg font-semibold text-gray-900">{value || '—'}</div>
                </div>
              ))}
            </div>
          </section>

          {/* Risks */}
          <section className="bg-white rounded-xl border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Risk Assessment ({analysis.risks.length} found)
            </h2>
            {analysis.risks.length === 0 ? (
              <p className="text-gray-500 text-sm">No risks identified.</p>
            ) : (
              <div className="space-y-4">
                {analysis.risks.map((risk, i) => (
                  <div key={i} className="border border-gray-100 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${severityColor[risk.severity] || ''}`}>
                        {risk.severity.toUpperCase()}
                      </span>
                      <span className="text-xs text-gray-400 uppercase">{risk.category}</span>
                      <span className="font-medium text-gray-900 ml-2">{risk.title}</span>
                    </div>
                    <p className="text-sm text-gray-600 mb-2">{risk.description}</p>
                    {risk.evidence.length > 0 && (
                      <div className="bg-gray-50 rounded p-2 mb-2">
                        <span className="text-xs text-gray-400">Evidence: </span>
                        {risk.evidence.map((e, j) => (
                          <span key={j} className="text-xs text-gray-600 italic">"{e.text}" </span>
                        ))}
                      </div>
                    )}
                    <p className="text-xs text-gray-500"><strong>Recommendation:</strong> {risk.recommendation}</p>
                  </div>
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
