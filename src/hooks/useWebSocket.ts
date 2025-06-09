
import { useEffect, useRef, useState } from 'react';

interface WebSocketHook<T = unknown> {
  socket: WebSocket | null;
  isConnected: boolean;
  error: string | null;
  sendMessage: (message: T) => void;
}

export const useWebSocket = <T = unknown>(
  url: string,
  onMessage?: (data: T) => void
): WebSocketHook<T> => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const socket = new WebSocket(url);
        
        socket.onopen = () => {
          console.log('WebSocket connected');
          setIsConnected(true);
          setError(null);
        };
        
        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as T;
            onMessage?.(data);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };
        
        socket.onclose = () => {
          console.log('WebSocket disconnected');
          setIsConnected(false);
          // Attempt to reconnect after 3 seconds
          setTimeout(connectWebSocket, 3000);
        };
        
        socket.onerror = (error) => {
          console.error('WebSocket error:', error);
          setError('WebSocket connection failed');
          setIsConnected(false);
        };
        
        socketRef.current = socket;
      } catch (e) {
        setError('Failed to create WebSocket connection');
        console.error('WebSocket connection error:', e);
      }
    };

    // Only attempt connection in production or when backend is available
    // For development, we'll skip WebSocket connection
    if (import.meta.env.PROD || import.meta.env.VITE_ENABLE_WS === 'true') {
      connectWebSocket();
    }

    return () => {
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [url, onMessage]);

  const sendMessage = (message: T) => {
    if (socketRef.current && isConnected) {
      socketRef.current.send(JSON.stringify(message));
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    error,
    sendMessage
  };
};
