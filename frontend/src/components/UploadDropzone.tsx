import React, { useRef, useState } from 'react'
import { UploadCloud } from 'lucide-react'
import { apiRequest } from '../api/client'
import type { DocumentItem } from '../types'

interface UploadDropzoneProps {
  onUploaded: (doc: DocumentItem) => void
}

const MAX_BYTES = 20 * 1024 * 1024
const ALLOWED_EXT = ['pdf', 'png', 'jpg', 'jpeg']

export function UploadDropzone({ onUploaded }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFile = async (file: File) => {
    setError(null)
    const ext = file.name.split('.').pop()?.toLowerCase() || ''
    if (!ALLOWED_EXT.includes(ext)) {
      setError('Chỉ hỗ trợ định dạng .pdf, .png, .jpg, .jpeg.')
      return
    }
    if (file.size > MAX_BYTES) {
      setError('Dung lượng tệp vượt quá giới hạn 20 MB.')
      return
    }

    const formData = new FormData()
    formData.append('file', file)

    setUploading(true)
    try {
      const doc = await apiRequest<DocumentItem>('/documents/upload', {
        method: 'POST',
        body: formData,
      })
      onUploaded(doc)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Tải lên thất bại.')
    } finally {
      setUploading(false)
    }
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files?.[0]
    if (file) void handleFile(file)
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragging(true)
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
      className={`cursor-pointer rounded-xl border-2 border-dashed p-6 text-center transition ${
        dragging
          ? 'border-indigo-500 bg-indigo-50'
          : 'border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50'
      }`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.png,.jpg,.jpeg"
        className="hidden"
        onChange={(e) => {
          const file = e.target.files?.[0]
          if (file) void handleFile(file)
          e.target.value = ''
        }}
      />
      <UploadCloud className="mx-auto mb-2 h-8 w-8 text-indigo-600" />
      <p className="text-sm font-medium text-slate-800">
        {uploading ? 'Đang tải lên tài liệu...' : 'Kéo thả hoặc nhấn để tải lên PDF / Ảnh đã tô màu highlight'}
      </p>
      <p className="mt-1 text-xs text-slate-500">
        Hỗ trợ .pdf, .png, .jpg, .jpeg • Tối đa 20 MB (≤ 100 trang PDF / ≤ 50 trang scan)
      </p>
      {error && <p className="mt-2 text-xs font-medium text-red-600">{error}</p>}
    </div>
  )
}
