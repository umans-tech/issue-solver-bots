import { useEffect, useRef, type RefObject } from 'react';

export function useScrollToBottom<T extends HTMLElement>(): [
  RefObject<T | null>,
  RefObject<T | null>,
] {
  const containerRef = useRef<T | null>(null);
  const endRef = useRef<T | null>(null);
  const isNearBottom = useRef(true);

  useEffect(() => {
    const container = containerRef.current;
    const end = endRef.current;

    if (!container || !end) return;

    // Check if we're near the bottom
    const checkIfNearBottom = () => {
      if (!container) return false;
      const distanceFromBottom = 
        container.scrollHeight - container.scrollTop - container.clientHeight;
      // If we're already following (near bottom), use a larger threshold
      // to prevent stopping the scroll
      const threshold = isNearBottom.current ? 300 : 100;
      isNearBottom.current = distanceFromBottom < threshold;
      return isNearBottom.current;
    };

    // Scroll handler to update isNearBottom state
    const handleScroll = () => {
      checkIfNearBottom();
    };

    container.addEventListener('scroll', handleScroll);

    const observer = new MutationObserver(() => {
      // Use requestAnimationFrame to ensure DOM is updated
      requestAnimationFrame(() => {
        if (checkIfNearBottom()) {
          end.scrollIntoView({ behavior: 'smooth', block: 'end' });
        }
      });
    });

    observer.observe(container, {
      childList: true,
      subtree: true,
      characterData: true,
    });

    return () => {
      observer.disconnect();
      container.removeEventListener('scroll', handleScroll);
    };
  }, []);

  return [containerRef, endRef];
}
