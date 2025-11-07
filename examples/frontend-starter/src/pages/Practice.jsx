import { useState, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import { useToast } from '../contexts/ToastContext';
import { api } from '../services/apiClient';
import LoadingSpinner from '../components/LoadingSpinner';
import './Practice.css';

function Practice() {
  const { user } = useAuth();
  const { success, error: showError } = useToast();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const subjectFromUrl = searchParams.get('subject');

  // Fetch user's progress to get goals and suggestions
  const { data: progressData, isLoading: progressLoading } = useQuery({
    queryKey: ['progress', user?.id],
    queryFn: () => api.getProgress(user.id).then(res => res.data),
    enabled: !!user?.id,
  });

  // Build list of available subjects from goals and suggestions
  const availableSubjects = useMemo(() => {
    const subjectsSet = new Set();
    const progress = progressData?.data || {};

    // Add subjects from goals
    if (progress.goals) {
      progress.goals.forEach(goal => {
        if (goal.subject && goal.subject !== 'Unknown') {
          subjectsSet.add(goal.subject);
        }
      });
    }

    // Add subjects from suggestions
    if (progress.suggestions) {
      progress.suggestions.forEach(suggestion => {
        if (suggestion.subjects && Array.isArray(suggestion.subjects)) {
          suggestion.subjects.forEach(subject => {
            if (subject) {
              subjectsSet.add(subject);
            }
          });
        }
      });
    }

    // Convert to sorted array
    const subjects = Array.from(subjectsSet).sort();
    
    // If no subjects found, provide default options
    if (subjects.length === 0) {
      return ['Math', 'Science', 'English'];
    }

    return subjects;
  }, [progressData]);

  // Set initial subject from URL or first available subject
  const [selectedSubject, setSelectedSubject] = useState(() => {
    if (subjectFromUrl && availableSubjects.includes(subjectFromUrl)) {
      return subjectFromUrl;
    }
    return availableSubjects[0] || 'Math';
  });

  // Update selected subject when URL param changes or available subjects change
  useEffect(() => {
    if (subjectFromUrl && availableSubjects.includes(subjectFromUrl)) {
      setSelectedSubject(subjectFromUrl);
    } else if (availableSubjects.length > 0 && !availableSubjects.includes(selectedSubject)) {
      // If current selection is not in available subjects, switch to first available
      setSelectedSubject(availableSubjects[0]);
    }
  }, [subjectFromUrl, availableSubjects]);

  // Handle returning from QA - restore practice state and move to next question
  const questionIndexFromUrl = searchParams.get('questionIndex');
  useEffect(() => {
    // Try to restore practice session from localStorage
    const savedState = localStorage.getItem('practice_session_state');
    if (savedState && questionIndexFromUrl) {
      try {
        const state = JSON.parse(savedState);
        if (state.allItems && state.allItems.length > 0) {
          // Restore all state
          setAllItems(state.allItems);
          setAttempts(state.attempts || {});
          setCompletedQuestions(state.completedQuestions || {});
          
          const index = parseInt(questionIndexFromUrl, 10);
          if (index >= 0 && index < state.allItems.length) {
            // Move to next question (since they already answered this one correctly)
            const nextIndex = index + 1;
            if (nextIndex < state.allItems.length) {
              setCurrentIndex(nextIndex);
              setSelectedChoice('');
              setQuestionState('answering');
              // Update start time for the next question
              const newItems = [...state.allItems];
              newItems[nextIndex].start_time = Date.now();
              setAllItems(newItems);
            } else {
              // No more questions, calculate and show summary
              const totalQuestions = state.allItems.length;
              const correctCount = Object.values(state.completedQuestions || {}).filter(q => q && q.correct).length;
              const incorrectCount = totalQuestions - correctCount;
              const totalAttempts = Object.values(state.attempts || {}).reduce((sum, count) => sum + count, 0);
              const averageAttempts = totalQuestions > 0 ? totalAttempts / totalQuestions : 0;
              const needsTutorHelp = totalQuestions > 0 && ((correctCount / totalQuestions) < 0.5 || averageAttempts > 2);
              
              setSummaryData({
                totalQuestions,
                correctCount,
                incorrectCount,
                totalAttempts,
                averageAttempts: averageAttempts.toFixed(1),
                needsTutorHelp,
                completedQuestions: state.completedQuestions || {}
              });
              setShowSummary(true);
            }
          }
          
          // Clear saved state and URL param
          localStorage.removeItem('practice_session_state');
          const newParams = new URLSearchParams(searchParams);
          newParams.delete('questionIndex');
          navigate(`/practice${newParams.toString() ? '?' + newParams.toString() : ''}`, { replace: true });
        }
      } catch (e) {
        console.error('Failed to restore practice state:', e);
        localStorage.removeItem('practice_session_state');
      }
    }
  }, [questionIndexFromUrl, navigate, searchParams]);

  // Practice state
  const [allItems, setAllItems] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedChoice, setSelectedChoice] = useState('');
  const [questionState, setQuestionState] = useState('answering'); // 'answering', 'correct', 'incorrect'
  const [attempts, setAttempts] = useState({}); // Track attempts per question
  const [completedQuestions, setCompletedQuestions] = useState({}); // Track completed questions
  const [showSummary, setShowSummary] = useState(false);
  const [summaryData, setSummaryData] = useState(null);

  const currentItem = allItems[currentIndex];
  const currentAttempts = attempts[currentIndex] || 0;

  const assignMutation = useMutation({
    mutationFn: (data) => api.assignPractice(data),
    onSuccess: (response) => {
      const practiceData = response.data?.data || response.data;
      
      if (!practiceData || !practiceData.items || practiceData.items.length === 0) {
        showError('No practice items were returned. Please try again.');
        return;
      }
      
      // Initialize all items
      const items = practiceData.items.map((item, idx) => ({
        assignment_id: practiceData.assignment_id,
        item_id: item.item_id,
        question_text: item.question || item.question_text,
        answer_text: item.answer || item.answer_text,
        choices: item.choices || [],
        correct_answer: item.correct_answer || "A",
        explanation: item.explanation,
        difficulty: item.difficulty,
        source: item.source,
        start_time: Date.now(),
        index: idx
      }));

      setAllItems(items);
      setCurrentIndex(0);
      setSelectedChoice('');
      setQuestionState('answering');
      setAttempts({});
      setCompletedQuestions({});
      setShowSummary(false);
      setSummaryData(null);
      
      success('Practice assignment loaded!');
    },
    onError: (err) => {
      console.error('[PRACTICE] Assignment error:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to load practice. Backend may not be running.';
      showError(errorMessage);
    },
  });

  const completeMutation = useMutation({
    mutationFn: ({ assignmentId, itemId, data, isCorrect }) => 
      api.completePractice(assignmentId, itemId, data).then(response => ({
        ...response,
        _isCorrect: isCorrect
      })),
    onSuccess: (response, variables) => {
      const result = response.data?.data || {};
      const isCorrect = response._isCorrect !== undefined ? response._isCorrect : false;
      
      // Update attempts
      const newAttempts = { ...attempts };
      newAttempts[currentIndex] = (newAttempts[currentIndex] || 0) + 1;
      setAttempts(newAttempts);

      // Mark question as completed
      const newCompleted = { ...completedQuestions };
      newCompleted[currentIndex] = {
        correct: isCorrect,
        attempts: newAttempts[currentIndex],
        itemId: variables.itemId
      };
      setCompletedQuestions(newCompleted);

      if (isCorrect) {
        setQuestionState('correct');
        success('Correct! Great job! 🎉');
      } else {
        setQuestionState('incorrect');
        showError('Incorrect. Try again!');
      }
    },
    onError: (err) => {
      console.error('[PRACTICE] Completion error:', err);
      const errorMessage = err.response?.data?.detail || 'Failed to submit answer. Please try again.';
      showError(errorMessage);
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
    if (!currentItem || !selectedChoice) {
      showError('Please select an answer before submitting.');
      return;
    }
    
    // Extract the letter from selected choice (e.g., "A" from "A) Option text")
    const selectedLetter = selectedChoice.charAt(0).toUpperCase();
    const isCorrect = selectedLetter === (currentItem.correct_answer || 'A').toUpperCase();
    
    // Track start time for time calculation
    const startTime = currentItem.start_time || Date.now();
    const timeSpent = Math.floor((Date.now() - startTime) / 1000);
    
    completeMutation.mutate({
      assignmentId: currentItem.assignment_id,
      itemId: currentItem.item_id,
      isCorrect: isCorrect,
      data: {
        student_answer: selectedChoice,
        correct: isCorrect,
        time_taken_seconds: timeSpent,
        hints_used: 0,
      },
    });
  };

  const handleNext = () => {
    if (currentIndex < allItems.length - 1) {
      setCurrentIndex(currentIndex + 1);
      setSelectedChoice('');
      setQuestionState('answering');
      // Update start time for new question
      const newItems = [...allItems];
      newItems[currentIndex + 1].start_time = Date.now();
      setAllItems(newItems);
    }
  };

  const handleDiveDeeper = () => {
    // Save practice state to localStorage before navigating
    const practiceState = {
      allItems,
      currentIndex,
      attempts,
      completedQuestions,
      selectedSubject
    };
    localStorage.setItem('practice_session_state', JSON.stringify(practiceState));
    
    // Navigate to QA with the question preloaded
    const questionText = currentItem.question_text;
    const explanation = currentItem.explanation || '';
    
    // Create a query that asks for deeper explanation
    const deeperQuery = `Can you provide a deeper explanation of this practice question: "${questionText}"${explanation ? ` The current explanation is: "${explanation}".` : ''} Please provide more context, examples, and help me understand the underlying concepts better.`;
    
    // Navigate to QA with preloaded query and return info
    navigate(`/qa?preload=${encodeURIComponent(deeperQuery)}&returnTo=practice&questionIndex=${currentIndex}&subject=${encodeURIComponent(selectedSubject)}`);
  };

  const handleDone = () => {
    // Calculate summary
    const totalQuestions = allItems.length;
    const correctCount = Object.values(completedQuestions).filter(q => q.correct).length;
    const incorrectCount = totalQuestions - correctCount;
    const totalAttempts = Object.values(attempts).reduce((sum, count) => sum + count, 0);
    const averageAttempts = totalAttempts / totalQuestions;

    // Determine if tutor notification is needed
    // Criteria: Less than 50% correct OR average attempts > 2
    const needsTutorHelp = (correctCount / totalQuestions) < 0.5 || averageAttempts > 2;

    setSummaryData({
      totalQuestions,
      correctCount,
      incorrectCount,
      totalAttempts,
      averageAttempts: averageAttempts.toFixed(1),
      needsTutorHelp,
      completedQuestions
    });
    setShowSummary(true);
  };

  const handleFinishPractice = () => {
    // Reset everything
    setAllItems([]);
    setCurrentIndex(0);
    setSelectedChoice('');
    setQuestionState('answering');
    setAttempts({});
    setCompletedQuestions({});
    setShowSummary(false);
    setSummaryData(null);
  };

  if (progressLoading) {
    return (
      <div className="practice">
        <LoadingSpinner message="Loading practice options..." />
      </div>
    );
  }

  // Show summary report
  if (showSummary && summaryData) {
    return (
      <div className="practice">
        <div className="practice-summary" style={{
          maxWidth: '600px',
          margin: '2rem auto',
          padding: '2rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <h1>Practice Summary</h1>
          
          <div style={{ marginTop: '1.5rem' }}>
            <h2>Your Results</h2>
            <div style={{ 
              display: 'grid', 
              gridTemplateColumns: '1fr 1fr', 
              gap: '1rem',
              marginTop: '1rem'
            }}>
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#d4edda', 
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#155724' }}>
                  {summaryData.correctCount}
                </div>
                <div style={{ color: '#155724' }}>Correct</div>
              </div>
              <div style={{ 
                padding: '1rem', 
                backgroundColor: '#f8d7da', 
                borderRadius: '4px',
                textAlign: 'center'
              }}>
                <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#721c24' }}>
                  {summaryData.incorrectCount}
                </div>
                <div style={{ color: '#721c24' }}>Incorrect</div>
              </div>
            </div>

            <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: 'white', borderRadius: '4px' }}>
              <p><strong>Total Questions:</strong> {summaryData.totalQuestions}</p>
              <p><strong>Average Attempts per Question:</strong> {summaryData.averageAttempts}</p>
              <p><strong>Accuracy:</strong> {((summaryData.correctCount / summaryData.totalQuestions) * 100).toFixed(1)}%</p>
            </div>

            {summaryData.needsTutorHelp && (
              <div style={{
                marginTop: '1.5rem',
                padding: '1rem',
                backgroundColor: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '4px'
              }}>
                <p style={{ margin: 0, fontWeight: '500', color: '#856404' }}>
                  ⚠️ Your tutor has been notified to provide additional support. 
                  Your progress will be updated accordingly.
                </p>
              </div>
            )}

            <div style={{ marginTop: '1.5rem', padding: '1rem', backgroundColor: '#d1ecf1', borderRadius: '4px' }}>
              <p style={{ margin: 0, color: '#0c5460' }}>
                ✓ Your progress has been saved and will be reflected in your dashboard.
              </p>
            </div>

            <button
              onClick={handleFinishPractice}
              style={{
                marginTop: '2rem',
                padding: '0.75rem 2rem',
                fontSize: '1rem',
                backgroundColor: '#007bff',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '500',
                width: '100%'
              }}
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Show practice setup
  if (allItems.length === 0) {
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
                style={{ minWidth: '200px' }}
              >
                {availableSubjects.map(subject => (
                  <option key={subject} value={subject}>
                    {subject}
                  </option>
                ))}
              </select>
            </label>
            {availableSubjects.length === 0 && (
              <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                No subjects available. Create a goal or check your progress for suggestions.
              </p>
            )}
            <button 
              onClick={handleStartPractice} 
              disabled={assignMutation.isPending || availableSubjects.length === 0}
            >
              Start Practice
            </button>
          </div>
        )}
      </div>
    );
  }

  // Show current question
  return (
    <div className="practice">
      <div style={{ marginBottom: '1rem', fontSize: '0.875rem', color: '#666' }}>
        Question {currentIndex + 1} of {allItems.length}
      </div>
      
      <div className="practice-question">
        <h2>{currentItem.question_text}</h2>
        
        {questionState === 'correct' && currentItem.explanation && (
          <div style={{
            marginTop: '1.5rem',
            padding: '1rem',
            backgroundColor: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '4px'
          }}>
            <h3 style={{ marginTop: 0, color: '#155724' }}>Explanation:</h3>
            <p style={{ margin: 0, color: '#155724' }}>{currentItem.explanation}</p>
          </div>
        )}

        {questionState === 'incorrect' && (
          <div style={{
            marginTop: '1.5rem',
            padding: '1rem',
            backgroundColor: '#f8d7da',
            border: '1px solid #f5c6cb',
            borderRadius: '4px',
            color: '#721c24',
            marginBottom: '1rem'
          }}>
            <p style={{ margin: 0, fontWeight: '500' }}>
              Incorrect. Try again! (Attempt {currentAttempts})
            </p>
          </div>
        )}

        {(questionState === 'answering' || questionState === 'incorrect') && currentItem.choices && currentItem.choices.length > 0 && (
          <div style={{ marginTop: questionState === 'incorrect' ? '0' : '1.5rem' }}>
            <p style={{ fontWeight: '500', marginBottom: '1rem' }}>Select your answer:</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {currentItem.choices.map((choice, idx) => {
                const isSelected = selectedChoice === choice;
                return (
                  <label
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.75rem',
                      border: `2px solid ${isSelected ? '#007bff' : '#ddd'}`,
                      borderRadius: '8px',
                      cursor: 'pointer',
                      backgroundColor: isSelected ? '#f0f8ff' : 'white',
                      transition: 'all 0.2s'
                    }}
                    onMouseEnter={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.borderColor = '#007bff';
                        e.currentTarget.style.backgroundColor = '#f8f9fa';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isSelected) {
                        e.currentTarget.style.borderColor = '#ddd';
                        e.currentTarget.style.backgroundColor = 'white';
                      }
                    }}
                  >
                    <input
                      type="radio"
                      name="practice-answer"
                      value={choice}
                      checked={selectedChoice === choice}
                      onChange={(e) => {
                        setSelectedChoice(e.target.value);
                        // Reset to answering state when user selects a new answer
                        if (questionState === 'incorrect') {
                          setQuestionState('answering');
                        }
                      }}
                      style={{ marginRight: '0.75rem', width: '20px', height: '20px', cursor: 'pointer' }}
                    />
                    <span style={{ fontSize: '1rem', flex: 1 }}>{choice}</span>
                  </label>
                );
              })}
            </div>
          </div>
        )}

        <div style={{ 
          marginTop: '1.5rem', 
          display: 'flex', 
          gap: '1rem',
          alignItems: 'center'
        }}>
          {(questionState === 'answering' || questionState === 'incorrect') && (
            <button 
              onClick={handleSubmit} 
              disabled={completeMutation.isPending || !selectedChoice}
              style={{
                padding: '0.75rem 2rem',
                fontSize: '1rem',
                backgroundColor: selectedChoice ? '#007bff' : '#ccc',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: selectedChoice ? 'pointer' : 'not-allowed',
                fontWeight: '500'
              }}
            >
              {completeMutation.isPending ? 'Submitting...' : 'Submit Answer'}
            </button>
          )}

          {questionState === 'correct' && (
            <>
              <button
                onClick={handleDiveDeeper}
                style={{
                  padding: '0.75rem 2rem',
                  fontSize: '1rem',
                  backgroundColor: '#17a2b8',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Pause, Dive Deeper
              </button>
              {currentIndex < allItems.length - 1 ? (
                <button
                  onClick={handleNext}
                  style={{
                    padding: '0.75rem 2rem',
                    fontSize: '1rem',
                    backgroundColor: '#28a745',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontWeight: '500'
                  }}
                >
                  Next Question →
                </button>
              ) : null}
              <button
                onClick={handleDone}
                style={{
                  padding: '0.75rem 2rem',
                  fontSize: '1rem',
                  backgroundColor: '#6c757d',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontWeight: '500'
                }}
              >
                Done
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default Practice;
