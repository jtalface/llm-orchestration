import React, { useState } from 'react'
import { MODELS } from '../types'

interface Props {
  value: string
  onChange: (model: string) => void
  isAgent: boolean
  onToggleAgent: (v: boolean) => void
}

export default function ModelSelector({ value, onChange, isAgent, onToggleAgent }: Props) {
  const [open, setOpen] = useState(false)

  const allModels = Object.entries(MODELS).flatMap(([provider, models]) =>
    models.map(m => ({ provider, model: m }))
  )

  const displayName = value.length > 28 ? '...' + value.slice(-25) : value

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 8 }}>
      {/* Model picker */}
      <button onClick={() => setOpen(o => !o)} style={selectorBtn}>
        <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--green)', display: 'inline-block' }} />
        {displayName}
        <span style={{ color: 'var(--text-dim)', fontSize: 10 }}>▾</span>
      </button>

      {open && (
        <div style={dropdownStyle} onClick={e => e.stopPropagation()}>
          {Object.entries(MODELS).map(([provider, models]) => (
            <div key={provider}>
              <div style={{ padding: '6px 10px 3px', fontSize: 10, fontWeight: 700, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                {provider}
              </div>
              {models.map(m => (
                <div
                  key={m}
                  onClick={() => { onChange(m); setOpen(false) }}
                  style={{
                    padding: '6px 10px', cursor: 'pointer', fontSize: 13,
                    background: value === m ? 'var(--surface2)' : 'transparent',
                    color: value === m ? 'var(--accent-hover)' : 'var(--text)',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'var(--surface2)')}
                  onMouseLeave={e => (e.currentTarget.style.background = value === m ? 'var(--surface2)' : 'transparent')}
                >
                  {m}
                </div>
              ))}
            </div>
          ))}
          {/* Custom model input */}
          <div style={{ borderTop: '1px solid var(--border)', padding: '8px 10px' }}>
            <input
              placeholder="Custom model ID..."
              style={customInputStyle}
              onKeyDown={e => {
                if (e.key === 'Enter') {
                  const v = (e.currentTarget.value || '').trim()
                  if (v) { onChange(v); setOpen(false) }
                }
              }}
            />
          </div>
        </div>
      )}

      {/* Agent mode toggle */}
      <button
        onClick={() => onToggleAgent(!isAgent)}
        style={{
          ...agentToggleStyle,
          background: isAgent ? 'var(--accent)' : 'var(--surface2)',
          color: isAgent ? '#fff' : 'var(--text-dim)',
          border: isAgent ? 'none' : '1px solid var(--border)',
        }}
        title="Toggle agent mode (uses the full Plan→Act→Observe loop with tools)"
      >
        {isAgent ? '⚡ Agent' : '💬 Chat'}
      </button>

      {open && (
        <div onClick={() => setOpen(false)} style={{ position: 'fixed', inset: 0, zIndex: 9 }} />
      )}
    </div>
  )
}

const selectorBtn: React.CSSProperties = {
  display: 'flex', alignItems: 'center', gap: 6, padding: '6px 10px',
  background: 'var(--surface2)', border: '1px solid var(--border)', borderRadius: 6,
  color: 'var(--text)', fontSize: 13, cursor: 'pointer',
}

const dropdownStyle: React.CSSProperties = {
  position: 'absolute', bottom: '100%', left: 0, marginBottom: 6,
  background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 8,
  minWidth: 240, maxHeight: 380, overflowY: 'auto', zIndex: 10,
  boxShadow: '0 8px 32px rgba(0,0,0,0.4)',
}

const agentToggleStyle: React.CSSProperties = {
  padding: '6px 12px', borderRadius: 6, fontSize: 12, cursor: 'pointer',
  fontWeight: 600, transition: 'all 0.15s',
}

const customInputStyle: React.CSSProperties = {
  width: '100%', background: 'var(--surface2)', border: '1px solid var(--border)',
  borderRadius: 4, padding: '5px 8px', color: 'var(--text)', fontSize: 12,
}
