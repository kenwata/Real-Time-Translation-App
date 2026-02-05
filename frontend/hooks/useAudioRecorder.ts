import { useState, useRef, useEffect, useCallback } from 'react';



export const useAudioRecorder = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [text, setText] = useState<string>("");
    const socketRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const isConnectedRef = useRef<boolean>(false);
    const [language, setLanguage] = useState<string>('en');
    const [partialText, setPartialText] = useState<string>("");
    const [isSessionActive, setIsSessionActive] = useState(false);

    const [segments, setSegments] = useState<string[]>([]);

    const sessionIdRef = useRef<string | null>(null); // Added sessionIdRef

    const pauseRecording = useCallback(() => {
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
        }
        if (sourceRef.current) { // Added sourceRef disconnection
            sourceRef.current.disconnect();
            sourceRef.current = null;
        }
        if (audioContextRef.current) {
            audioContextRef.current.close();
            audioContextRef.current = null;
        }
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setIsRecording(false);
    }, []);

    const connectWebSocket = useCallback(() => {
        if (socketRef.current?.readyState === WebSocket.OPEN) return;

        // Close existing if any
        if (socketRef.current) {
            socketRef.current.close();
        }

        const sid = sessionIdRef.current; // Get session ID
        const sessionIdParam = sid ? `&session_id=${sid}` : ""; // Add session ID parameter
        // Removed model_type parameter
        const wsUrl = `ws://localhost:8000/ws/transcribe?language=${language}${sessionIdParam}`;

        console.log(`Connecting to WebSocket: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket Connected');
            isConnectedRef.current = true;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.text) {
                    if (data.is_final === false) {
                        setPartialText(data.text);
                    } else {
                        // Final result
                        const newText = data.text.trim();
                        if (newText) {
                            setText(prev => prev + (prev ? " " : "") + newText);
                            setSegments(prev => [...prev, newText]);
                        }
                        setPartialText(""); // Clear partial since it's now finalized (or new segment started)
                    }
                }
            } catch (err) {
                console.error('Error parsing message:', err);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket Error:', error);
            // Try to log to backend
            fetch('/api/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ level: 'error', message: 'WebSocket Error', meta: { error } })
            }).catch(() => { });
        };

        ws.onclose = () => {
            console.log('WebSocket Disconnected');
            isConnectedRef.current = false;
            pauseRecording();
        };

        socketRef.current = ws;
    }, [language, pauseRecording]);

    const startRecording = useCallback(async () => {
        try {
            // Generate session ID if new
            if (!sessionIdRef.current) {
                sessionIdRef.current = Date.now().toString();
                console.log("Started new session:", sessionIdRef.current);
                // Clear history for new session
                setText("");
                setSegments([]);
                setPartialText("");
            }

            setIsSessionActive(true);

            if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
                connectWebSocket();
                // Wait a bit for connection
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            setIsRecording(true);
            // setPartialText(""); // Don't clear partials on un-pause, only on Clear

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            // Attempt to use native 16kHz context for better quality resampling
            let audioContext: AudioContext;
            try {
                audioContext = new AudioContext({ sampleRate: 16000 });
            } catch (e) {
                console.warn("Browser does not support sampleRate configuration, falling back to default");
                audioContext = new AudioContext();
            }
            audioContextRef.current = audioContext;
            console.log(`AudioContext Sample Rate: ${audioContext.sampleRate}`);

            const source = audioContext.createMediaStreamSource(stream);
            sourceRef.current = source; // Store source to disconnect later!

            // Use ScriptProcessor for raw audio access (simpler for this demo than AudioWorklet)
            // Buffer size 4096 = ~0.25s at 16kHz
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            processorRef.current = processor;

            processor.onaudioprocess = (e) => {
                if (!isConnectedRef.current || !socketRef.current) return;

                const inputData = e.inputBuffer.getChannelData(0);
                const targetRate = 16000;
                const currentRate = audioContext.sampleRate;

                if (socketRef.current.readyState === WebSocket.OPEN) {
                    if (currentRate === targetRate) {
                        // usage of .buffer on a TypedArray sends the underlying buffer which might be larger or shared.
                        // We should send the TypedArray itself (view) or a slice.
                        // sending the TypedArray view is supported by WebSocket and safer.
                        socketRef.current.send(inputData);
                    } else {
                        // Simple downsampling
                        const ratio = currentRate / targetRate;
                        const newLength = Math.floor(inputData.length / ratio);
                        const result = new Float32Array(newLength);
                        for (let i = 0; i < newLength; i++) {
                            result[i] = inputData[Math.floor(i * ratio)];
                        }
                        socketRef.current.send(result);
                    }
                }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

        } catch (err: unknown) {
            const errorMessage = err instanceof Error ? err.message : String(err);
            const errorStack = err instanceof Error ? err.stack : undefined;

            console.error("Error accessing microphone:", err);
            alert("Error accessing microphone: " + errorMessage);
            // Log to backend
            fetch('/api/log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    level: 'error',
                    message: 'Microphone Access Error',
                    meta: { error: errorMessage, stack: errorStack }
                })
            }).catch(() => { });
        }
    }, [connectWebSocket]);

    const endSession = useCallback(async () => { // Made async to await fetch
        pauseRecording();

        // Finalize text: Flush partials and ensure punctuation
        setText(prev => {
            const currentPartial = partialText;
            let combined = prev;
            if (currentPartial) {
                combined = (combined + " " + currentPartial).trim();
            }
            if (combined && !/[.!?。]$/.test(combined)) {
                combined += ".";
            }
            return combined;
        });

        // Also finalize segment for partial
        setSegments(prev => {
            if (partialText) {
                return [...prev, partialText];
            }
            return prev;
        });

        setPartialText("");

        const sid = sessionIdRef.current;
        if (sid) {
            console.log(`Ending session ${sid} and saving recording...`);
            try {
                const response = await fetch('/api/save_recording', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sid })
                });
                const result = await response.json();
                console.log("Recording saved:", result);
            } catch (e) {
                console.error("Failed to save recording:", e);
            }
            sessionIdRef.current = null; // Reset session ID
        }
        setIsSessionActive(false);

        if (socketRef.current) {
            console.log('Ending session (Closing WebSocket)');
            socketRef.current.close();
            socketRef.current = null;
        }
    }, [pauseRecording, partialText]);

    // clearText removed


    // Initialize WebSocket
    useEffect(() => {
        // connectWebSocket(); // Don't auto-connect on mount, wait for start
        return () => {
            socketRef.current?.close();
        };
    }, []); // Remove connectWebSocket from dependency to avoid loop

    return {
        isRecording,
        isSessionActive,
        text,
        segments, // New export
        partialText,
        language,
        setLanguage,
        startRecording,
        pauseRecording,
        endSession
    };
};

