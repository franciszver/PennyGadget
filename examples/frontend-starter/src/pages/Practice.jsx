import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Practice.css';

function Practice() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [selectedSubject, setSelectedSubject] = useState('Math');
  const [currentAssignment, setCurrentAssignment] = useState(null);
  const [answer, setAnswer] = useState('');

  const assignMutation = useMutation({
    mutationFn: (data) => api.assignPractice(data),
    onSuccess: (response) => {
      setCurrentAssignment(response.data.data);
      success('Practice assignment loaded!');
    },
    onError: (err) => {
      console.error('[PRACTICE] Assignment error:', err);
      showError('Failed to load practice. Backend may not be running.');
    },
  });

  const completeMutation = useMutation({
    mutationFn: ({ assignmentId, data }) => 
      api.completePractice(assignmentId, data),
    onSuccess: () => {
      success('Practice completed! Great job!');
      setCurrentAssignment(null);
      setAnswer('');
    },
    onError: (err) => {
      console.error('[PRACTICE] Completion error:', err);
      showError('Failed to submit answer. Backend may not be running.');
    },
  });

  const handleStartPractice = () => {
    assignMutation.mutate({
      student_id: user.id,
      subject: selectedSubject,
      difficulty_level: 5,
    });
  };

  const handleSubmit = () => {
    if (!currentAssignment || !answer) return;
    
    completeMutation.mutate({
      assignmentId: currentAssignment.assignment_id,
      data: {
        student_answer: answer,
        time_spent_seconds: 300,
      },
    });
  };

  if (!currentAssignment) {
    return (
      <div className="practice">
        <h1>Practice Assignment</h1>
        {assignMutation.isPending ? (
          <LoadingSpinner message="Loading practice question..." />
        ) : (
          <div className="practice-setup">
            <label>
              Subject:
              <select 
                value={selectedSubject} 
                onChange={(e) => setSelectedSubject(e.target.value)}
              >
                <option value="Math">Math</option>
                <option value="Science">Science</option>
                <option value="English">English</option>
              </select>
            </label>
            <button onClick={handleStartPractice} disabled={assignMutation.isPending}>
              Start Practice
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="practice">
      <h1>Practice Question</h1>
      <div className="practice-question">
        <h2>{currentAssignment.question_text}</h2>
        <textarea
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Enter your answer..."
          rows={5}
        />
        <button onClick={handleSubmit} disabled={completeMutation.isPending}>
          {completeMutation.isPending ? 'Submitting...' : 'Submit Answer'}
        </button>
      </div>
    </div>
  );
}

export default Practice;

