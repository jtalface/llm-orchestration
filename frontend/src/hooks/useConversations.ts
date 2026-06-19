import { useState, useEffect, useCallback } from 'react'
import { Conversation } from '../types'

export function useConversations() {
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    try {
      const res = await fetch('/conversations')
      const data = await res.json()
      setConversations(data)
    } catch {
      // backend not yet running
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { load() }, [load])

  const create = useCallback(async (title?: string, model?: string) => {
    const res = await fetch('/conversations', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: title || 'New conversation', model }),
    })
    const conv: Conversation = await res.json()
    setConversations(prev => [conv, ...prev])
    return conv
  }, [])

  const rename = useCallback(async (id: string, title: string) => {
    await fetch(`/conversations/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title }),
    })
    setConversations(prev => prev.map(c => c.id === id ? { ...c, title } : c))
  }, [])

  const remove = useCallback(async (id: string) => {
    await fetch(`/conversations/${id}`, { method: 'DELETE' })
    setConversations(prev => prev.filter(c => c.id !== id))
  }, [])

  return { conversations, loading, create, rename, remove, reload: load }
}
