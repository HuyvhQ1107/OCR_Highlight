import { useEffect, useState } from 'react'
import { Loader2, Sparkles } from 'lucide-react'
import { apiRequest } from '../api/client'
import { HighlightCard } from '../components/HighlightCard'
import { StudyPlayer } from '../components/StudyPlayer'
import type { DocumentItem, HighlightTrace, StudyMaterialItem } from '../types'

export function StudyPage() {
  const [docs, setDocs] = useState<DocumentItem[]>([])
  const [selectedDocId, setSelectedDocId] = useState<string>('')
  const [traces, setTraces] = useState<HighlightTrace[]>([])
  const [selectedTraceIds, setSelectedTraceIds] = useState<string[]>([])
  const [materialType, setMaterialType] = useState<'flashcard' | 'quiz'>('flashcard')
  const [materials, setMaterials] = useState<StudyMaterialItem[]>([])
  const [activeMaterial, setActiveMaterial] = useState<StudyMaterialItem | null>(null)
  const [generating, setGenerating] = useState(false)

  useEffect(() => {
    apiRequest<{ items: DocumentItem[] }>('/documents').then((res) => {
      const readyDocs = res.items.filter((d) => d.status === 'ready')
      setDocs(readyDocs)
      if (readyDocs.length > 0) setSelectedDocId(readyDocs[0].id)
    })
    apiRequest<{ items: StudyMaterialItem[] }>('/study').then((res) => {
      setMaterials(res.items)
      if (res.items.length > 0) setActiveMaterial(res.items[0])
    })
  }, [])

  useEffect(() => {
    if (!selectedDocId) return
    apiRequest<{ highlights: HighlightTrace[] }>(`/documents/${selectedDocId}`).then((res) => {
      setTraces(res.highlights)
      setSelectedTraceIds([])
    })
  }, [selectedDocId])

  const toggleTrace = (id: string) => {
    setSelectedTraceIds((prev) =>
      prev.includes(id) ? prev.filter((item) => item !== id) : [...prev, id]
    )
  }

  const handleGenerate = async () => {
    if (selectedTraceIds.length === 0) return
    setGenerating(true)
    try {
      const created = await apiRequest<StudyMaterialItem>('/study/generate', {
        method: 'POST',
        body: JSON.stringify({
          trace_ids: selectedTraceIds,
          material_type: materialType,
          count: 5,
        }),
      })
      setMaterials((prev) => [created, ...prev])
      setActiveMaterial(created)
    } finally {
      setGenerating(false)
    }
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6 px-4 py-6">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Ôn tập chủ động (Flashcard & Quiz)</h1>
        <p className="text-sm text-slate-500">
          Chọn các vùng highlight quan trọng để AI sinh thẻ ghi nhớ hoặc câu hỏi trắc nghiệm.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <div className="space-y-4 rounded-xl border border-slate-200 bg-white p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <select
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm"
            >
              {docs.length === 0 && <option value="">Chưa có tài liệu sẵn sàng</option>}
              {docs.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.title}
                </option>
              ))}
            </select>

            <div className="flex items-center gap-2">
              <select
                value={materialType}
                onChange={(e) => setMaterialType(e.target.value as 'flashcard' | 'quiz')}
                className="rounded-lg border border-slate-300 px-2.5 py-1.5 text-sm"
              >
                <option value="flashcard">Flashcard</option>
                <option value="quiz">Quiz trắc nghiệm</option>
              </select>
              <button
                onClick={handleGenerate}
                disabled={generating || selectedTraceIds.length === 0}
                className="flex items-center gap-1.5 rounded-lg bg-indigo-600 px-3.5 py-1.5 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
              >
                {generating ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
                <span>Tạo ({selectedTraceIds.length})</span>
              </button>
            </div>
          </div>

          <div className="max-h-96 space-y-2.5 overflow-y-auto pr-1">
            {traces.map((t) => (
              <HighlightCard
                key={t.id}
                pageNumber={t.page_number}
                color={t.highlight_color}
                extractedText={t.extracted_text}
                contextSnippet={null}
                selectable
                selected={selectedTraceIds.includes(t.id)}
                onToggleSelect={() => toggleTrace(t.id)}
              />
            ))}
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {materials.map((m) => (
              <button
                key={m.id}
                onClick={() => setActiveMaterial(m)}
                className={`rounded-lg px-3 py-1.5 text-xs font-medium ${
                  activeMaterial?.id === m.id
                    ? 'bg-indigo-600 text-white'
                    : 'border border-slate-200 bg-white text-slate-700'
                }`}
              >
                {m.title}
              </button>
            ))}
          </div>

          {activeMaterial ? (
            <StudyPlayer material={activeMaterial} />
          ) : (
            <div className="rounded-xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
              Chọn vùng highlight bên trái và nhấn "Tạo" để bắt đầu ôn tập.
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
