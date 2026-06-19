import React, { useState } from 'react'
import { AgentEvent } from '../types'

interface Props {
  events: AgentEvent[]
}

export default function AgentTrace({ events }: Props) {
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())

  if (!events.length) return null

  // Group events by step
  const steps: Record<number, AgentEvent[]> = {}
  for (const e of events) {
    const s = e.step ?? 0
    if (!steps[s]) steps[s] = []
    steps[s].push(e)
  }

  const toggleStep = (key: string) => {
    setCollapsed(prev => {
      const next = new Set(prev)
      next.has(key) ? next.delete(key) : next.add(key)
      return next
    })
  }

  return (
    <div style={{ marginTop: 8, fontSize: 12 }}>
      {Object.entries(steps).map(([stepNum, stepEvents]) => {
        const key = `step-${stepNum}`
        const isCollapsed = collapsed.has(key)
        const toolCalls = stepEvents.filter(e => e.type === 'tool_call')
        const toolResults = stepEvents.filter(e => e.type === 'tool_result')

        if (parseInt(stepNum) === 0) return null

        return (
          <div key={key} style={{ marginBottom: 6, borderRadius: 6, overflow: 'hidden', border: '1px solid var(--border)' }}>
            <div
              onClick={() => toggleStep(key)}
              style={{
                padding: '5px 10px', background: 'var(--surface2)', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: 6, userSelect: 'none',
              }}
            >
              <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>{isCollapsed ? '▶' : '▼'}</span>
              <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Step {stepNum}</span>
              {toolCalls.map((tc, i) => (
                <span key={i} style={{
                  background: 'var(--tool-bg)', border: '1px solid var(--tool-border)',
                  borderRadius: 4, padding: '1px 6px', color: '#a5b4fc', fontSize: 11,
                }}>
                  {tc.tool_name}
                </span>
              ))}
            </div>

            {!isCollapsed && (
              <div style={{ padding: '8px 10px', background: '#0d0d1a' }}>
                {toolCalls.map((tc, i) => {
                  const result = toolResults[i]
                  return (
                    <div key={i} style={{ marginBottom: i < toolCalls.length - 1 ? 10 : 0 }}>
                      {/* Tool call */}
                      <div style={{ marginBottom: 4 }}>
                        <span style={{ color: '#a5b4fc', fontWeight: 600 }}>→ {tc.tool_name}</span>
                        {tc.tool_input && Object.keys(tc.tool_input).length > 0 && (
                          <pre style={{
                            marginTop: 4, padding: '6px 8px', background: 'rgba(99,102,241,0.08)',
                            borderRadius: 4, fontSize: 11, color: '#c4b5fd', overflowX: 'auto',
                            whiteSpace: 'pre-wrap', wordBreak: 'break-word',
                          }}>
                            {JSON.stringify(tc.tool_input, null, 2)}
                          </pre>
                        )}
                      </div>
                      {/* Tool result */}
                      {result?.tool_result && (
                        <pre style={{
                          padding: '6px 8px', background: 'rgba(74,222,128,0.06)',
                          border: '1px solid rgba(74,222,128,0.15)', borderRadius: 4,
                          fontSize: 11, color: '#86efac', overflowX: 'auto',
                          whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 200,
                          overflowY: 'auto',
                        }}>
                          {result.tool_result}
                        </pre>
                      )}
                    </div>
                  )
                })}

                {/* No tool calls — just text reasoning */}
                {toolCalls.length === 0 && (
                  <span style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>Reasoning step</span>
                )}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
