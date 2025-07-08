import { useEffect, useRef, useState } from 'react';

interface WebSocketHook<T = unknown> {
  socket: WebSocket | null;
  isConnected: boolean;
  error: string | null;
  sendMessage: (message: T) => void;
}

/**
 * Generisk WebSocket hook som kan användas för FastAPI endpoints
 * 
 * @param url WebSocket URL att ansluta till
 * @param onMessage Callback som anropas när ett meddelande tas emot
 * @param autoReconnect Om true, försöker automatiskt återansluta vid frånkoppling
 * @returns WebSocketHook objekt med socket, isConnected, error och sendMessage
 */
export const useWebSocket = <T = unknown>(
  url: string,
  onMessage?: (data: T) => void,
  autoReconnect: boolean = true
): WebSocketHook<T> => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        // Stäng befintlig anslutning om den finns
        if (socketRef.current) {
          socketRef.current.close();
        }
        
        console.log(`Connecting to WebSocket: ${url}`);
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
            // Försök hantera text-meddelanden om JSON-parsning misslyckas
            if (typeof event.data === 'string' && onMessage) {
              try {
                onMessage(event.data as unknown as T);
              } catch (textError) {
                console.error('Failed to handle text message:', textError);
              }
            }
          }
        };
        
        socket.onclose = (event) => {
          console.log(`WebSocket disconnected: ${event.code} ${event.reason}`);
          setIsConnected(false);
          
          // Attempt to reconnect after delay if autoReconnect is enabled
          if (autoReconnect) {
            if (reconnectTimeoutRef.current) {
              clearTimeout(reconnectTimeoutRef.current);
            }
            
            console.log('Attempting to reconnect in 3 seconds...');
            reconnectTimeoutRef.current = setTimeout(connectWebSocket, 3000);
          }
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
        
        // Attempt to reconnect after delay if autoReconnect is enabled
        if (autoReconnect) {
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }
          
          console.log('Attempting to reconnect in 5 seconds after error...');
          reconnectTimeoutRef.current = setTimeout(connectWebSocket, 5000);
        }
      }
    };

    // Only attempt connection in production or when backend is available
    if (import.meta.env.PROD || import.meta.env.VITE_ENABLE_WS === 'true') {
      connectWebSocket();
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (socketRef.current) {
        socketRef.current.close();
      }
    };
  }, [url, onMessage, autoReconnect]);

  const sendMessage = (message: T) => {
    if (socketRef.current && isConnected) {
      socketRef.current.send(JSON.stringify(message));
    } else {
      console.warn('Cannot send message: WebSocket is not connected');
    }
  };

  return {
    socket: socketRef.current,
    isConnected,
    error,
    sendMessage
  };
};
