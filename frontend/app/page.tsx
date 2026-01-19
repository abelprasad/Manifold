'use client'

import { useState } from 'react'
import { Upload, Search, FileText, Loader2 } from 'lucide-react'

export default function Home() {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [documentInfo, setDocumentInfo] = useState<any>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<any[]>([])
  const [searching, setSearching] = useState(false)
  const [error, setError] = useState<string | null>(null)

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
      setDocumentInfo(data.document)
      setSearchResults([])
    } catch (err) {
      setError('Failed to upload PDF. Please try again.')
      console.error(err)
    } finally {
      setUploading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim() || !documentInfo) return

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
          top_k: 10,
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
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-slate-900 mb-3">
            Public Defender Evidence Search
          </h1>
          <p className="text-slate-600 text-lg">
            AI-powered semantic search for legal discovery documents
          </p>
        </div>

        {/* Upload Section */}
        {!documentInfo && (
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-8">
            <div className="flex items-center gap-3 mb-6">
              <Upload className="w-6 h-6 text-blue-600" />
              <h2 className="text-2xl font-semibold text-slate-900">
                Upload Discovery Document
              </h2>
            </div>

            <div className="border-2 border-dashed border-slate-300 rounded-xl p-12 text-center hover:border-blue-400 transition-colors">
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label
                htmlFor="file-upload"
                className="cursor-pointer flex flex-col items-center gap-4"
              >
                <FileText className="w-16 h-16 text-slate-400" />
                <div>
                  <p className="text-lg font-medium text-slate-700 mb-1">
                    {file ? file.name : 'Click to select PDF file'}
                  </p>
                  <p className="text-sm text-slate-500">
                    Upload discovery documents up to 500 pages
                  </p>
                </div>
              </label>
            </div>

            {file && (
              <button
                onClick={handleUpload}
                disabled={uploading}
                className="mt-6 w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold py-4 px-6 rounded-xl transition-colors flex items-center justify-center gap-2"
              >
                {uploading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Processing PDF...
                  </>
                ) : (
                  <>
                    <Upload className="w-5 h-5" />
                    Upload and Process
                  </>
                )}
              </button>
            )}

            {error && (
              <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                {error}
              </div>
            )}
          </div>
        )}

        {/* Document Info & Search Section */}
        {documentInfo && (
          <div className="space-y-8">
            {/* Document Info Card */}
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2">
                    {documentInfo.filename}
                  </h3>
                  <div className="flex gap-4 text-sm text-slate-600">
                    <span>{documentInfo.page_count} pages</span>
                    <span>•</span>
                    <span>{documentInfo.total_chunks} searchable chunks</span>
                    <span>•</span>
                    <span>{documentInfo.file_size_mb} MB</span>
                  </div>
                </div>
                <button
                  onClick={() => {
                    setDocumentInfo(null)
                    setFile(null)
                    setSearchResults([])
                    setSearchQuery('')
                  }}
                  className="text-slate-500 hover:text-slate-700 px-4 py-2 rounded-lg hover:bg-slate-100 transition-colors"
                >
                  Upload New Document
                </button>
              </div>
            </div>

            {/* Search Bar */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <div className="flex items-center gap-3 mb-6">
                <Search className="w-6 h-6 text-blue-600" />
                <h2 className="text-2xl font-semibold text-slate-900">
                  Search Evidence
                </h2>
              </div>

              <div className="flex gap-4">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder='e.g., "murder weapon", "surveillance footage", "witness testimony"'
                  className="flex-1 px-6 py-4 border-2 border-slate-200 rounded-xl focus:border-blue-500 focus:outline-none text-lg"
                />
                <button
                  onClick={handleSearch}
                  disabled={searching || !searchQuery.trim()}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-semibold px-8 py-4 rounded-xl transition-colors flex items-center gap-2 whitespace-nowrap"
                >
                  {searching ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Searching...
                    </>
                  ) : (
                    <>
                      <Search className="w-5 h-5" />
                      Search
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div className="bg-white rounded-2xl shadow-lg p-8">
                <h3 className="text-xl font-semibold text-slate-900 mb-6">
                  Found {searchResults.length} Results
                </h3>

                <div className="space-y-4">
                  {searchResults.map((result, index) => (
                    <div
                      key={index}
                      className="border-2 border-slate-200 rounded-xl p-6 hover:border-blue-300 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <span className="bg-blue-100 text-blue-700 font-semibold px-3 py-1 rounded-lg text-sm">
                            Page {result.page_num}
                          </span>
                          <span className="text-slate-600 text-sm">
                            Relevance: {result.score_percentage.toFixed(1)}%
                          </span>
                        </div>
                      </div>
                      <p className="text-slate-700 leading-relaxed">
                        {result.text}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </main>
  )
}