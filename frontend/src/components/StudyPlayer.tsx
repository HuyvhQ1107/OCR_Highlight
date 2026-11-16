import { useState } from 'react'
import { CheckCircle2, RotateCw, XCircle } from 'lucide-react'
import type { StudyMaterialItem } from '../types'

interface StudyPlayerProps {
  material: StudyMaterialItem
}

export function StudyPlayer({ material }: StudyPlayerProps) {
  const [flipped, setFlipped] = useState<Record<number, boolean>>({})
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({})

  if (material.material_type === 'flashcard') {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {material.items.map((card, idx) => {
          const isFlipped = Boolean(flipped[idx])
          return (
            <div
              key={idx}
              onClick={() => setFlipped((prev) => ({ ...prev, [idx]: !isFlipped }))}
              className="cursor-pointer rounded-xl border border-slate-200 bg-white p-5 shadow-xs transition hover:border-indigo-300"
            >
              <div className="mb-2 flex items-center justify-between text-xs font-medium text-slate-400">
                <span>Thẻ #{idx + 1} • {isFlipped ? 'Mặt sau (Đáp án)' : 'Mặt trước (Câu hỏi)'}</span>
                <RotateCw className="h-3.5 w-3.5" />
              </div>
              <p className="text-sm font-medium text-slate-800">
                {isFlipped ? card.back : card.front}
              </p>
            </div>
          )
        })}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {material.items.map((q, idx) => {
        const chosen = selectedAnswers[idx]
        const options: string[] = Array.isArray(q.options) ? q.options : []
        return (
          <div key={idx} className="rounded-xl border border-slate-200 bg-white p-4">
            <p className="mb-3 text-sm font-semibold text-slate-900">
              Câu {idx + 1}: {q.question}
            </p>
            <div className="space-y-2">
              {options.map((opt) => {
                const isChosen = chosen === opt
                const isCorrect = opt === q.correct_answer
                let style = 'border-slate-200 hover:bg-slate-50'
                if (chosen) {
                  if (isCorrect) style = 'border-emerald-400 bg-emerald-50 text-emerald-900'
                  else if (isChosen) style = 'border-red-400 bg-red-50 text-red-900'
                }
                return (
                  <button
                    key={opt}
                    onClick={() => setSelectedAnswers((prev) => ({ ...prev, [idx]: opt }))}
                    className={`flex w-full items-center justify-between rounded-lg border px-3 py-2 text-left text-sm transition ${style}`}
                  >
                    <span>{opt}</span>
                    {chosen && isCorrect && <CheckCircle2 className="h-4 w-4 text-emerald-600" />}
                    {chosen && isChosen && !isCorrect && <XCircle className="h-4 w-4 text-red-600" />}
                  </button>
                )
              })}
            </div>
            {chosen && q.explanation && (
              <p className="mt-3 rounded-lg bg-slate-50 p-2.5 text-xs text-slate-700">
                <span className="font-semibold">Giải thích: </span>
                {q.explanation}
              </p>
            )}
          </div>
        )
      })}
    </div>
  )
}
