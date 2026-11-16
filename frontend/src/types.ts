export interface DocumentItem {
  id: string
  title: string
  file_type: string
  file_size_bytes: number
  is_scanned_pdf: boolean
  total_pages: number
  processed_pages: number
  status: 'pending' | 'processing' | 'ready' | 'failed'
  error_message: string | null
  created_at: string
}

export interface HighlightTrace {
  id: string
  document_id: string
  page_number: number
  highlight_color: string | null
  bbox_json: string | null
  extracted_text: string
  context_snippet: string | null
  language: string
  created_at: string
}

export interface SearchResultItem {
  trace_id: string
  document_id: string
  document_title: string
  page_number: number
  highlight_color: string | null
  extracted_text: string
  context_snippet: string | null
  score: number
}

export interface SearchHistoryItem {
  id: string
  query_text: string
  result_count: number
  created_at: string
}

export interface ExplanationResponse {
  id: string
  trace_id: string
  mode: 'basic' | 'deep' | 'example' | 'summary'
  content: string
  created_at: string
}

export interface RelatedTraceItem {
  trace_id: string
  document_id: string
  document_title: string
  page_number: number
  extracted_text: string
  similarity_score: number
}

export interface RelatedTracesResponse {
  trace_id: string
  related_traces: RelatedTraceItem[]
}

export interface StudyMaterialItem {
  id: string
  material_type: 'flashcard' | 'quiz'
  title: string
  items: Array<Record<string, any>>
  created_at: string
}
