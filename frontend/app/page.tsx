'use client'

import { useState, useEffect } from 'react'
import { Upload, Search, FileText, Loader2, Trash2, File as FileIcon } from 'lucide-react'

interface DocumentInfo {
  filename: string
  safe_filename: string
  page_count: number
  total_chunks: number
  upload_time: string
  file_size_mb: number
}

interface SearchResult {
  chunk_id: number
  page_num: number
  text: string
  similarity_score: number
  score_percentage: number
  filename: string
}

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [documents, setDocuments] = useState<DocumentInfo[]>([])
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch documents on load
  useEffect(() => {
    fetchDocuments()
  }, [])

  const fetchDocuments = async () => {
    try {
      const response = await fetch('http://127.0.0.1:8000/api/documents')
      if (response.ok) {
        const data = await response.json()
        setDocuments(data.documents)
      }
    } catch (err) {
      console.error('Failed to fetch documents', err)
    }
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
      setError(null)
    }
  }

  const handleUpload = async () => {
    if (!file) return

    setUploading(true)
    setError(null)

    const formData = new FormData()
    formData.append('file', file)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        throw new Error('Upload failed')
      }

      const data = await response.json()
      // Refresh list to include new doc
      setDocuments(prev => [...prev, data.document])
      setFile(null)
    } catch (err) {
      setError('Failed to upload PDF. Please try again.')
      console.error(err)
    } finally {
      setUploading(false)
    }
  }

  const handleClearDocuments = async () => {
    if (!confirm('Are you sure you want to delete all documents and clear the index?')) return

    try {
      await fetch('http://127.0.0.1:8000/api/documents', { method: 'DELETE' })
      setDocuments([])
      setSearchResults([])
      setSearchQuery('')
    } catch {
      setError('Failed to clear documents')
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim() || documents.length === 0) return

    setSearching(true)
    setError(null)

    try {
      const response = await fetch('http://127.0.0.1:8000/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: searchQuery,
          top_k: 20, // Increased for multi-doc
        }),
      })

      if (!response.ok) {
        throw new Error('Search failed')
      }

      const data = await response.json()
      setSearchResults(data.results)
    } catch (err) {
      setError('Search failed. Please try again.')
      console.error(err)
    } finally {
      setSearching(false)
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8">
      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Sidebar: Document Management */}
        <div className="lg:col-span-4 space-y-6">
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-slate-100">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <FileIcon className="w-5 h-5 text-blue-600" />
              Case Files
            </h2>

            {/* Upload Box */}
            <div className="border-2 border-dashed border-slate-200 rounded-xl p-6 text-center hover:border-blue-400 transition-colors bg-slate-50 mb-6">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              {!file ? (
                <label
                  htmlFor="file-upload"
                  className="cursor-pointer flex flex-col items-center gap-2"
                >
                  <Upload className="w-8 h-8 text-slate-400" />
                  <span className="text-sm font-medium text-slate-600">
                    Add PDF Document
                  </span>
                </label>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center gap-2 justify-center text-sm font-medium text-slate-700">
                    <FileText className="w-4 h-4" />
                    <span className="truncate max-w-[200px]">{file.name}</span>
                  </div>
                  <button
                    onClick={handleUpload}
                    disabled={uploading}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white text-sm font-semibold py-2 px-4 rounded-lg transition-colors flex items-center justify-center gap-2"
                  >
                    {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Process'}
                  </button>
                </div>
              )}
            </div>

            {/* Document List */}
            {documents.length > 0 ? (
              <div className="space-y-3">
                <div className="flex justify-between items-center text-xs text-slate-500 uppercase font-semibold tracking-wider">
                  <span>{documents.length} Documents</span>
                  <button 
                    onClick={handleClearDocuments}
                    className="text-red-500 hover:text-red-700 flex items-center gap-1"
                  >
                    <Trash2 className="w-3 h-3" /> Clear All
                  </button>
                </div>
                <div className="max-h-[500px] overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                  {documents.map((doc, idx) => (
                    <div key={idx} className="bg-white border border-slate-200 p-3 rounded-lg text-sm shadow-sm">
                      <div className="font-medium text-slate-800 truncate" title={doc.filename}>
                        {doc.filename}
                      </div>
                      <div className="flex justify-between mt-1 text-slate-500 text-xs">
                        <span>{doc.page_count} pages</span>
                        <span>{doc.file_size_mb} MB</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center text-slate-400 py-8 text-sm">
                No documents uploaded yet.
              </div>
            )}
            
            {error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Right Main Area: Search */}
        <div className="lg:col-span-8 space-y-6">
          {/* Header */}
          <div className="text-center lg:text-left mb-8">
            <h1 className="text-3xl font-bold text-slate-900">
              Evidence Search
            </h1>
            <p className="text-slate-600">
              Search across all uploaded case files instantly.
            </p>
          </div>

          {/* Search Bar */}
          <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-6 z-10 border border-slate-100">
            <div className="flex gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  disabled={documents.length === 0}
                  placeholder={documents.length === 0 ? "Upload documents to start searching..." : "Search e.g., \"weapon\", \"suspect description\"..."}
                  className="w-full pl-12 pr-4 py-4 border-2 border-slate-200 rounded-xl focus:border-blue-500 focus:outline-none text-lg disabled:bg-slate-50 disabled:text-slate-400 transition-colors"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={searching || !searchQuery.trim() || documents.length === 0}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed text-white font-semibold px-8 py-4 rounded-xl transition-colors flex items-center gap-2"
              >
                {searching ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  'Search'
                )}
              </button>
            </div>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 ? (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900 px-1">
                Found {searchResults.length} relevant matches
              </h3>
              {searchResults.map((result, index) => (
                <div
                  key={index}
                  className="bg-white border border-slate-200 rounded-xl p-6 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="bg-slate-100 text-slate-700 font-medium px-3 py-1 rounded-lg text-sm border border-slate-200">
                        {result.filename}
                      </span>
                      <span className="bg-blue-50 text-blue-700 font-medium px-3 py-1 rounded-lg text-sm border border-blue-100">
                        Page {result.page_num}
                      </span>
                    </div>
                    <span className="text-slate-400 text-xs font-mono">
                      {result.score_percentage.toFixed(1)}% Match
                    </span>
                  </div>
                  <p className="text-slate-700 leading-relaxed text-lg">
                    {result.text}
                  </p>
                </div>
              ))}
            </div>
          ) : (
            searching ? null : (
              <div className="flex flex-col items-center justify-center py-20 text-slate-400">
                <Search className="w-16 h-16 mb-4 opacity-20" />
                <p>Enter a query to search across your case files</p>
              </div>
            )
          )}
        </div>
      </div>
    </main>
  )
}
