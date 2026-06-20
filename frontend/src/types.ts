export interface Conversation {
  id: string
  title: string
  model: string
  system_prompt: string | null
  created_at: string
  updated_at: string
}

export interface Turn {
  id: string
  conversation_id: string
  role: 'user' | 'assistant' | 'tool_result'
  content: string
  model: string | null
  step: number | null
  tool_calls: unknown[] | null
  tool_results: unknown[] | null
  token_count: number | null
  created_at: string
}

export interface AgentEvent {
  type: string
  step?: number
  text?: string
  tool_name?: string
  tool_input?: Record<string, unknown>
  tool_result?: string
  tool_call_id?: string
  final_text?: string
  error?: string
  usage?: { input_tokens: number; output_tokens: number; steps: number }
}

export type SubtaskStatus = 'pending' | 'running' | 'done' | 'error'

export interface SubtaskState {
  id: string
  title: string
  goal: string
  status: SubtaskStatus
  step: number
  currentTool?: string
  events: AgentEvent[]
  finalText?: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  isStreaming?: boolean
  agentEvents?: AgentEvent[]
  isAgent?: boolean
  isMultiAgent?: boolean
  multiAgentPlan?: Array<{ id: string; title: string; goal: string }>
  subtasks?: Record<string, SubtaskState>
  synthesisStatus?: 'idle' | 'running' | 'done'
  usage?: { input_tokens: number; output_tokens: number; steps?: number }
}

export interface Tool {
  name: string
  description: string
  parameters: Record<string, unknown>
  requires_confirmation: boolean
}

export const MODELS = {
  anthropic: ['claude-opus-4-8', 'claude-sonnet-4-6', 'claude-haiku-4-5-20251001'],
  openai: ['gpt-4o', 'gpt-4o-mini', 'o3'],
  gemini: ['gemini-2.5-pro', 'gemini-2.5-flash'],
  ollama: ['llama3.2', 'mistral', 'qwen2.5', 'phi4', 'deepseek-r1'],
}
