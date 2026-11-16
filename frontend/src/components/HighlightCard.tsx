import { Sparkles } from 'lucide-react'

const COLOR_STYLES: Record<string, string> = {
  yellow: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  green: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  blue: 'bg-sky-100 text-sky-800 border-sky-300',
  pink: 'bg-pink-100 text-pink-800 border-pink-300',
  orange: 'bg-orange-100 text-orange-800 border-orange-300',
}

interface HighlightCardProps {
  pageNumber: number
  color: string | null
  extractedText: string
  contextSnippet: string | null
  documentTitle?: string
  selectable?: boolean
  selected?: boolean
  onToggleSelect?: () => void
  onExplain?: () => void
}

export function HighlightCard({
  pageNumber,
  color,
  extractedText,
  contextSnippet,
  documentTitle,
  selectable,
  selected,
  onToggleSelect,
  onExplain,
}: HighlightCardProps) {
  const badgeClass =
    COLOR_STYLES[(color || 'yellow').toLowerCase()] ||
    'bg-slate-100 text-slate-700 border-slate-300'

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-xs transition hover:border-indigo-200">
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          {selectable && (
            <input
              type="checkbox"
              checked={Boolean(selected)}
              onChange={onToggleSelect}
              className="h-4 w-4 rounded border-slate-300 text-indigo-600"
            />
          )}
          <span className="rounded-md bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
            Trang {pageNumber}
          </span>
          <span className={`rounded-md border px-2 py-0.5 text-xs font-medium ${badgeClass}`}>
            {color || 'highlight'}
          </span>
          {documentTitle && (
            <span className="text-xs font-medium text-indigo-600">{documentTitle}</span>
          )}
        </div>
        {onExplain && (
          <button
            onClick={onExplain}
            className="flex items-center gap-1 rounded-lg bg-indigo-50 px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-100"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>AI Giải thích</span>
          </button>
        )}
      </div>

      <blockquote className="border-l-4 border-amber-400 bg-amber-50/50 px-3 py-2 text-sm font-medium text-slate-900">
        {extractedText}
      </blockquote>

      {contextSnippet && (
        <p className="mt-2 text-xs leading-relaxed text-slate-600">
          <span className="font-semibold text-slate-700">Ngữ cảnh: </span>
          {contextSnippet}
        </p>
      )}
    </div>
  )
}
