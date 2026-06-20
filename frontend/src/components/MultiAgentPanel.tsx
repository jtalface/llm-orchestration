import React, { useState } from 'react'
import { SubtaskState } from '../types'
import AgentTrace from './AgentTrace'

interface Props {
  plan: Array<{ id: string; title: string; goal: string }>
  subtasks: Record<string, SubtaskState>
  synthesisStatus: 'idle' | 'running' | 'done'
  isStreaming: boolean
}

const STATUS_ICON: Record<string, string> = {
  pending: '⏳',
  running: '⚡',
  done: '✅',
  error: '❌',
}

const STATUS_COLOR: Record<string, string> = {
  pending: 'var(--text-dim)',
  running: '#fbbf24',
  done: '#4ade80',
  error: '#f87171',
}

export default function MultiAgentPanel({ plan, subtasks, synthesisStatus, isStreaming }: Props) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set())

  const toggle = (id: string) =>
    setExpanded(prev => {
      const next = new Set(prev)
      next.has(id) ? next.delete(id) : next.add(id)
      return next
    })

  const doneCount = plan.filter(p => subtasks[p.id]?.status === 'done').length

  return (
    <div style={{ marginTop: 10, fontSize: 12 }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8,
        padding: '6px 10px', background: 'var(--surface2)', borderRadius: 8,
        border: '1px solid var(--border)',
      }}>
        <span style={{ fontSize: 13 }}>🤖</span>
        <span style={{ fontWeight: 700, color: 'var(--text)', fontSize: 12 }}>Multi-Agent Run</span>
        <span style={{ color: 'var(--text-dim)', fontSize: 11 }}>
          {plan.length} specialists
        </span>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6 }}>
          <div style={{ display: 'flex', gap: 3 }}>
            {plan.map(p => {
              const status = subtasks[p.id]?.status ?? 'pending'
              return (
                <div
                  key={p.id}
                  style={{
                    width: 8, height: 8, borderRadius: '50%',
                    background: STATUS_COLOR[status],
                    transition: 'background 0.3s',
                  }}
                  title={p.title}
                />
              )
            })}
          </div>
          <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>
            {doneCount}/{plan.length}
          </span>
        </div>
      </div>

      {/* Subtask cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {plan.map(p => {
          const sub = subtasks[p.id] ?? { id: p.id, title: p.title, goal: p.goal, status: 'pending', step: 0, events: [] }
          const isExp = expanded.has(p.id)
          const status = sub.status

          return (
            <div key={p.id} style={{
              border: `1px solid ${status === 'running' ? '#f59e0b55' : 'var(--border)'}`,
              borderRadius: 8, overflow: 'hidden',
              transition: 'border-color 0.3s',
            }}>
              {/* Card header */}
              <div
                onClick={() => toggle(p.id)}
                style={{
                  padding: '7px 10px', background: 'var(--surface2)', cursor: 'pointer',
                  display: 'flex', alignItems: 'center', gap: 8, userSelect: 'none',
                }}
              >
                <span style={{ fontSize: 14 }}>{STATUS_ICON[status]}</span>
                <span style={{ fontWeight: 600, color: STATUS_COLOR[status], fontSize: 12 }}>
                  {p.title}
                </span>

                {status === 'running' && (
                  <span style={{
                    fontSize: 10, color: '#fbbf24',
                    animation: 'pulse 1.5s ease-in-out infinite',
                  }}>
                    step {sub.step}
                  </span>
                )}

                {status === 'running' && sub.currentTool && (
                  <span style={{
                    background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.3)',
                    borderRadius: 4, padding: '1px 6px', color: '#a5b4fc', fontSize: 10,
                  }}>
                    {sub.currentTool}
                  </span>
                )}

                {status === 'done' && (
                  <span style={{ color: 'var(--text-dim)', fontSize: 10, marginLeft: 'auto' }}>
                    {sub.step} step{sub.step !== 1 ? 's' : ''}
                  </span>
                )}

                <span style={{ color: 'var(--text-dim)', fontSize: 10, marginLeft: status === 'done' ? 0 : 'auto' }}>
                  {isExp ? '▼' : '▶'}
                </span>
              </div>

              {/* Goal subtitle — always visible */}
              <div style={{
                padding: '4px 10px 5px 36px',
                background: '#0a0e1a',
                color: 'var(--text-dim)', fontSize: 10, lineHeight: 1.4,
                borderBottom: isExp && sub.events.length > 0 ? '1px solid var(--border)' : 'none',
              }}>
                {p.goal.length > 120 ? p.goal.slice(0, 120) + '…' : p.goal}
              </div>

              {/* Expanded: agent trace */}
              {isExp && sub.events.length > 0 && (
                <div style={{ padding: '8px 10px', background: '#080c18' }}>
                  <AgentTrace events={sub.events} />
                  {sub.finalText && (
                    <div style={{
                      marginTop: 8, padding: '6px 8px',
                      background: 'rgba(74,222,128,0.05)', border: '1px solid rgba(74,222,128,0.15)',
                      borderRadius: 4, color: '#86efac', fontSize: 11, whiteSpace: 'pre-wrap',
                    }}>
                      {sub.finalText.slice(0, 400)}{sub.finalText.length > 400 ? '…' : ''}
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Synthesis row */}
      {synthesisStatus !== 'idle' && (
        <div style={{
          marginTop: 8, padding: '7px 10px',
          border: `1px solid ${synthesisStatus === 'done' ? 'rgba(139,92,246,0.4)' : 'rgba(139,92,246,0.2)'}`,
          borderRadius: 8, background: '#1a1a2e',
          display: 'flex', alignItems: 'center', gap: 8,
          transition: 'border-color 0.3s',
        }}>
          <span style={{ fontSize: 14 }}>
            {synthesisStatus === 'done' ? '✅' : '🔀'}
          </span>
          <span style={{ color: '#a78bfa', fontWeight: 600, fontSize: 12 }}>
            {synthesisStatus === 'running' ? 'Synthesizing results…' : 'Synthesis complete'}
          </span>
        </div>
      )}

      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
      `}</style>
    </div>
  )
}
