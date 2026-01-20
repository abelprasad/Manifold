'use client'

import { useState, useEffect } from 'react'

const API_URL = 'http://127.0.0.1:8000'

interface Document {
  filename: string
  page_count: number
  file_size_mb: number
}

interface Result {
  text: string
  filename: string
  page_num: number
  score_percentage: number
  semantic_highlights?: { phrase: string; score: number }[]
}

interface Metrics {
  search_time_seconds: number
  total_pages_searched: number
  manual_review_hours: number
}

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([])
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Result[]>([])
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])

  useEffect(() => {
    fetch(`${API_URL}/api/documents`)
      .then(r => r.json())
      .then(d => setDocuments(d.documents || []))
      .catch(() => setError('Backend not running'))
  }, [])

  const loadDemo = async () => {
    setLoading(true)
    setError('')
    try {
      const r = await fetch(`${API_URL}/api/demo/load`, { method: 'POST' })
      const d = await r.json()
      setSuggestions(d.sample_queries || [])
      const docs = await fetch(`${API_URL}/api/documents`).then(r => r.json())
      setDocuments(docs.documents || [])
    } catch {
      setError('Failed to load demo')
    }
    setLoading(false)
  }

  const upload = async (file: File) => {
    setUploading(true)
    const form = new FormData()
    form.append('file', file)
    try {
      await fetch(`${API_URL}/api/upload`, { method: 'POST', body: form })
      const docs = await fetch(`${API_URL}/api/documents`).then(r => r.json())
      setDocuments(docs.documents || [])
    } catch {
      setError('Upload failed')
    }
    setUploading(false)
  }

  const search = async (q?: string) => {
    const searchQuery = q || query
    if (!searchQuery.trim()) return
    setQuery(searchQuery)
    setLoading(true)
    setError('')
    try {
      const r = await fetch(`${API_URL}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, top_k: 15 })
      })
      const d = await r.json()
      setResults(d.results || [])
      setMetrics(d.metrics || null)
    } catch {
      setError('Search failed')
    }
    setLoading(false)
  }

  const clear = async () => {
    await fetch(`${API_URL}/api/documents`, { method: 'DELETE' })
    setDocuments([])
    setResults([])
    setMetrics(null)
    setQuery('')
  }

  const exportCSV = async () => {
    const r = await fetch(`${API_URL}/api/export/csv`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 15 })
    })
    const blob = await r.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'results.csv'
    a.click()
  }

  const highlight = (text: string, highlights?: { phrase: string; score: number }[]) => {
    if (!highlights?.length) return text
    const sorted = [...highlights].sort((a, b) => b.phrase.length - a.phrase.length)
    const pattern = new RegExp(`(${sorted.map(h => h.phrase.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|')})`, 'gi')
    return text.split(pattern).map((part, i) => {
      const match = sorted.find(h => h.phrase.toLowerCase() === part.toLowerCase())
      return match ? <mark key={i} className="bg-amber-100 text-amber-900 px-1">{part}</mark> : part
    })
  }

  const totalPages = documents.reduce((s, d) => s + d.page_count, 0)

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-slate-900 border-b-4 border-amber-500">
        <div className="max-w-6xl mx-auto px-8 py-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            {/* Magnifying Glass Logo */}
            <svg className="w-9 h-9 text-amber-500" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="10" cy="10" r="6" />
              <path d="M14.5 14.5L20 20" strokeLinecap="round" />
              <text x="10" y="13" textAnchor="middle" fontSize="8" fontWeight="bold" fill="currentColor" stroke="none">M</text>
            </svg>
            <div>
              <h1 className="text-xl font-bold text-white tracking-tight">MANIFOLD</h1>
              <p className="text-xs text-slate-400 uppercase tracking-widest">Legal Document Intelligence</p>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-6xl mx-auto px-8 py-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10">

          {/* Sidebar */}
          <aside className="lg:col-span-4 space-y-6">
            {/* Upload */}
            <div className="bg-white border border-slate-200 shadow-sm">
              <div className="bg-slate-800 px-5 py-3">
                <h2 className="text-sm font-semibold text-white uppercase tracking-wide">Case Files</h2>
              </div>
              <div className="p-5">
                <label className="block border-2 border-dashed border-slate-300 p-6 text-center cursor-pointer hover:border-amber-500 hover:bg-amber-50/50 transition-all">
                  <input
                    type="file"
                    accept=".pdf"
                    className="hidden"
                    onChange={e => e.target.files?.[0] && upload(e.target.files[0])}
                    disabled={uploading}
                  />
                  <svg className="w-10 h-10 mx-auto mb-2 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  <span className="text-sm text-slate-600">
                    {uploading ? 'Processing...' : 'Upload Evidence'}
                  </span>
                </label>
              </div>
            </div>

            {/* Documents */}
            <div className="bg-white border border-slate-200 shadow-sm">
              <div className="bg-slate-800 px-5 py-3 flex items-center justify-between">
                <h2 className="text-sm font-semibold text-white uppercase tracking-wide">Evidence Index</h2>
                {documents.length > 0 && (
                  <button onClick={clear} className="text-xs text-slate-400 hover:text-red-400">Clear</button>
                )}
              </div>
              <div className="p-5">
                {documents.length === 0 ? (
                  <div className="text-center py-6">
                    <p className="text-sm text-slate-400 mb-4">No documents in case file</p>
                    <button
                      onClick={loadDemo}
                      disabled={loading}
                      className="text-sm font-medium text-amber-600 hover:text-amber-700 border border-amber-600 px-4 py-2 hover:bg-amber-50 transition-colors"
                    >
                      {loading ? 'Loading...' : 'Load Sample Case'}
                    </button>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {documents.map((d, i) => (
                      <div key={i} className="flex items-center gap-3 p-3 bg-slate-50 border-l-4 border-slate-800">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-slate-800 truncate">{d.filename}</p>
                          <p className="text-xs text-slate-500">{d.page_count} pages</p>
                        </div>
                      </div>
                    ))}
                    <div className="pt-3 mt-3 border-t border-slate-200">
                      <p className="text-xs text-slate-500 font-medium">{totalPages} pages indexed</p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {error && (
              <div className="p-4 bg-red-50 border-l-4 border-red-500">
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </aside>

          {/* Main */}
          <main className="lg:col-span-8 space-y-6">
            {/* Search */}
            <div className="bg-white border border-slate-200 shadow-sm">
              <div className="bg-slate-800 px-5 py-3">
                <h2 className="text-sm font-semibold text-white uppercase tracking-wide">Discovery Search</h2>
              </div>
              <div className="p-5">
                <div className="flex gap-3">
                  <input
                    type="text"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && search()}
                    placeholder={documents.length ? 'Search witness statements, evidence, testimony...' : 'Load case files to begin'}
                    disabled={!documents.length}
                    className="flex-1 px-4 py-3 border border-slate-300 text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-800 focus:ring-1 focus:ring-slate-800 disabled:bg-slate-100 disabled:text-slate-400"
                  />
                  <button
                    onClick={() => search()}
                    disabled={loading || !query.trim() || !documents.length}
                    className="px-6 py-3 bg-slate-800 text-white text-sm font-semibold uppercase tracking-wide hover:bg-slate-700 disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors"
                  >
                    {loading ? '...' : 'Search'}
                  </button>
                </div>

                {/* Suggestions */}
                {suggestions.length > 0 && !results.length && (
                  <div className="mt-4 flex flex-wrap items-center gap-2">
                    <span className="text-xs text-slate-500 uppercase tracking-wide">Suggested:</span>
                    {suggestions.slice(0, 4).map(s => (
                      <button
                        key={s}
                        onClick={() => search(s)}
                        className="text-xs text-slate-600 px-3 py-1.5 bg-slate-100 border border-slate-200 hover:border-amber-500 hover:text-amber-700 transition-colors"
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Metrics */}
            {metrics && (
              <div className="bg-slate-800 text-white px-5 py-4 flex flex-wrap items-center gap-x-8 gap-y-2">
                <div>
                  <span className="text-2xl font-bold text-amber-400">{metrics.total_pages_searched}</span>
                  <span className="text-sm text-slate-400 ml-2">pages analyzed</span>
                </div>
                <div>
                  <span className="text-2xl font-bold text-amber-400">{metrics.search_time_seconds}s</span>
                  <span className="text-sm text-slate-400 ml-2">search time</span>
                </div>
                <div>
                  <span className="text-sm text-slate-400">Est. manual review:</span>
                  <span className="text-sm text-white ml-1">{metrics.manual_review_hours}+ hours</span>
                </div>
                {results.length > 0 && (
                  <button onClick={exportCSV} className="ml-auto text-sm text-amber-400 hover:text-amber-300 font-medium">
                    Export Results
                  </button>
                )}
              </div>
            )}

            {/* Results */}
            {results.length > 0 ? (
              <div className="space-y-4">
                <p className="text-sm font-semibold text-slate-600 uppercase tracking-wide">{results.length} Relevant Passages Found</p>
                {results.map((r, i) => (
                  <div key={i} className="bg-white border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
                    <div className="bg-slate-50 px-5 py-3 border-b border-slate-200 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <span className="text-sm font-semibold text-slate-800">{r.filename}</span>
                        <span className="text-sm text-slate-500">Page {r.page_num}</span>
                      </div>
                      <span className="text-xs font-bold text-amber-600 bg-amber-50 px-2 py-1 border border-amber-200">
                        {r.score_percentage.toFixed(0)}% MATCH
                      </span>
                    </div>
                    <div className="p-5">
                      <p className="text-slate-700 leading-relaxed">
                        {highlight(r.text, r.semantic_highlights)}
                      </p>
                      {r.semantic_highlights && r.semantic_highlights.length > 0 && (
                        <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap gap-2">
                          <span className="text-xs text-slate-400 uppercase tracking-wide">Key Terms:</span>
                          {r.semantic_highlights.slice(0, 4).map((h, j) => (
                            <span key={j} className="text-xs text-slate-600 bg-slate-100 px-2 py-1">
                              {h.phrase}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : !loading && documents.length > 0 ? (
              <div className="text-center py-20 bg-white border border-slate-200">
                <svg className="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <p className="text-slate-500 font-medium">Search the evidence</p>
                <p className="text-sm text-slate-400 mt-1">Find relevant passages using natural language queries</p>
              </div>
            ) : !loading && (
              <div className="text-center py-20 bg-white border border-slate-200">
                <svg className="w-16 h-16 mx-auto mb-4 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="text-slate-500 font-medium">No case files loaded</p>
                <p className="text-sm text-slate-400 mt-1">Upload documents or load a sample case to begin</p>
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-slate-200 mt-16">
        <div className="max-w-6xl mx-auto px-8 py-6">
          <p className="text-xs text-slate-400 text-center uppercase tracking-wide">
            Manifold Legal Document Intelligence System
          </p>
        </div>
      </footer>
    </div>
  )
}
