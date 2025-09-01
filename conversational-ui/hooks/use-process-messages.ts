import { useState, useEffect, useRef } from 'react';

/**
 * Hook to poll process messages at regular intervals for real-time updates
 * @param processId The ID of the process to poll messages for
 * @param pollInterval The interval in milliseconds between polls (default: 3000ms = 3s)
 * @param enabled Whether polling is enabled (default: true)
 * @returns Object containing messages, loading state, and error state
 */
export function useProcessMessages(
  processId?: string | null | undefined,
  pollInterval: number = 3000,
  enabled: boolean = true
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

  async function fetchMessages() {
    if (!processId || !enabled) {
      return;
    }

    // Skip if already polling or if we polled very recently (debounce)
    const now = Date.now();
    if (isPollingRef.current || (now - lastPollTimeRef.current) < 1000) {
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
        throw new Error(`Failed to fetch messages: ${response.status} ${response.statusText}`);
      }

      const newMessages = await response.json();
      
      // Sort messages by turn for consistent ordering
      const sortedMessages = newMessages.sort((a: any, b: any) => (a.turn || 0) - (b.turn || 0));
      
      // Only update state if messages have actually changed
      const currentMessageCount = sortedMessages.length;
      const lastMessageCount = lastMessageCountRef.current;
      
      if (currentMessageCount !== lastMessageCount || initialLoad) {
        setMessages(sortedMessages);
        lastMessageCountRef.current = currentMessageCount;
        
        if (process.env.NODE_ENV === 'development') {
          console.log(`Messages updated: ${lastMessageCount} -> ${currentMessageCount} messages`);
        }
      }
      
      setError(null);
      errorCountRef.current = 0;
      
      if (initialLoad) {
        setInitialLoad(false);
        setLoading(false);
      }
      
    } catch (err) {
      console.error('Error fetching process messages:', err);
      
      errorCountRef.current += 1;
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch messages';
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
  }, [processId, pollInterval, enabled]);

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
    refetch: fetchMessages,
  };
}
