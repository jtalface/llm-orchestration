import React, { useState } from 'react'
import Sidebar from './components/Sidebar'
import Chat from './components/Chat'
import { Conversation } from './types'
import { useConversations } from './hooks/useConversations'

export default function App() {
  const { conversations, create, rename, remove } = useConversations()
  const [activeId, setActiveId] = useState<string | null>(null)

  const activeConv = conversations.find(c => c.id === activeId) ?? null

  const handleCreate = async () => {
    const conv = await create('New conversation')
    setActiveId(conv.id)
  }

  const handleDelete = async (id: string) => {
    await remove(id)
    if (activeId === id) setActiveId(null)
  }

  const handleFirstMessage = (title: string) => {
    if (activeId) rename(activeId, title)
  }

  return (
    <div style={{ display: 'flex', height: '100vh', width: '100vw', overflow: 'hidden' }}>
      <Sidebar
        conversations={conversations}
        activeId={activeId}
        onSelect={setActiveId}
        onCreate={handleCreate}
        onDelete={handleDelete}
        onRename={rename}
      />
      <Chat
        conversation={activeConv}
        onFirstMessage={handleFirstMessage}
      />
    </div>
  )
}
