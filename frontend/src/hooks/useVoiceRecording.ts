/**
 * Task 6.2: 音声録音フック
 *
 * MediaRecorder API で録音し、停止時に Base64 エンコードした音声を
 * WebSocket の voice イベントとして送信する。
 */

import { useCallback, useRef, useState } from "react";

export interface UseVoiceRecordingReturn {
  isRecording: boolean;
  micAllowed: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
}

/** Blob を Base64 文字列に変換する */
function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => {
      const dataUrl = reader.result as string;
      const base64 = dataUrl.includes(",") ? dataUrl.split(",")[1] : dataUrl;
      resolve(base64 ?? "");
    };
    reader.onerror = () => reject(new Error("FileReader error"));
    reader.readAsDataURL(blob);
  });
}

/** 利用可能な MIME タイプを選択する */
function selectMimeType(): string {
  const candidates = ["audio/webm", "audio/ogg", "audio/mp4"];
  for (const type of candidates) {
    if (typeof MediaRecorder !== "undefined" && MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }
  return "audio/webm";
}

export function useVoiceRecording(
  sendJson: (data: object) => void,
): UseVoiceRecordingReturn {
  const [isRecording, setIsRecording] = useState(false);
  const [micAllowed, setMicAllowed] = useState(true);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);
  const sendJsonRef = useRef(sendJson);
  sendJsonRef.current = sendJson;

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const mimeType = selectMimeType();
      const mediaRecorder = new MediaRecorder(stream, { mimeType });
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const blob = new Blob(chunksRef.current, { type: mimeType });
        try {
          const base64 = await blobToBase64(blob);
          sendJsonRef.current({ type: "voice", data: base64 });
        } catch {
          // エンコード失敗時はスキップ
        } finally {
          streamRef.current?.getTracks().forEach((t) => t.stop());
          streamRef.current = null;
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch {
      setMicAllowed(false);
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current?.state === "recording") {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, []);

  return { isRecording, micAllowed, startRecording, stopRecording };
}
