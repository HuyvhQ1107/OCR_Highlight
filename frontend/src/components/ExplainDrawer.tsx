import { useEffect, useState } from 'react'
import { Link2, Loader2, X } from 'lucide-react'
import { apiRequest } from '../api/client'
import type { ExplanationResponse, RelatedTraceItem, RelatedTracesResponse } from '../types'

interface ExplainDrawerProps {
  traceId: string | null
  extractedText: string
  onClose: () => void
}

const MODES: Array<{ key: 'basic' | 'deep' | 'example' | 'summary'; label: string }> = [
  { key: 'basic', label: 'Cơ bản' },
  { key: 'deep', label: 'Chuyên sâu' },
  { key: 'example', label: 'Ví dụ minh họa' },
  { key: 'summary', label: 'Tóm tắt' },
]

export function ExplainDrawer({ traceId, extractedText, onClose }: ExplainDrawerProps) {
  const [mode, setMode] = useState<'basic' | 'deep' | 'example' | 'summary'>('basic')
  const [content, setContent] = useState<string>('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [related, setRelated] = useState<RelatedTraceItem[]>([])

  useEffect(() => {
    if (!traceId) return
    let cancelled = false
    setLoading(true)
    setError(null)

    apiRequest<ExplanationResponse>(`/traces/${traceId}/explain`, {
      method: 'POST',
      body: JSON.stringify({ mode }),
    })
      .then((res) => {
        if (!cancelled) setContent(res.content)
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : 'Lỗi tải giải thích.')
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [traceId, mode])

  useEffect(() => {
    if (!traceId) return
    apiRequest<RelatedTracesResponse>(`/traces/${traceId}/related`)
      .then((res) => setRelated(res.related_traces))
      .catch(() => setRelated([]))
  }, [traceId])

  if (!traceId) return null

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/40">
      <div className="flex h-full w-full max-w-lg flex-col bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
          <h2 className="text-base font-semibold text-slate-900">AI Giải thích theo ngữ cảnh</h2>
          <button onClick={onClose} className="rounded-lg p-1 text-slate-500 hover:bg-slate-100">
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-5">
          <div className="mb-4 rounded-lg border-l-4 border-amber-400 bg-amber-50 p-3 text-sm font-medium text-slate-800">
            {extractedText}
          </div>

          <div className="mb-4 flex flex-wrap gap-1.5">
            {MODES.map((m) => (
              <button
                key={m.key}
                onClick={() => setMode(m.key)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  mode === m.key
                    ? 'bg-indigo-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {m.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
              <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
              <span>Gemini đang phân tích ngữ cảnh...</span>
            </div>
          ) : error ? (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>
          ) : (
            <div className="whitespace-pre-wrap rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm leading-relaxed text-slate-800">
              {content}
            </div>
          )}

          <div className="mt-6 border-t border-slate-200 pt-4">
            <h3 className="mb-2 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
              <Link2 className="h-4 w-4 text-indigo-600" />
              <span>Khái niệm liên quan</span>
            </h3>
            {related.length === 0 ? (
              <p className="text-xs text-slate-500">Chưa tìm thấy vùng highlight liên quan nào khác.</p>
            ) : (
              <div className="space-y-2">
                {related.map((item) => (
                  <div key={item.trace_id} className="rounded-lg border border-slate-200 p-2.5 text-xs">
                    <div className="mb-1 flex justify-between font-medium text-indigo-700">
                      <span>{item.document_title} • Trang {item.page_number}</span>
                      <span>{(item.similarity_score * 100).toFixed(0)}%</span>
                    </div>
                    <p className="text-slate-700">{item.extracted_text}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
