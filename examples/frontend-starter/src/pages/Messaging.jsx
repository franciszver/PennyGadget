import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Messaging.css';

function Messaging() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const queryClient = useQueryClient();
  const [selectedThread, setSelectedThread] = useState(null);
  const [newMessage, setNewMessage] = useState('');

  const { data: threads, isLoading } = useQuery({
    queryKey: ['threads', user?.id],
    queryFn: () => api.getThreads(user.id).then(res => res.data),
    enabled: !!user?.id,
    retry: false,
    onError: (err) => {
      console.log('[MESSAGING] API error (expected in dev):', err);
    }
  });

  const sendMessageMutation = useMutation({
    mutationFn: ({ threadId, data }) => api.sendMessage(threadId, data),
    onSuccess: () => {
      success('Message sent!');
      queryClient.invalidateQueries(['threads', user?.id]);
      setNewMessage('');
    },
    onError: (err) => {
      console.error('[MESSAGING] Send error:', err);
      showError('Failed to send message. Backend may not be running.');
    },
  });

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (!newMessage.trim() || !selectedThread) return;

    sendMessageMutation.mutate({
      threadId: selectedThread.id,
      data: {
        sender_id: user.id,
        content: newMessage,
      },
    });
  };

  if (isLoading) {
    return (
      <div className="messaging">
        <LoadingSpinner message="Loading messages..." />
      </div>
    );
  }

  const threadsList = threads?.data || [];
  const currentThread = threadsList.find(t => t.id === selectedThread?.id) || selectedThread;

  return (
    <div className="messaging">
      <h1>Messages</h1>
      
      {/* Integration Notice */}
      <div className="integration-notice">
        <div className="integration-notice-header">
          <span className="integration-icon">💬</span>
          <h3>Integration Point: Tutor Responses</h3>
        </div>
        <p className="integration-message">
          This is where tutor responses would be integrated. In production, tutors would receive student messages 
          and respond through this messaging system. All tutor responses would appear in the conversation threads below.
        </p>
        <div className="integration-details">
          <strong>How it works:</strong>
          <ul>
            <li>Students send messages to tutors through this interface</li>
            <li>Tutors receive notifications and respond via their dashboard</li>
            <li>All messages are stored in conversation threads</li>
            <li>Threads can be closed when issues are resolved</li>
          </ul>
        </div>
      </div>
      
      <div className="messaging-container">
        <div className="threads-list">
          <h2>Conversations</h2>
          {threadsList.length === 0 ? (
            <div className="empty-threads">
              <p>No messages yet.</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>
                Messages will appear here when you communicate with tutors.
              </p>
            </div>
          ) : (
            threadsList.map((thread) => (
              <div
                key={thread.id}
                className={`thread-item ${selectedThread?.id === thread.id ? 'active' : ''}`}
                onClick={() => setSelectedThread(thread)}
              >
                <div className="thread-header">
                  <strong>{thread.subject || 'Conversation'}</strong>
                  {thread.status === 'open' && <span className="status-badge">Open</span>}
                </div>
                {thread.last_message && (
                  <p className="thread-preview">{thread.last_message.substring(0, 50)}...</p>
                )}
                <span className="thread-date">
                  {thread.updated_at ? new Date(thread.updated_at).toLocaleDateString() : ''}
                </span>
              </div>
            ))
          )}
        </div>

        <div className="messages-view">
          {currentThread ? (
            <>
              <div className="messages-header">
                <h2>{currentThread.subject || 'Conversation'}</h2>
                <span className={`thread-status thread-status-${currentThread.status}`}>
                  {currentThread.status}
                </span>
              </div>
              
              <div className="messages-list">
                {currentThread.messages?.length > 0 ? (
                  currentThread.messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`message ${msg.sender_id === user.id ? 'sent' : 'received'}`}
                    >
                      <div className="message-content">{msg.content}</div>
                      <div className="message-time">
                        {msg.created_at ? new Date(msg.created_at).toLocaleString() : ''}
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="empty-messages">
                    <p>No messages in this conversation yet.</p>
                  </div>
                )}
              </div>

              <form onSubmit={handleSendMessage} className="message-form">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Type your message..."
                  disabled={sendMessageMutation.isPending}
                />
                <button 
                  type="submit" 
                  disabled={sendMessageMutation.isPending || !newMessage.trim()}
                  className="btn-primary"
                >
                  {sendMessageMutation.isPending ? 'Sending...' : 'Send'}
                </button>
              </form>
            </>
          ) : (
            <div className="no-thread-selected">
              <p>Select a conversation to view messages</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Messaging;

