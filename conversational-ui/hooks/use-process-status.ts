import { useState, useEffect, useRef } from 'react';
import { useSession } from 'next-auth/react';
import { extractRepositoryIndexedEvents } from '@/lib/repository-events';

/**
 * Hook to poll the process status at regular intervals
 * @param processId The ID of the process to poll
 * @param pollInterval The interval in milliseconds between polls (default: 10000ms = 10s)
 * @returns The current status of the process
 */
export function useProcessStatus(
  processId?: string | null | undefined,
  pollInterval: number = 10000
) {
  const { data: session, update } = useSession();
  
  // Determine initial status based on session data internally
  const knowledgeBaseId = session?.user?.selectedSpace?.knowledgeBaseId;
  const initialStatus: 'none' | 'indexing' | 'indexed' = 
    knowledgeBaseId && !processId ? 'indexed' : 'none';
  
  const [status, setStatus] = useState<'none' | 'indexing' | 'indexed'>(initialStatus);
  const intervalIdRef = useRef<NodeJS.Timeout | null>(null);
  const isPollingRef = useRef(false);
  const lastPollTimeRef = useRef<number>(0);
  const errorCountRef = useRef(0);
  const lastProcessIdRef = useRef<string | null | undefined>(processId);
  const lastKnowledgeBaseIdRef = useRef<string | null | undefined>(knowledgeBaseId);
  
  // Update status when session data changes
  useEffect(() => {
    const currentInitialStatus: 'none' | 'indexing' | 'indexed' = 
      knowledgeBaseId && !processId ? 'indexed' : 'none';
    
    const processIdChanged = lastProcessIdRef.current !== processId;
    const knowledgeBaseIdChanged = lastKnowledgeBaseIdRef.current !== knowledgeBaseId;
    
    // Update status if:
    // 1. No processId and we should use the calculated initial status
    // 2. ProcessId changed 
    // 3. KnowledgeBaseId changed (affects whether we show 'indexed' status)
    if (!processId || processIdChanged || knowledgeBaseIdChanged) {
      if (process.env.NODE_ENV === 'development') {
        console.log(`Updating status to: ${currentInitialStatus} (processId: ${processId}, knowledgeBaseId: ${knowledgeBaseId})`);
      }
      setStatus(currentInitialStatus);
    }
    
    lastProcessIdRef.current = processId;
    lastKnowledgeBaseIdRef.current = knowledgeBaseId;
  }, [processId, knowledgeBaseId]);
  
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
      // Only log in development environment
      if (process.env.NODE_ENV === 'development') {
        console.log(`Polling status for process: ${processId}`);
      }
      
      const response = await fetch(`/api/processes/${processId}`);
      
      if (!response.ok) {
        errorCountRef.current += 1;
        
        // Only log errors in development environment
        if (process.env.NODE_ENV === 'development') {
          console.warn(`Failed to fetch process status (attempt ${errorCountRef.current}):`, response.statusText);
        }
        
        // If we've had too many errors, stop polling
        if (errorCountRef.current >= 5) {
          if (process.env.NODE_ENV === 'development') {
            console.warn('Too many polling errors, stopping poll');
          }
          clearIntervalIfExists();
        }
        
        isPollingRef.current = false;
        return;
      }
      
      // Reset error count after successful request
      errorCountRef.current = 0;
      
      const data = await response.json();
      const indexedVersions = extractRepositoryIndexedEvents(data?.events);
     
      // Only log in development environment
      if (process.env.NODE_ENV === 'development') {
        console.log("Full process status API response:", data);
      }
      
      // Get status directly from the API response
      const processStatus = data.status?.toLowerCase() || '';
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`Final extracted process status: "${processStatus}"`);
      }
      
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
      
      if (process.env.NODE_ENV === 'development') {
        console.log(`Mapping API status "${processStatus}" to component status "${newStatus}"`);
      }
      
      // Update the status state
      setStatus(newStatus);
      
      // Update the session with the new status
      if (session?.user?.selectedSpace) {
        try {
          const indexedPayload = indexedVersions.length > 0 ? { indexedVersions } : {};

          await update({
            user: {
              ...session.user,
              selectedSpace: {
                ...session.user.selectedSpace,
                processStatus: newStatus,
                processId: processId || session.user.selectedSpace.processId,
                knowledgeBaseId: session.user.selectedSpace.knowledgeBaseId,
                ...indexedPayload,
              }
            }
          });
          
          if (process.env.NODE_ENV === 'development') {
            console.log("Session update successful");
          }
        } catch (sessionError) {
          if (process.env.NODE_ENV === 'development') {
            console.error("Error updating session:", sessionError);
          }
        }
      }
      
      // If the process is indexed, stop polling
      if (newStatus === 'indexed') {
        clearIntervalIfExists();
      }
      
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error("Error checking process status:", error);
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
  
  // Set up polling when the component mounts or when processId changes
  useEffect(() => {
    // Clear any existing interval
    clearIntervalIfExists();
    
    // If we have a process ID, start polling
    if (processId) {
      // Initial check
      checkProcessStatus();
      
      // Set up interval for subsequent checks
      intervalIdRef.current = setInterval(checkProcessStatus, pollInterval);
    }
    
    // Clean up on unmount or when processId changes
    return () => {
      clearIntervalIfExists();
    };
  }, [processId, pollInterval]);
  
  return status;
} 
