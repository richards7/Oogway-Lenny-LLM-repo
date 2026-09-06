import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import ChatWindow from './components/ChatWindow';
import MessageInput from './components/MessageInput';
import ArtifactViewer from './components/ArtifactViewer';
import { AlertCircle, RefreshCw } from 'lucide-react';

const SIDEBAR_DEFAULT_WIDTH = 260;
const SIDEBAR_MIN_WIDTH = 200;
const SIDEBAR_MAX_WIDTH = 480;

const ARTIFACT_DEFAULT_WIDTH = 460;
const ARTIFACT_MIN_WIDTH = 320;

// localStorage throws in some embedded/private contexts - never let it break render.
const readStored = (key, fallback) => {
  try {
    const v = localStorage.getItem(key);
    return v === null ? fallback : v;
  } catch {
    return fallback;
  }
};

export default function App() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sessionsList, setSessionsList] = useState([]);
  const [activeProvider, setActiveProvider] = useState('ollama');
  const [activeArtifact, setActiveArtifact] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [config, setConfig] = useState(null);
  const [backendOffline, setBackendOffline] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(() => {
    const saved = Number(readStored('sidebarWidth', SIDEBAR_DEFAULT_WIDTH));
    return saved >= SIDEBAR_MIN_WIDTH && saved <= SIDEBAR_MAX_WIDTH ? saved : SIDEBAR_DEFAULT_WIDTH;
  });
  const [sidebarCollapsed, setSidebarCollapsed] = useState(
    () => readStored('sidebarCollapsed', 'false') === 'true'
  );
  const [artifactWidth, setArtifactWidth] = useState(() => {
    const saved = Number(readStored('artifactWidth', ARTIFACT_DEFAULT_WIDTH));
    return saved >= ARTIFACT_MIN_WIDTH ? saved : ARTIFACT_DEFAULT_WIDTH;
  });

  // Persist sidebar layout across reloads.
  useEffect(() => {
    try {
      localStorage.setItem('sidebarWidth', String(sidebarWidth));
      localStorage.setItem('sidebarCollapsed', String(sidebarCollapsed));
      localStorage.setItem('artifactWidth', String(artifactWidth));
    } catch {
      /* storage unavailable - layout just won't persist */
    }
  }, [sidebarWidth, sidebarCollapsed, artifactWidth]);

  // Pointer capture keeps the drag alive over iframes and outside the window.
  // `direction` is +1 when the panel grows as the pointer moves right (sidebar)
  // and -1 when it grows as the pointer moves left (artifact panel).
  const makeResizeHandler = (getWidth, setWidth, min, max, direction) => (e) => {
    e.preventDefault();
    const handle = e.currentTarget;
    const startX = e.clientX;
    const startWidth = getWidth();

    const onMove = (ev) => {
      const limit = typeof max === 'function' ? max() : max;
      const next = Math.min(limit, Math.max(min, startWidth + direction * (ev.clientX - startX)));
      setWidth(next);
    };
    const onUp = (ev) => {
      handle.releasePointerCapture?.(ev.pointerId);
      handle.removeEventListener('pointermove', onMove);
      handle.removeEventListener('pointerup', onUp);
      handle.removeEventListener('pointercancel', onUp);
      document.body.style.userSelect = '';
      document.body.style.cursor = '';
    };

    handle.setPointerCapture?.(e.pointerId);
    handle.addEventListener('pointermove', onMove);
    handle.addEventListener('pointerup', onUp);
    handle.addEventListener('pointercancel', onUp);
    document.body.style.userSelect = 'none';
    document.body.style.cursor = 'col-resize';
  };

  const handleResizeStart = makeResizeHandler(
    () => sidebarWidth, setSidebarWidth, SIDEBAR_MIN_WIDTH, SIDEBAR_MAX_WIDTH, 1
  );

  // Cap the artifact panel so the chat column always keeps a usable measure.
  const handleArtifactResizeStart = makeResizeHandler(
    () => artifactWidth,
    setArtifactWidth,
    ARTIFACT_MIN_WIDTH,
    () => Math.max(ARTIFACT_MIN_WIDTH, window.innerWidth - (sidebarCollapsed ? 48 : sidebarWidth) - 380),
    -1
  );

  // Initialize Session & Load History List
  useEffect(() => {
    fetchConfig();
    initApp();
  }, []);

  const initApp = async () => {
    const list = await fetchSessionsList();
    if (list && list.length > 0) {
      await selectSession(list[0].id);
    } else {
      await createNewSession();
    }
  };

  const fetchSessionsList = async () => {
    try {
      const res = await fetch('/api/sessions');
      if (res.ok) {
        const data = await res.json();
        setSessionsList(data);
        return data;
      }
    } catch (err) {
      console.error('Failed to fetch sessions list:', err);
    }
    return [];
  };

  const selectSession = async (sId) => {
    setSessionId(sId);
    setActiveArtifact(null);
    try {
      const res = await fetch(`/api/sessions/${sId}/messages`);
      if (res.ok) {
        const msgs = await res.json();
        setMessages(msgs);
        // Deliberately does NOT re-open the last artifact. Auto-opening meant a
        // panel the user had closed came back every time they revisited the
        // chat. Each message keeps its own "View Artifact" button instead.
      }
    } catch (err) {
      console.error(`Failed to load messages for session ${sId}:`, err);
    }
  };

  const createNewSession = async () => {
    try {
      const res = await fetch('/api/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ client_metadata: { user_agent: navigator.userAgent } })
      });
      if (res.ok) {
        const data = await res.json();
        setSessionId(data.session_id);
        setMessages([]);
        setActiveArtifact(null);
        setBackendOffline(false);
        await fetchSessionsList();
        return data.session_id;
      }
    } catch (err) {
      console.error('Failed to create session:', err);
      setBackendOffline(true);
    }
    return null;
  };

  const handleDeleteSession = async (sId) => {
    try {
      await fetch(`/api/sessions/${sId}`, { method: 'DELETE' });
      const updated = sessionsList.filter(s => s.id !== sId);
      setSessionsList(updated);
      if (sId === sessionId) {
        if (updated.length > 0) {
          selectSession(updated[0].id);
        } else {
          createNewSession();
        }
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
  };

  const fetchConfig = async () => {
    try {
      const res = await fetch('/api/config');
      if (res.ok) {
        const data = await res.json();
        setConfig(data);
        if (data.active_provider) {
          setActiveProvider(data.active_provider);
        }
        setBackendOffline(false);
      }
    } catch (err) {
      console.error('Failed to fetch config:', err);
      setBackendOffline(true);
    }
  };

  // Edit and regenerate both rewind the thread on the server, so the client
  // trims its own tail first and then appends whatever the replayed turn returns.
  const replayTurn = async (url, payload, truncateAt) => {
    if (isLoading || !sessionId) return;

    const previous = messages;
    setMessages(truncateAt);
    setActiveArtifact(null);
    setIsLoading(true);

    try {
      const res = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });

      if (res.ok) {
        const assistantMsg = await res.json();
        setMessages((prev) => [...prev, assistantMsg]);
        if (assistantMsg.artifact) setActiveArtifact(assistantMsg.artifact);
        setBackendOffline(false);
        fetchSessionsList();
      } else {
        // Server rejected the replay, so the thread is untouched - put it back.
        const errData = await res.json().catch(() => null);
        setMessages(previous);
        setMessages((prev) => [...prev, {
          id: 'err-' + Date.now(),
          role: 'assistant',
          content: `⚠️ **Could not update that message**: ${errData?.error?.message || 'Request failed.'}`,
          citations: [],
          model_provider: activeProvider
        }]);
      }
    } catch (err) {
      setMessages(previous);
      setBackendOffline(true);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEditMessage = (messageId, newContent) => {
    const idx = messages.findIndex((m) => m.id === messageId);
    if (idx === -1) return;
    const trimmed = messages
      .slice(0, idx + 1)
      .map((m) => (m.id === messageId ? { ...m, content: newContent } : m));

    return replayTurn(
      `/api/sessions/${sessionId}/messages/${messageId}/edit`,
      { content: newContent, provider_override: activeProvider },
      trimmed
    );
  };

  const handleRegenerate = (messageId) => {
    const idx = messages.findIndex((m) => m.id === messageId);
    if (idx === -1) return;

    return replayTurn(
      `/api/sessions/${sessionId}/messages/${messageId}/regenerate`,
      { provider_override: activeProvider },
      messages.slice(0, idx)
    );
  };

  const handleSendMessage = async (userPrompt) => {
    if (isLoading) return;

    let activeSession = sessionId;
    if (!activeSession) {
      activeSession = await createNewSession();
    }

    if (!activeSession) {
      setMessages(prev => [...prev, {
        id: 'err-' + Date.now(),
        role: 'assistant',
        content: `⚠️ **Backend Server Offline**: Unable to establish a session with backend on \`http://localhost:5001\`. Please make sure your backend server is running (\`.\\dev-backend.bat\` or \`docker compose up -d\`).`,
        citations: [],
        model_provider: activeProvider
      }]);
      return;
    }

    // Optimistic user message update
    const tempUserMsg = {
      id: 'temp-' + Date.now(),
      role: 'user',
      content: userPrompt,
      citations: [],
      model_provider: 'user'
    };
    setMessages(prev => [...prev, tempUserMsg]);
    setIsLoading(true);

    try {
      const res = await fetch(`/api/sessions/${activeSession}/messages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: userPrompt,
          provider_override: activeProvider
        })
      });

      if (res.ok) {
        const assistantMsg = await res.json();
        setMessages(prev => [...prev, assistantMsg]);
        if (assistantMsg.artifact) {
          setActiveArtifact(assistantMsg.artifact);
        }
        setBackendOffline(false);
        fetchSessionsList();
      } else {
        const errData = await res.json();
        const errContent = errData?.error?.message || 'Error executing request.';
        setMessages(prev => [...prev, {
          id: 'err-' + Date.now(),
          role: 'assistant',
          content: `⚠️ **API Error**: ${errContent}`,
          citations: [],
          model_provider: activeProvider
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: 'err-' + Date.now(),
        role: 'assistant',
        content: `⚠️ **Connection Failure**: Unable to connect to backend server. Make sure \`.\\dev-backend.bat\` is running.`,
        citations: [],
        model_provider: activeProvider
      }]);
      setBackendOffline(true);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw' }}>
      <Header 
        activeProvider={activeProvider}
        onProviderChange={setActiveProvider}
        onNewSession={createNewSession}
        config={config}
      />

      {backendOffline && (
        <div style={{
          background: '#FDF2F2',
          borderBottom: '1px solid #F87171',
          padding: '8px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          fontSize: '13px',
          color: '#991B1B'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} color="#DC2626" />
            <span><strong>Backend Offline:</strong> Python backend is not running on <code>http://localhost:5001</code>. Run <code>.\dev-backend.bat</code> in your terminal.</span>
          </div>
          <button 
            className="glass-button" 
            style={{ padding: '3px 10px', fontSize: '11px', background: '#FFFFFF', borderColor: '#FCA5A5' }}
            onClick={() => { createNewSession(); fetchConfig(); }}
          >
            <RefreshCw size={12} /> Retry Connection
          </button>
        </div>
      )}

      <div style={{ display: 'flex', flex: 1, overflow: 'hidden' }}>
        {/* Left Sidebar for Chat History */}
        <Sidebar 
          sessions={sessionsList}
          activeSessionId={sessionId}
          onSelectSession={selectSession}
          onNewSession={createNewSession}
          onDeleteSession={handleDeleteSession}
          width={sidebarWidth}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((c) => !c)}
          onResizeStart={handleResizeStart}
          onResizeReset={() => setSidebarWidth(SIDEBAR_DEFAULT_WIDTH)}
        />

        {/* Main Chat Area */}
        <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', height: '100%' }}>
          <ChatWindow 
            messages={messages} 
            isLoading={isLoading} 
            onSelectArtifact={setActiveArtifact}
            activeArtifactId={activeArtifact?.id || null}
            onEditMessage={handleEditMessage}
            onRegenerate={handleRegenerate}
          />
          <MessageInput 
            onSendMessage={handleSendMessage} 
            disabled={isLoading}
          />
        </div>

        {/* Side-panel Artifact Viewer */}
        {activeArtifact && (
          <ArtifactViewer 
            artifact={activeArtifact} 
            onClose={() => setActiveArtifact(null)}
            width={artifactWidth}
            onResizeStart={handleArtifactResizeStart}
            onResizeReset={() => setArtifactWidth(ARTIFACT_DEFAULT_WIDTH)}
          />
        )}
      </div>
    </div>
  );
}



