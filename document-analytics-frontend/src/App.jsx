import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button.jsx'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card.jsx'
import { Input } from '@/components/ui/input.jsx'
import { Label } from '@/components/ui/label.jsx'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs.jsx'
import { Badge } from '@/components/ui/badge.jsx'
import { Progress } from '@/components/ui/progress.jsx'
import { Upload, Search, FileText, BarChart3, Clock, Database, Filter, ChevronLeft, ChevronRight } from 'lucide-react'
import './App.css'

const API_BASE_URL = 'http://localhost:5000/api'

// Component for displaying match contexts with navigation
function MatchContextViewer({ matchContexts, totalMatches }) {
  const [currentMatchIndex, setCurrentMatchIndex] = useState(0)

  if (!matchContexts || matchContexts.length === 0) {
    return null
  }

  const currentMatch = matchContexts[currentMatchIndex]

  const goToPrevious = () => {
    setCurrentMatchIndex(prev => prev > 0 ? prev - 1 : matchContexts.length - 1)
  }

  const goToNext = () => {
    setCurrentMatchIndex(prev => prev < matchContexts.length - 1 ? prev + 1 : 0)
  }

  return (
    <div className="mt-3 border rounded-lg bg-white shadow-sm">
      {/* Navigation header */}
      <div className="match-navigation flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2">
          <span className="match-counter text-sm">
            Match {currentMatchIndex + 1} of {totalMatches}
          </span>
          <Badge variant="outline" className="line-badge text-xs">
            Line {currentMatch.line_number}
          </Badge>
        </div>

        {totalMatches > 1 && (
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={goToPrevious}
              className="h-8 w-8 p-0 hover:bg-blue-50"
              title="Previous match"
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={goToNext}
              className="h-8 w-8 p-0 hover:bg-blue-50"
              title="Next match"
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      {/* Context content */}
      <div className="p-4">
        <div
          className="match-context text-sm bg-gray-50 p-4 rounded-lg border search-content"
          dangerouslySetInnerHTML={{ __html: currentMatch.context }}
        />
        <div className="mt-3 text-xs text-gray-500 flex items-center gap-2">
          <span>Lines {currentMatch.context_start_line}-{currentMatch.context_end_line}</span>
          <span>•</span>
          <span>Term: "{currentMatch.term}"</span>
        </div>
      </div>
    </div>
  )
}

function App() {
  const [documents, setDocuments] = useState([])
  const [searchResults, setSearchResults] = useState([])
  const [statistics, setStatistics] = useState({})
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [sortBy, setSortBy] = useState('upload_date')
  const [sortOrder, setSortOrder] = useState('desc')
  const [apiStatus, setApiStatus] = useState('unknown') // 'connected', 'disconnected', 'unknown'
  const [errorMessage, setErrorMessage] = useState('')

  useEffect(() => {
    fetchDocuments()
    fetchStatistics()
  }, [sortBy, sortOrder])

  const fetchDocuments = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/documents?sort_by=${sortBy}&sort_order=${sortOrder}`)
      const data = await response.json()
      setDocuments(data.documents || [])
    } catch (error) {
      console.error('Error fetching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/statistics`)
      const data = await response.json()
      setStatistics(data)
    } catch (error) {
      console.error('Error fetching statistics:', error)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData
      })
      
      if (response.ok) {
        await fetchDocuments()
        await fetchStatistics()
        event.target.value = '' // Reset file input
      } else {
        const error = await response.json()
        alert(`Upload failed: ${error.error}`)
      }
    } catch (error) {
      console.error('Error uploading file:', error)
      alert('Upload failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      setSearchResults([])
      return
    }

    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ keywords: searchQuery })
      })
      
      const data = await response.json()
      setSearchResults(data.documents || [])
    } catch (error) {
      console.error('Error searching documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleClassifyAll = async () => {
    try {
      setLoading(true)
      const response = await fetch(`${API_BASE_URL}/classify`, {
        method: 'POST'
      })
      
      if (response.ok) {
        await fetchDocuments()
        await fetchStatistics()
        alert('Documents classified successfully!')
      }
    } catch (error) {
      console.error('Error classifying documents:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString()
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto p-6">
        <div className="mb-8 text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Document Analytics Service
          </h1>
          <p className="text-lg text-gray-600">
            Upload, search, sort, and classify your documents with AI-powered analytics
          </p>
        </div>

        <Tabs defaultValue="upload" className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="upload" className="flex items-center gap-2">
              <Upload className="w-4 h-4" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="search" className="flex items-center gap-2">
              <Search className="w-4 h-4" />
              Search
            </TabsTrigger>
            <TabsTrigger value="documents" className="flex items-center gap-2">
              <FileText className="w-4 h-4" />
              Documents
            </TabsTrigger>
            <TabsTrigger value="analytics" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Analytics
            </TabsTrigger>
          </TabsList>

          <TabsContent value="upload">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="w-5 h-5" />
                  Upload Documents
                </CardTitle>
                <CardDescription>
                  Upload PDF or DOCX files for processing and analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid w-full max-w-sm items-center gap-1.5">
                  <Label htmlFor="file">Choose File</Label>
                  <Input
                    id="file"
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleFileUpload}
                    disabled={loading}
                  />
                </div>
                {loading && (
                  <div className="flex items-center gap-2">
                    <Progress value={50} className="w-full" />
                    <span className="text-sm text-gray-600">Processing...</span>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="search">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Search className="w-5 h-5" />
                  Search Documents
                </CardTitle>
                <CardDescription>
                  Search through your documents using keywords
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <Input
                      placeholder="Enter keywords, phrases, or sentences to search..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                    />
                    <Button onClick={handleSearch} disabled={loading}>
                      <Search className="w-4 h-4 mr-2" />
                      Search
                    </Button>
                  </div>
                  <p className="text-xs text-gray-500">
                    💡 Tip: Use exact phrases for precise matches, or individual words for broader results
                  </p>
                </div>
                
                {searchResults.length > 0 && (
                  <div className="space-y-4">
                    <h3 className="text-lg font-semibold">Search Results ({searchResults.length})</h3>
                    {searchResults.map((doc) => (
                      <Card key={doc.id} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex justify-between items-start mb-2">
                            <h4 className="font-semibold text-lg">{doc.title}</h4>
                            <div className="flex items-center gap-2">
                              <Badge variant="secondary">{doc.classification}</Badge>
                              {doc.total_matches > 0 && (
                                <Badge variant="outline" className="text-xs">
                                  {doc.total_matches} match{doc.total_matches > 1 ? 'es' : ''}
                                </Badge>
                              )}
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{doc.filename}</p>

                          {/* Match type indicator */}
                          {doc.match_type && (
                            <div className="mb-3 flex items-center gap-2">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${
                                doc.match_type === 'exact_phrase'
                                  ? 'bg-green-100 text-green-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}>
                                {doc.match_type === 'exact_phrase' ? 'Exact phrase' : 'Individual words'}
                              </span>
                              {doc.matched_terms && (
                                <span className="text-xs text-gray-600">
                                  Found: {doc.matched_terms.join(', ')}
                                </span>
                              )}
                            </div>
                          )}

                          {/* Context viewer for matches */}
                          {doc.match_contexts && doc.match_contexts.length > 0 ? (
                            <MatchContextViewer
                              matchContexts={doc.match_contexts}
                              totalMatches={doc.total_matches || doc.match_contexts.length}
                            />
                          ) : (
                            /* Fallback to old content display */
                            doc.highlighted_content && (
                              <div className="text-sm bg-gray-50 p-3 rounded border max-h-32 overflow-y-auto search-results">
                                <div
                                  className="search-content"
                                  dangerouslySetInnerHTML={{
                                    __html: doc.highlighted_content.length > 500
                                      ? doc.highlighted_content.substring(0, 500) + '...'
                                      : doc.highlighted_content
                                  }}
                                />
                              </div>
                            )
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="documents">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  Document Library
                </CardTitle>
                <CardDescription>
                  View and manage your uploaded documents
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex gap-4 items-center">
                  <div className="flex items-center gap-2">
                    <Filter className="w-4 h-4" />
                    <Label>Sort by:</Label>
                    <select 
                      value={sortBy} 
                      onChange={(e) => setSortBy(e.target.value)}
                      className="border rounded px-2 py-1"
                    >
                      <option value="upload_date">Upload Date</option>
                      <option value="title">Title</option>
                      <option value="file_size">File Size</option>
                    </select>
                    <select 
                      value={sortOrder} 
                      onChange={(e) => setSortOrder(e.target.value)}
                      className="border rounded px-2 py-1"
                    >
                      <option value="desc">Descending</option>
                      <option value="asc">Ascending</option>
                    </select>
                  </div>
                  <Button onClick={handleClassifyAll} variant="outline" disabled={loading}>
                    Classify All Documents
                  </Button>
                </div>

                <div className="grid gap-4">
                  {documents.map((doc) => (
                    <Card key={doc.id} className="hover:shadow-md transition-shadow">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <h4 className="font-semibold text-lg mb-1">{doc.title}</h4>
                            <p className="text-sm text-gray-600 mb-2">{doc.filename}</p>
                            <div className="flex gap-4 text-sm text-gray-500">
                              <span>Size: {formatFileSize(doc.file_size)}</span>
                              <span>Uploaded: {formatDate(doc.upload_date)}</span>
                              {doc.author && <span>Author: {doc.author}</span>}
                            </div>
                          </div>
                          <div className="flex flex-col items-end gap-2">
                            <Badge variant={doc.classification ? "default" : "secondary"}>
                              {doc.classification || "Unclassified"}
                            </Badge>
                            {doc.classification_confidence && (
                              <span className="text-xs text-gray-500">
                                {Math.round(doc.classification_confidence * 100)}% confidence
                              </span>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="analytics">
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Documents</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{statistics.total_documents || 0}</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Storage</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{statistics.total_size_mb || 0} MB</div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Avg Search Time</CardTitle>
                  <Clock className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{statistics.average_search_time || 0}s</div>
                </CardContent>
              </Card>

              <Card className="md:col-span-2 lg:col-span-3">
                <CardHeader>
                  <CardTitle>Document Classification Distribution</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {statistics.classification_distribution && Object.entries(statistics.classification_distribution).map(([category, count]) => (
                      <div key={category} className="flex items-center justify-between">
                        <span className="text-sm font-medium">{category}</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${(count / (statistics.total_documents || 1)) * 100}%` }}
                            ></div>
                          </div>
                          <span className="text-sm text-gray-600">{count}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App
