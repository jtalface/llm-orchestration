import React from 'react'
import { Message } from '../types'
import AgentTrace from './AgentTrace'

interface Props {
  message: Message
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === 'user'

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: isUser ? 'flex-end' : 'flex-start',
      marginBottom: 16,
      maxWidth: '100%',
    }}>
      {/* Role label */}
      <div style={{
        fontSize: 11, fontWeight: 600, color: 'var(--text-dim)',
        marginBottom: 4, paddingLeft: isUser ? 0 : 2,
        textTransform: 'uppercase', letterSpacing: '0.06em',
      }}>
        {isUser ? 'You' : message.isAgent ? '⚡ Agent' : 'Assistant'}
      </div>

      {/* Bubble */}
      <div style={{
        maxWidth: '80%',
        padding: '10px 14px',
        borderRadius: isUser ? '12px 12px 4px 12px' : '12px 12px 12px 4px',
        background: isUser ? 'var(--accent)' : 'var(--surface2)',
        color: 'var(--text)',
        lineHeight: 1.6,
        fontSize: 14,
        wordBreak: 'break-word',
      }}>
        {message.isStreaming && !message.content ? (
          <span style={{ color: 'var(--text-dim)' }}>
            <BlinkingCursor />
          </span>
        ) : (
          <MarkdownContent content={message.content} />
        )}
        {message.isStreaming && message.content && (
          <BlinkingCursor />
        )}
      </div>

      {/* Agent trace — shown below the bubble */}
      {message.isAgent && message.agentEvents && message.agentEvents.length > 0 && (
        <div style={{ maxWidth: '80%', width: '100%' }}>
          <AgentTrace events={message.agentEvents} />
        </div>
      )}

      {/* Usage */}
      {message.usage && !message.isStreaming && (
        <div style={{ fontSize: 10, color: 'var(--text-dim)', marginTop: 4, paddingLeft: 2 }}>
          {message.usage.input_tokens && `${message.usage.input_tokens + message.usage.output_tokens} tokens`}
          {message.usage.steps !== undefined && ` · ${message.usage.steps} steps`}
        </div>
      )}
    </div>
  )
}

function BlinkingCursor() {
  return (
    <span style={{
      display: 'inline-block', width: 2, height: '1em', background: 'var(--text)',
      marginLeft: 1, verticalAlign: 'text-bottom', animation: 'blink 1s step-end infinite',
    }}>
      <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`}</style>
    </span>
  )
}

function MarkdownContent({ content }: { content: string }) {
  if (!content) return null

  // Simple inline markdown rendering without external deps
  const html = content
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    // Code blocks
    .replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre style="background:rgba(0,0,0,0.3);padding:10px 12px;border-radius:6px;overflow-x:auto;margin:8px 0;font-size:12px;"><code>$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code style="background:rgba(0,0,0,0.3);padding:2px 5px;border-radius:3px;font-size:12px;">$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3 style="margin:10px 0 4px;font-size:14px;color:var(--text)">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 style="margin:12px 0 4px;font-size:15px;color:var(--text)">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 style="margin:14px 0 4px;font-size:16px;color:var(--text)">$1</h1>')
    // Horizontal rule
    .replace(/^---$/gm, '<hr style="border:none;border-top:1px solid var(--border);margin:10px 0">')
    // Newlines
    .replace(/\n/g, '<br/>')

  return <span dangerouslySetInnerHTML={{ __html: html }} />
}
