import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileText, Loader2, Trash2 } from 'lucide-react'
import { apiRequest } from '../api/client'
import { UploadDropzone } from '../components/UploadDropzone'
import type { DocumentItem } from '../types'

const STATUS_LABEL: Record<string, { text: string; cls: string }> = {
  pending: { text: 'Đang chờ', cls: 'bg-slate-100 text-slate-700' },
  processing: { text: 'Đang OCR', cls: 'bg-amber-100 text-amber-800' },
  ready: { text: 'Sẵn sàng', cls: 'bg-emerald-100 text-emerald-800' },
  failed: { text: 'Lỗi', cls: 'bg-red-100 text-red-700' },
}

export function DashboardPage() {
  const [documents, setDocuments] = useState<DocumentItem[]>([])
  const [loading, setLoading] = useState(true)

  const loadDocs = async () => {
    try {
      const res = await apiRequest<{ items: DocumentItem[] }>('/documents')
      setDocuments(res.items)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void loadDocs()
  }, [])

  // Poll while any document is pending or processing
  useEffect(() => {
    const hasActive = documents.some((d) => d.status === 'pending' || d.status === 'processing')
    if (!hasActive) return
    const timer = setInterval(() => {
      void loadDocs()
    }, 2500)
    return () => clearInterval(timer)
  }, [documents])

  const handleDelete = async (id: string) => {
    if (!confirm('Bạn có chắc muốn xóa tài liệu này cùng toàn bộ vùng highlight?')) return
    await apiRequest(`/documents/${id}`, { method: 'DELETE' })
    setDocuments((prev) => prev.filter((d) => d.id !== id))
  }

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-4 py-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Kho tài liệu cá nhân</h1>
        <p className="text-sm text-slate-500">
          Tải lên PDF hoặc ảnh đã tô màu highlight để hệ thống tự động trích xuất dấu vết tri thức.
        </p>
      </div>

      <UploadDropzone
        onUploaded={(doc) => setDocuments((prev) => [doc, ...prev])}
      />

      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-slate-700">
          Tài liệu của bạn ({documents.length})
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 py-8 text-sm text-slate-500">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Đang tải danh sách...</span>
          </div>
        ) : documents.length === 0 ? (
          <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
            Chưa có tài liệu nào. Hãy tải lên file PDF hoặc ảnh đầu tiên ở trên.
          </div>
        ) : (
          <div className="space-y-2.5">
            {documents.map((doc) => {
              const badge = STATUS_LABEL[doc.status] || STATUS_LABEL.pending
              return (
                <div
                  key={doc.id}
                  className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-4 shadow-xs"
                >
                  <Link
                    to={`/documents/${doc.id}`}
                    className="flex min-w-0 flex-1 items-center gap-3 hover:opacity-80"
                  >
                    <div className="rounded-lg bg-indigo-50 p-2 text-indigo-600">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate text-sm font-semibold text-slate-900">{doc.title}</p>
                      <p className="text-xs text-slate-500">
                        {doc.file_type.toUpperCase()} • {doc.total_pages} trang •{' '}
                        {(doc.file_size_bytes / 1024 / 1024).toFixed(2)} MB
                        {(doc.status === 'processing' || doc.status === 'pending') &&
                          ` • Đã xử lý ${doc.processed_pages}/${doc.total_pages}`}
                      </p>
                    </div>
                  </Link>

                  <div className="ml-4 flex items-center gap-2">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${badge.cls}`}>
                      {badge.text}
                    </span>
                    <button
                      onClick={() => void handleDelete(doc.id)}
                      title="Xóa tài liệu"
                      className="rounded-lg p-1.5 text-slate-400 hover:bg-red-50 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
