import React, { useState } from 'react'
import { Conversation } from '../types'

interface Props {
  conversations: Conversation[]
  activeId: string | null
  onSelect: (id: string) => void
  onCreate: () => void
  onDelete: (id: string) => void
  onRename: (id: string, title: string) => void
}

export default function Sidebar({ conversations, activeId, onSelect, onCreate, onDelete, onRename }: Props) {
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editTitle, setEditTitle] = useState('')

  const startEdit = (conv: Conversation, e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(conv.id)
    setEditTitle(conv.title)
  }

  const commitEdit = (id: string) => {
    if (editTitle.trim()) onRename(id, editTitle.trim())
    setEditingId(null)
  }

  return (
    <div style={{
      width: 240, minWidth: 240, background: 'var(--surface)', borderRight: '1px solid var(--border)',
      display: 'flex', flexDirection: 'column', height: '100vh',
    }}>
      {/* Header */}
      <div style={{ padding: '16px 12px 12px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: 'var(--text)', letterSpacing: '0.02em', marginBottom: 10 }}>
          LLM Platform
        </div>
        <button onClick={onCreate} style={newBtnStyle}>
          <span style={{ fontSize: 16, lineHeight: 1 }}>+</span> New conversation
        </button>
      </div>

      {/* Conversation list */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
        {conversations.length === 0 && (
          <div style={{ padding: '16px 12px', color: 'var(--text-dim)', fontSize: 12 }}>
            No conversations yet
          </div>
        )}
        {conversations.map(conv => (
          <div
            key={conv.id}
            onClick={() => onSelect(conv.id)}
            style={{
              padding: '8px 12px',
              cursor: 'pointer',
              background: activeId === conv.id ? 'var(--surface2)' : 'transparent',
              borderLeft: activeId === conv.id ? '2px solid var(--accent)' : '2px solid transparent',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              position: 'relative',
            }}
            className="sidebar-item"
          >
            {editingId === conv.id ? (
              <input
                autoFocus
                value={editTitle}
                onChange={e => setEditTitle(e.target.value)}
                onBlur={() => commitEdit(conv.id)}
                onKeyDown={e => {
                  if (e.key === 'Enter') commitEdit(conv.id)
                  if (e.key === 'Escape') setEditingId(null)
                }}
                onClick={e => e.stopPropagation()}
                style={{
                  flex: 1, background: 'var(--surface2)', border: '1px solid var(--accent)',
                  color: 'var(--text)', borderRadius: 4, padding: '2px 6px', fontSize: 13,
                }}
              />
            ) : (
              <>
                <span style={{
                  flex: 1, fontSize: 13, color: activeId === conv.id ? 'var(--text)' : 'var(--text-dim)',
                  overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
                }}>
                  {conv.title}
                </span>
                <span style={{ display: 'flex', gap: 2, opacity: 0, transition: 'opacity 0.1s' }} className="item-actions">
                  <button onClick={e => startEdit(conv, e)} style={iconBtnStyle} title="Rename">✏️</button>
                  <button onClick={e => { e.stopPropagation(); onDelete(conv.id) }} style={iconBtnStyle} title="Delete">🗑</button>
                </span>
              </>
            )}
          </div>
        ))}
      </div>

      {/* Footer */}
      <div style={{ padding: '10px 12px', borderTop: '1px solid var(--border)', color: 'var(--text-dim)', fontSize: 11 }}>
        <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer"
          style={{ color: 'var(--text-dim)', textDecoration: 'none' }}>
          API docs ↗
        </a>
      </div>

      <style>{`
        .sidebar-item:hover .item-actions { opacity: 1 !important; }
      `}</style>
    </div>
  )
}

const newBtnStyle: React.CSSProperties = {
  width: '100%', padding: '7px 10px', background: 'var(--accent)', border: 'none',
  borderRadius: 6, color: '#fff', fontSize: 13, cursor: 'pointer', display: 'flex',
  alignItems: 'center', gap: 6, fontWeight: 500,
}

const iconBtnStyle: React.CSSProperties = {
  background: 'none', border: 'none', cursor: 'pointer', padding: '2px 3px',
  fontSize: 11, borderRadius: 3, color: 'var(--text-dim)',
}
