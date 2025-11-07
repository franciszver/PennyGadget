import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './QA.css';

function QA() {
  const { user } = useAuth();
  const [query, setQuery] = useState('');
  const [conversation, setConversation] = useState([]);

  const { success, error: showError } = useToast();
  
  const queryMutation = useMutation({
    mutationFn: (data) => api.submitQuery(data),
    onSuccess: (response) => {
      const result = response.data.data;
      setConversation([
        ...conversation,
        { type: 'user', content: query },
        { 
          type: 'assistant', 
          content: result.answer,
          confidence: result.confidence,
        },
      ]);
      setQuery('');
      if (result.confidence === 'High') {
        success('Got a high-confidence answer!');
      }
    },
    onError: (err) => {
      console.error('[QA] Query error:', err);
      showError('Failed to get answer. Backend may not be running.');
    },
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    queryMutation.mutate({
      student_id: user.id,
      query: query,
      context: {},
    });
  };

  return (
    <div className="qa">
      <h1>Ask a Question</h1>
      
      {queryMutation.isPending && conversation.length === 0 && (
        <LoadingSpinner message="Thinking..." />
      )}
      
      <div className="qa-conversation">
        {conversation.length === 0 && !queryMutation.isPending && (
          <div className="qa-empty">
            <p>Start a conversation by asking a question below!</p>
            <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
              Try: "How do I solve quadratic equations?" or "Explain photosynthesis"
            </p>
          </div>
        )}
        {conversation.map((msg, idx) => (
          <div key={idx} className={`qa-message ${msg.type}`}>
            <div className="qa-content">{msg.content}</div>
            {msg.confidence && (
              <div className="qa-confidence">
                Confidence: <span className={`confidence-${msg.confidence.toLowerCase()}`}>
                  {msg.confidence}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={handleSubmit} className="qa-form">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask your question..."
          disabled={queryMutation.isPending}
        />
        <button type="submit" disabled={queryMutation.isPending || !query.trim()}>
          {queryMutation.isPending ? 'Thinking...' : 'Ask'}
        </button>
      </form>
    </div>
  );
}

export default QA;

