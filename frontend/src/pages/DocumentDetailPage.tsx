import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ArrowLeft, Loader2 } from 'lucide-react'
import { apiRequest } from '../api/client'
import { ExplainDrawer } from '../components/ExplainDrawer'
import { HighlightCard } from '../components/HighlightCard'
import type { DocumentItem, HighlightTrace } from '../types'

export function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const [doc, setDoc] = useState<DocumentItem | null>(null)
  const [highlights, setHighlights] = useState<HighlightTrace[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTrace, setActiveTrace] = useState<HighlightTrace | null>(null)

  const fetchDetail = async () => {
    if (!id) return
    const res = await apiRequest<{ document: DocumentItem; highlights: HighlightTrace[] }>(
      `/documents/${id}`
    )
    setDoc(res.document)
    setHighlights(res.highlights)
    setLoading(false)
  }

  useEffect(() => {
    void fetchDetail()
  }, [id])

  useEffect(() => {
    if (!doc || (doc.status !== 'pending' && doc.status !== 'processing')) return
    const timer = setInterval(() => {
      void fetchDetail()
    }, 2000)
    return () => clearInterval(timer)
  }, [doc])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16 text-sm text-slate-500">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
        <span>Đang tải chi tiết tài liệu...</span>
      </div>
    )
  }

  if (!doc) {
    return <div className="p-8 text-center text-sm text-slate-500">Không tìm thấy tài liệu.</div>
  }

  return (
    <div className="mx-auto max-w-5xl space-y-5 px-4 py-6">
      <Link
        to="/dashboard"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-slate-600 hover:text-indigo-600"
      >
        <ArrowLeft className="h-4 w-4" />
        <span>Quay lại kho tài liệu</span>
      </Link>

      <div className="rounded-xl border border-slate-200 bg-white p-5">
        <h1 className="text-lg font-bold text-slate-900">{doc.title}</h1>
        <p className="mt-1 text-xs text-slate-500">
          Trạng thái: <span className="font-semibold">{doc.status}</span> • Tiến độ:{' '}
          {doc.processed_pages}/{doc.total_pages} trang • Phát hiện{' '}
          <span className="font-semibold text-indigo-600">{highlights.length}</span> vùng highlight
        </p>
        {doc.error_message && (
          <p className="mt-2 rounded-lg bg-red-50 p-2.5 text-xs text-red-700">{doc.error_message}</p>
        )}
      </div>

      {(doc.status === 'pending' || doc.status === 'processing') && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 p-4 text-sm text-amber-800">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Hệ thống đang lọc màu highlight và chạy OCR Gemini... Trang sẽ tự động cập nhật.</span>
        </div>
      )}

      {doc.status === 'ready' && highlights.length === 0 ? (
        <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
          Không phát hiện vùng tô màu highlight nào trong tài liệu này. Hãy kiểm tra chất lượng ảnh hoặc độ tương phản màu tô.
        </div>
      ) : (
        <div className="space-y-3">
          {highlights.map((h) => (
            <HighlightCard
              key={h.id}
              pageNumber={h.page_number}
              color={h.highlight_color}
              extractedText={h.extracted_text}
              contextSnippet={h.context_snippet}
              onExplain={() => setActiveTrace(h)}
            />
          ))}
        </div>
      )}

      <ExplainDrawer
        traceId={activeTrace?.id || null}
        extractedText={activeTrace?.extracted_text || ''}
        onClose={() => setActiveTrace(null)}
      />
    </div>
  )
}
