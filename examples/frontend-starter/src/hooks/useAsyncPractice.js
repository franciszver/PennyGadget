import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '../services/apiClient';

/**
 * Hook for async practice assignment with WebSocket and polling fallback
 * 
 * Usage:
 *   const { startJob, status, result, error, progress } = useAsyncPractice();
 *   
 *   // Start job
 *   startJob({ student_id, subject, num_items: 5 });
 *   
 *   // Check status
 *   if (status === 'completed') {
 *     // Use result.data
 *   }
 */
export function useAsyncPractice() {
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null); // pending, processing, completed, failed
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState({ percent: 0, message: '' });

  const wsRef = useRef(null);
  const pollIntervalRef = useRef(null);
  const useWebSocketRef = useRef(true); // Try WebSocket first, fallback to polling
  const jobCompletedRef = useRef(false); // Track if job finished (avoids stale closure issues)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Connect via WebSocket
  const connectWebSocket = useCallback((jobId) => {
    if (!useWebSocketRef.current) return; // Already failed, skip WebSocket

    try {
      // Get WebSocket URL from API base URL
      const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || window.location.origin;
      const wsProtocol = apiBaseUrl.startsWith('https') ? 'wss' : 'ws';
      // Remove /api/v1 suffix if present (we'll add it back in the path)
      const wsBaseUrl = apiBaseUrl.replace(/^https?/, wsProtocol).replace(/\/api\/v1\/?$/, '');
      const wsUrl = `${wsBaseUrl}/api/v1/jobs/${jobId}/ws`;

      console.log('[ASYNC_PRACTICE] Connecting to WebSocket:', wsUrl);

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('[ASYNC_PRACTICE] WebSocket connected');
        setStatus('processing');
      };

      ws.onmessage = (event) => {
        try {
          const update = JSON.parse(event.data);
          console.log('[ASYNC_PRACTICE] WebSocket update:', update);

          switch (update.type) {
            case 'status':
              // Handle status updates - check if it's actually a completion status
              if (update.status === 'completed') {
                // Some backends send status type with completed status before the completed type
                // Don't mark as completed here - wait for the completed type with result
                setProgress({
                  percent: update.progress_percent || 100,
                  message: update.progress_message || 'Complete!'
                });
              } else {
                setStatus('processing');
                setProgress({
                  percent: update.progress_percent || 0,
                  message: update.progress_message || ''
                });
              }
              break;

            case 'completed':
              jobCompletedRef.current = true; // Mark as completed synchronously
              setStatus('completed');
              setProgress({ percent: 100, message: 'Complete!' });
              setResult(update.result);
              ws.close();
              break;

            case 'failed':
              jobCompletedRef.current = true; // Mark as done
              setStatus('failed');
              setError(update.error || 'Job failed');
              ws.close();
              break;

            case 'error':
              jobCompletedRef.current = true; // Mark as done
              setStatus('failed');
              setError(update.message || 'WebSocket error');
              ws.close();
              break;
          }
        } catch (err) {
          console.error('[ASYNC_PRACTICE] Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (err) => {
        console.warn('[ASYNC_PRACTICE] WebSocket error, falling back to polling:', err);
        useWebSocketRef.current = false;
        ws.close();
        // Fallback to polling only if not already completed
        if (!jobCompletedRef.current) {
          startPolling(jobId);
        }
      };

      ws.onclose = () => {
        console.log('[ASYNC_PRACTICE] WebSocket closed');
        wsRef.current = null;
        // If not completed/failed, start polling as fallback (use ref for sync check)
        if (!jobCompletedRef.current) {
          startPolling(jobId);
        }
      };

    } catch (err) {
      console.warn('[ASYNC_PRACTICE] WebSocket not available, using polling:', err);
      useWebSocketRef.current = false;
      startPolling(jobId);
    }
  }, [status]);

  // Poll job status (fallback)
  const startPolling = useCallback((jobId) => {
    // Don't start polling if already completed
    if (jobCompletedRef.current) {
      console.log('[ASYNC_PRACTICE] Skipping polling - job already completed');
      return;
    }

    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    console.log('[ASYNC_PRACTICE] Starting polling for job:', jobId);

    const poll = async () => {
      // Stop polling if job completed via another mechanism
      if (jobCompletedRef.current) {
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
        return;
      }

      try {
        const response = await api.getJobStatus(jobId);
        const jobData = response.data.data;

        setStatus(jobData.status);
        setProgress({
          percent: jobData.progress_percent || 0,
          message: jobData.progress_message || ''
        });

        if (jobData.status === 'completed') {
          jobCompletedRef.current = true;
          setResult(jobData.result);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } else if (jobData.status === 'failed') {
          jobCompletedRef.current = true;
          setError(jobData.error || 'Job failed');
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        }
      } catch (err) {
        console.error('[ASYNC_PRACTICE] Polling error:', err);
        // Continue polling on error (might be temporary)
      }
    };

    // Poll immediately, then every 2 seconds
    poll();
    pollIntervalRef.current = setInterval(poll, 2000);
  }, []);

  // Start async practice job
  const startJob = useCallback(async (params) => {
    // Reset state
    setJobId(null);
    setStatus(null);
    setResult(null);
    setError(null);
    setProgress({ percent: 0, message: '' });
    useWebSocketRef.current = true; // Reset WebSocket preference
    jobCompletedRef.current = false; // Reset completion flag

    try {
      console.log('[ASYNC_PRACTICE] Starting async practice job:', params);
      const response = await api.assignPracticeAsync(params);
      const data = response.data;

      if (data.success && data.job_id) {
        const newJobId = data.job_id;
        setJobId(newJobId);
        setStatus('pending');

        // Try WebSocket first, fallback to polling
        connectWebSocket(newJobId);

        return { success: true, jobId: newJobId };
      } else {
        throw new Error(data.message || 'Failed to start job');
      }
    } catch (err) {
      console.error('[ASYNC_PRACTICE] Error starting job:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to start practice job');
      setStatus('failed');
      return { success: false, error: err.message };
    }
  }, [connectWebSocket]);

  // Reset hook state
  const reset = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
      pollIntervalRef.current = null;
    }
    jobCompletedRef.current = false;
    setJobId(null);
    setStatus(null);
    setResult(null);
    setError(null);
    setProgress({ percent: 0, message: '' });
  }, []);

  return {
    jobId,
    status, // pending, processing, completed, failed
    result, // Full result object when completed
    error,  // Error message if failed
    progress, // { percent: 0-100, message: string }
    startJob,
    reset,
    isLoading: status === 'pending' || status === 'processing',
    isCompleted: status === 'completed',
    isFailed: status === 'failed'
  };
}

