import { useEffect, useRef, useState } from 'react';

/**
 * Hook to poll process messages at regular intervals for real-time updates
 * @param processId The ID of the process to poll messages for
 * @param pollInterval The interval in milliseconds between polls (default: 3000ms = 3s)
 * @param enabled Whether polling is enabled (default: true)
 * @param onProcessDataUpdate Optional callback to receive full process data updates
 * @returns Object containing messages, loading state, and error state
 */
export function useProcessMessages(
  processId?: string | null | undefined,
  pollInterval = 3000,
  enabled = true,
  onProcessDataUpdate?: (processData: any) => void,
) {
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialLoad, setInitialLoad] = useState(true);

  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);
  const lastPollTimeRef = useRef<number>(0);
  const errorCountRef = useRef(0);
  const lastProcessIdRef = useRef<string | null | undefined>(processId);
  const lastMessageCountRef = useRef<number>(0);
  const lastStatusCheckRef = useRef<number>(0);
  const currentStatusRef = useRef<string | null>(null);

  // Helper function to check if process is in terminal state
  const isTerminalState = (status?: string): boolean => {
    if (!status) return false;
    const terminalStates = ['completed', 'success', 'failed', 'error'];
    return terminalStates.includes(status.toLowerCase());
  };

  async function fetchMessages() {
    if (!processId || !enabled) {
      return;
    }

    // Skip if already polling or if we polled very recently (debounce)
    const now = Date.now();
    if (isPollingRef.current || now - lastPollTimeRef.current < 1000) {
      return;
    }

    // Stop polling if we know the process is in terminal state
    if (currentStatusRef.current && isTerminalState(currentStatusRef.current)) {
      clearIntervalIfExists();
      if (process.env.NODE_ENV === 'development') {
        console.log(
          `Process ${processId} is in terminal state: ${currentStatusRef.current}. Stopping message polling.`,
        );
      }
      return;
    }

    try {
      isPollingRef.current = true;
      lastPollTimeRef.current = now;

      if (initialLoad) {
        setLoading(true);
      }

      const response = await fetch(`/api/processes/${processId}/messages`);

      if (!response.ok) {
        throw new Error(
          `Failed to fetch messages: ${response.status} ${response.statusText}`,
        );
      }

      const newMessages = await response.json();

      // Sort messages by turn for consistent ordering
      const sortedMessages = newMessages.sort(
        (a: any, b: any) => (a.turn || 0) - (b.turn || 0),
      );

      // Only update state if messages have actually changed
      const currentMessageCount = sortedMessages.length;
      const lastMessageCount = lastMessageCountRef.current;

      if (currentMessageCount !== lastMessageCount || initialLoad) {
        setMessages(sortedMessages);
        lastMessageCountRef.current = currentMessageCount;

        if (process.env.NODE_ENV === 'development') {
          console.log(
            `Messages updated: ${lastMessageCount} -> ${currentMessageCount} messages`,
          );
        }
      }

      setError(null);
      errorCountRef.current = 0;

      if (initialLoad) {
        setInitialLoad(false);
        setLoading(false);
      }

      // Occasionally check process status (every 4th poll, roughly every 12 seconds)
      const shouldCheckStatus = now - lastStatusCheckRef.current > 12000;
      if (shouldCheckStatus) {
        try {
          const statusResponse = await fetch(`/api/processes/${processId}`);
          if (statusResponse.ok) {
            const processData = await statusResponse.json();
            const newStatus = processData.status;

            if (newStatus && newStatus !== currentStatusRef.current) {
              currentStatusRef.current = newStatus;
              lastStatusCheckRef.current = now;

              // Notify parent component of process data update
              if (onProcessDataUpdate) {
                onProcessDataUpdate(processData);
              }

              if (process.env.NODE_ENV === 'development') {
                console.log(`Process status updated: ${newStatus}`);
              }

              // Stop polling if terminal state reached
              if (isTerminalState(newStatus)) {
                clearIntervalIfExists();
                if (process.env.NODE_ENV === 'development') {
                  console.log(
                    `Process ${processId} reached terminal state: ${newStatus}. Stopping polling.`,
                  );
                }
              }
            }
          }
        } catch (statusError) {
          // Don't fail message polling if status check fails
          if (process.env.NODE_ENV === 'development') {
            console.warn('Failed to check process status:', statusError);
          }
        }
      }
    } catch (err) {
      console.error('Error fetching process messages:', err);

      errorCountRef.current += 1;
      const errorMessage =
        err instanceof Error ? err.message : 'Failed to fetch messages';
      setError(errorMessage);

      if (initialLoad) {
        setLoading(false);
        setInitialLoad(false);
      }

      // Exponential backoff for errors
      if (errorCountRef.current >= 3) {
        clearIntervalIfExists();
        if (process.env.NODE_ENV === 'development') {
          console.log('Stopping message polling due to repeated errors');
        }
      }
    } finally {
      isPollingRef.current = false;
    }
  }

  // Function to clear the interval if it exists
  function clearIntervalIfExists() {
    if (intervalIdRef.current) {
      clearInterval(intervalIdRef.current);
      intervalIdRef.current = null;
    }
  }

  // Reset state when processId changes
  useEffect(() => {
    if (lastProcessIdRef.current !== processId) {
      lastProcessIdRef.current = processId;
      setMessages([]);
      setError(null);
      setInitialLoad(true);
      errorCountRef.current = 0;
      lastMessageCountRef.current = 0;
      lastStatusCheckRef.current = 0;
      currentStatusRef.current = null;
      clearIntervalIfExists();
    }
  }, [processId]);

  // Set up polling when the component mounts or when processId/enabled changes
  useEffect(() => {
    if (!processId || !enabled) {
      clearIntervalIfExists();
      return;
    }

    // Initial fetch
    fetchMessages();

    // Set up polling interval
    intervalIdRef.current = setInterval(fetchMessages, pollInterval);

    // Cleanup on unmount or dependency change
    return () => {
      clearIntervalIfExists();
    };
  }, [processId, pollInterval, enabled, onProcessDataUpdate]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearIntervalIfExists();
    };
  }, []);

  return {
    messages,
    loading,
    error,
    currentStatus: currentStatusRef.current,
    isTerminal: currentStatusRef.current
      ? isTerminalState(currentStatusRef.current)
      : false,
    refetch: fetchMessages,
  };
}
