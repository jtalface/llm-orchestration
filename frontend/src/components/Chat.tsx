import React, { useState, useRef, useEffect, useCallback } from 'react'
import { Message, AgentEvent, Conversation } from '../types'
import MessageBubble from './MessageBubble'
import ModelSelector from './ModelSelector'

interface Props {
  conversation: Conversation | null
  onFirstMessage?: (title: string) => void
}

let msgSeq = 0
const newId = () => `msg-${++msgSeq}-${Date.now()}`

export default function Chat({ conversation, onFirstMessage }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const [model, setModel] = useState('claude-sonnet-4-6')
  const [isAgentMode, setIsAgentMode] = useState(false)
  const [isMultiAgent, setIsMultiAgent] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Load conversation history when conversation changes
  useEffect(() => {
    setMessages([])
    if (!conversation) return
    fetch(`/conversations/${conversation.id}`)
      .then(r => r.json())
      .then(data => {
        const turns: Message[] = (data.turns || []).map((t: { id: string; role: 'user' | 'assistant'; content: string }) => ({
          id: t.id,
          role: t.role as 'user' | 'assistant',
          content: t.content,
        }))
        setMessages(turns)
      })
      .catch(() => {})
  }, [conversation?.id])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const autoResize = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 200) + 'px'
  }

  const send = useCallback(async () => {
    if (!input.trim() || sending) return
    const text = input.trim()
    setInput('')
    setSending(true)
    if (textareaRef.current) textareaRef.current.style.height = 'auto'

    const userMsg: Message = { id: newId(), role: 'user', content: text }
    const assistantId = newId()
    const assistantMsg: Message = {
      id: assistantId,
      role: 'assistant',
      content: '',
      isStreaming: true,
      isAgent: isAgentMode,
      agentEvents: [],
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])

    // Auto-title first message
    if (messages.length === 0 && onFirstMessage) {
      onFirstMessage(text.slice(0, 60))
    }

    try {
      if (isAgentMode) {
        await streamAgent(text, assistantId)
      } else {
        await streamChat(text, assistantId)
      }
    } finally {
      setSending(false)
    }
  }, [input, sending, isAgentMode, conversation, messages.length, model])

  const streamChat = async (text: string, assistantId: string) => {
    const endpoint = '/chat/stream'
    const body: Record<string, unknown> = { message: text, model }
    if (conversation) body.conversation_id = conversation.id

    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    await consumeSSE(res, (data) => {
      if (data === '[DONE]') return
      try {
        const ev = JSON.parse(data)
        if (ev.type === 'text_delta' && ev.text) {
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, content: m.content + ev.text }
              : m
          ))
        } else if (ev.type === 'stop') {
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, isStreaming: false, usage: ev.usage }
              : m
          ))
        } else if (ev.type === 'error') {
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, isStreaming: false, content: `⚠️ Error: ${ev.error}` }
              : m
          ))
        }
      } catch {}
    })

    setMessages(prev => prev.map(m =>
      m.id === assistantId
        ? { ...m, isStreaming: false, content: m.content || '⚠️ No response received. Check your API key in .env.' }
        : m
    ))
  }

  const streamAgent = async (text: string, assistantId: string) => {
    const body: Record<string, unknown> = { goal: text, model, multi_agent: isMultiAgent }
    if (conversation) body.conversation_id = conversation.id

    const res = await fetch('/agents/run/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    await consumeSSE(res, (data) => {
      if (data === '[DONE]') return
      try {
        const ev: AgentEvent = JSON.parse(data)

        setMessages(prev => prev.map(m => {
          if (m.id !== assistantId) return m

          const newEvents = [...(m.agentEvents || []), ev]

          if (ev.type === 'text_delta' && ev.text) {
            return { ...m, content: m.content + ev.text, agentEvents: newEvents }
          }
          if (ev.type === 'done') {
            return {
              ...m,
              content: ev.final_text || m.content,
              isStreaming: false,
              agentEvents: newEvents,
              usage: ev.usage,
            }
          }
          if (ev.type === 'error') {
            return {
              ...m,
              content: `Error: ${ev.error}`,
              isStreaming: false,
              agentEvents: newEvents,
            }
          }
          return { ...m, agentEvents: newEvents }
        }))
      } catch {}
    })

    setMessages(prev => prev.map(m =>
      m.id === assistantId ? { ...m, isStreaming: false } : m
    ))
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  if (!conversation) {
    return (
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <div style={{ fontSize: 32 }}>⚡</div>
        <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--text)' }}>LLM Orchestration Platform</div>
        <div style={{ color: 'var(--text-dim)', fontSize: 14, textAlign: 'center', maxWidth: 360 }}>
          Select a conversation from the sidebar, or create a new one to get started.
        </div>
      </div>
    )
  }

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      {/* Header */}
      <div style={{
        padding: '12px 20px', borderBottom: '1px solid var(--border)',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        background: 'var(--surface)', flexShrink: 0,
      }}>
        <span style={{ fontWeight: 600, fontSize: 15, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {conversation.title}
        </span>
        <ModelSelector
          value={model} onChange={setModel}
          isAgent={isAgentMode}
          onToggleAgent={v => { setIsAgentMode(v); if (!v) setIsMultiAgent(false) }}
          isMultiAgent={isMultiAgent}
          onToggleMultiAgent={setIsMultiAgent}
        />
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '20px 24px', display: 'flex', flexDirection: 'column' }}>
        {messages.length === 0 && (
          <div style={{ margin: 'auto', textAlign: 'center', color: 'var(--text-dim)', fontSize: 14 }}>
            <div style={{ fontSize: 28, marginBottom: 8 }}>
              {isAgentMode ? '⚡' : '💬'}
            </div>
            <div style={{ fontWeight: 600, marginBottom: 4, color: 'var(--text)' }}>
              {isAgentMode ? 'Agent mode' : 'Chat mode'}
            </div>
            <div style={{ fontSize: 13, maxWidth: 320 }}>
              {isAgentMode
                ? 'Give the agent a goal. It will plan, use tools, observe results, and iterate until done.'
                : 'Ask anything. The model will respond directly without using tools.'
              }
            </div>
          </div>
        )}
        {messages.map(msg => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{
        padding: '12px 20px', borderTop: '1px solid var(--border)',
        background: 'var(--surface)', flexShrink: 0,
      }}>
        <div style={{
          display: 'flex', gap: 8, alignItems: 'flex-end',
          background: 'var(--surface2)', borderRadius: 12,
          border: '1px solid var(--border)', padding: '8px 8px 8px 14px',
        }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => { setInput(e.target.value); autoResize() }}
            onKeyDown={handleKeyDown}
            placeholder={isAgentMode ? 'Give the agent a goal...' : 'Message...'}
            rows={1}
            style={{
              flex: 1, background: 'transparent', border: 'none', resize: 'none',
              color: 'var(--text)', fontSize: 14, lineHeight: 1.5, outline: 'none',
              fontFamily: 'inherit', minHeight: 24, maxHeight: 200,
            }}
          />
          <button
            onClick={send}
            disabled={!input.trim() || sending}
            style={{
              padding: '7px 14px', borderRadius: 8, border: 'none', cursor: 'pointer',
              background: input.trim() && !sending ? 'var(--accent)' : 'var(--border)',
              color: input.trim() && !sending ? '#fff' : 'var(--text-dim)',
              fontSize: 14, fontWeight: 600, transition: 'all 0.15s', flexShrink: 0,
            }}
          >
            {sending ? '...' : '↑'}
          </button>
        </div>
        <div style={{ textAlign: 'center', marginTop: 6, fontSize: 11, color: 'var(--text-dim)' }}>
          Enter to send · Shift+Enter for newline
        </div>
      </div>
    </div>
  )
}

async function consumeSSE(response: Response, onLine: (data: string) => void) {
  const reader = response.body?.getReader()
  if (!reader) return
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() ?? ''
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        onLine(line.slice(6))
      }
    }
  }
}
