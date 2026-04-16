import { useCallback, useEffect, useRef, useState } from "react";

const RECONNECT_DELAY_MS = 3000;

export interface UseWebSocketReturn {
  isConnected: boolean;
  sendJson: (data: object) => void;
  lastMessage: Record<string, unknown> | null;
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<Record<string, unknown> | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const unmountedRef = useRef(false);

  useEffect(() => {
    unmountedRef.current = false;

    function connect() {
      if (unmountedRef.current) return;

      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        if (!unmountedRef.current) setIsConnected(true);
      };

      ws.onclose = () => {
        if (!unmountedRef.current) {
          setIsConnected(false);
          wsRef.current = null;
          reconnectTimerRef.current = setTimeout(connect, RECONNECT_DELAY_MS);
        }
      };

      ws.onerror = () => {
        ws.close();
      };

      ws.onmessage = (event: MessageEvent) => {
        if (!unmountedRef.current) {
          try {
            const data = JSON.parse(event.data as string) as Record<string, unknown>;
            setLastMessage(data);
          } catch {
            // 不正な JSON は無視
          }
        }
      };
    }

    connect();

    return () => {
      unmountedRef.current = true;
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
      }
      wsRef.current?.close();
    };
  }, [url]);

  const sendJson = useCallback((data: object) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  return { isConnected, sendJson, lastMessage };
}
