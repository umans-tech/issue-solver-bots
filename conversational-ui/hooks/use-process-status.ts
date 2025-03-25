import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import type { Session } from 'next-auth';

/**
 * Hook to poll the process status at regular intervals
 * @param processId The ID of the process to poll
 * @param initialStatus The initial status of the process
 * @param pollInterval The interval in milliseconds between polls (default: 20000ms = 20s)
 * @returns The current status of the process
 */
export function useProcessStatus(
  processId: string | null | undefined,
  initialStatus: 'none' | 'indexing' | 'indexed' = 'none',
  pollInterval: number = 20000
) {
  const { data: session, update } = useSession();
  const [status, setStatus] = useState<'none' | 'indexing' | 'indexed'>(initialStatus);
  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);
  const lastPollTimeRef = useRef<number>(0);
  const errorCountRef = useRef(0);
  
  // Define the checkProcessStatus function outside the main effect for reuse
  async function checkProcessStatus() {
    // Skip if already polling or if we polled very recently (debounce)
    const now = Date.now();
    if (isPollingRef.current || (now - lastPollTimeRef.current < 5000) || !processId) {
      return;
    }
    
    lastPollTimeRef.current = now;
    isPollingRef.current = true;
    
    try {
      console.log(`Polling status for process: ${processId}`);
      
      const response = await fetch(`/api/processes/${processId}`);
      
      if (!response.ok) {
        errorCountRef.current += 1;
        console.error(`Failed to fetch process status (attempt ${errorCountRef.current}):`, response.statusText);
        
        // If we've had too many errors, stop polling
        if (errorCountRef.current >= 5) {
          console.error('Too many polling errors, stopping poll');
          clearIntervalIfExists();
        }
        
        isPollingRef.current = false;
        return;
      }
      
      // Reset error count after successful request
      errorCountRef.current = 0;
      
      const data = await response.json();
      
      // Log the full response for debugging
      console.log("Full process status API response:", data);
      
      // Get status directly from the API response
      const processStatus = data.status?.toLowerCase() || '';
      console.log(`Final extracted process status: "${processStatus}"`);
      
      // Direct 1:1 mapping from API status to component status
      let newStatus: 'none' | 'indexing' | 'indexed';
      
      if (processStatus === 'indexing' || processStatus === 'connected' || processStatus === 'retrying') {
        newStatus = 'indexing';
      } 
      else if (processStatus === 'indexed') {
        newStatus = 'indexed';
      } 
      else {
        newStatus = 'none';
      }
      
      console.log(`Mapping API status "${processStatus}" to component status "${newStatus}"`);
      
      // Update the status state
      setStatus(newStatus);
      
      // Update the session with the new status
      if (session?.user?.selectedSpace) {
        try {
          await update({
            user: {
              ...session.user,
              selectedSpace: {
                ...session.user.selectedSpace,
                processStatus: newStatus,
                processId: processId || session.user.selectedSpace.processId,
                knowledgeBaseId: session.user.selectedSpace.knowledgeBaseId
              }
            }
          });
          console.log("Session update successful");
        } catch (sessionError) {
          console.error("Error updating session:", sessionError);
        }
      }
      
      // Manage polling interval based on status
      if (newStatus === 'indexing') {
        // Only set up polling if not already polling
        if (!intervalIdRef.current) {
          console.log(`Setting up polling interval: ${pollInterval}ms for indexing status`);
          intervalIdRef.current = setInterval(checkProcessStatus, pollInterval);
        }
      } else if (intervalIdRef.current) {
        // For indexed or none status, stop polling
        console.log(`Stopping polling for ${newStatus} status`);
        clearIntervalIfExists();
      }
    } catch (error) {
      errorCountRef.current += 1;
      console.error(`Error checking process status (attempt ${errorCountRef.current}):`, error);
    }
    
    isPollingRef.current = false;
  }
  
  // Helper function to clear interval if it exists
  function clearIntervalIfExists() {
    if (intervalIdRef.current) {
      clearInterval(intervalIdRef.current);
      intervalIdRef.current = null;
    }
  }
  
  // This effect handles the polling and cleanup
  useEffect(() => {
    // Skip polling if no processId
    if (!processId) {
      setStatus('none');
      clearIntervalIfExists();
      return;
    }
    
    // Run the initial check
    checkProcessStatus();
    
    // Start polling if we have a processId
    if (processId && !intervalIdRef.current) {
      console.log(`Setting up initial polling interval for indexing status`);
      intervalIdRef.current = setInterval(checkProcessStatus, pollInterval);
    }
    
    // Cleanup function to run when component unmounts or deps change
    return () => {
      if (intervalIdRef.current) {
        console.log('Cleaning up polling interval on unmount/deps change');
        clearIntervalIfExists();
      }
    };
  }, [processId, pollInterval]);
  
  return status;
} 