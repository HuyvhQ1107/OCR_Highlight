import React, { useEffect, useState } from 'react'
import { Clock, Search } from 'lucide-react'
import { apiRequest } from '../api/client'
import { ExplainDrawer } from '../components/ExplainDrawer'
import { HighlightCard } from '../components/HighlightCard'
import type { SearchHistoryItem, SearchResultItem } from '../types'

export function SearchPage() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<SearchResultItem[]>([])
  const [latencyMs, setLatencyMs] = useState<number | null>(null)
  const [history, setHistory] = useState<SearchHistoryItem[]>([])
  const [searching, setSearching] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [activeTrace, setActiveTrace] = useState<SearchResultItem | null>(null)

  const loadHistory = async () => {
    const res = await apiRequest<{ items: SearchHistoryItem[] }>('/search/history')
    setHistory(res.items)
  }

  useEffect(() => {
    void loadHistory()
  }, [])

  const runSearch = async (searchText: string) => {
    if (!searchText.trim()) return
    setSearching(true)
    setHasSearched(true)
    try {
      const res = await apiRequest<{
        query: string
        latency_ms: number
        results: SearchResultItem[]
      }>('/search', {
        method: 'POST',
        body: JSON.stringify({ query: searchText.trim(), limit: 15 }),
      })
      setResults(res.results)
      setLatencyMs(res.latency_ms)
      void loadHistory()
    } finally {
      setSearching(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    void runSearch(query)
  }

  return (
    <div className="mx-auto grid max-w-6xl gap-6 px-4 py-6 lg:grid-cols-4">
      <div className="space-y-5 lg:col-span-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Tìm kiếm Dấu Vết Tri Thức</h1>
          <p className="text-sm text-slate-500">
            Hỗ trợ tìm theo từ khóa chính xác hoặc mô tả ý nhớ mang máng (Semantic Search).
          </p>
        </div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Nhập từ khóa hoặc nội dung bạn nhớ đã highlight..."
              className="w-full rounded-xl border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm focus:border-indigo-500 focus:outline-none"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="rounded-xl bg-indigo-600 px-5 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
          >
            {searching ? 'Đang tìm...' : 'Tìm kiếm'}
          </button>
        </form>

        {latencyMs !== null && (
          <p className="text-xs text-slate-500">
            Tìm thấy <span className="font-semibold">{results.length}</span> kết quả trong{' '}
            <span className="font-semibold">{latencyMs} ms</span>
          </p>
        )}

        {hasSearched && results.length === 0 && !searching ? (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
            Không tìm thấy nội dung khớp trong các vùng highlight của bạn. Thử từ khóa khác ngắn gọn hơn.
          </div>
        ) : (
          <div className="space-y-3">
            {results.map((r) => (
              <HighlightCard
                key={r.trace_id}
                pageNumber={r.page_number}
                color={r.highlight_color}
                extractedText={r.extracted_text}
                contextSnippet={r.context_snippet}
                documentTitle={r.document_title}
                onExplain={() => setActiveTrace(r)}
              />
            ))}
          </div>
        )}
      </div>

      <aside className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="mb-3 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
          <Clock className="h-4 w-4 text-indigo-600" />
          <span>Lịch sử tra cứu</span>
        </h2>
        {history.length === 0 ? (
          <p className="text-xs text-slate-500">Chưa có lịch sử tìm kiếm.</p>
        ) : (
          <div className="space-y-2">
            {history.map((h) => (
              <button
                key={h.id}
                onClick={() => {
                  setQuery(h.query_text)
                  void runSearch(h.query_text)
                }}
                className="block w-full rounded-lg border border-slate-100 p-2 text-left text-xs hover:bg-slate-50"
              >
                <p className="truncate font-medium text-slate-800">{h.query_text}</p>
                <p className="mt-0.5 text-[11px] text-slate-400">{h.result_count} kết quả</p>
              </button>
            ))}
          </div>
        )}
      </aside>

      <ExplainDrawer
        traceId={activeTrace?.trace_id || null}
        extractedText={activeTrace?.extracted_text || ''}
        onClose={() => setActiveTrace(null)}
      />
    </div>
  )
}
