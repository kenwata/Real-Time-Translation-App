import { useState, useRef, useEffect, useCallback } from 'react';



export const useAudioRecorder = () => {
    const [isRecording, setIsRecording] = useState(false);
    const [text, setText] = useState<string>("");
    const socketRef = useRef<WebSocket | null>(null);
    const audioContextRef = useRef<AudioContext | null>(null);
    const processorRef = useRef<ScriptProcessorNode | null>(null);
    const streamRef = useRef<MediaStream | null>(null);
    const isConnectedRef = useRef<boolean>(false);
    const [language, setLanguage] = useState<string>('en');
    const [model, setModel] = useState<string>('sensevoice');
    const [mode, setMode] = useState<string>('offline');
    const [partialText, setPartialText] = useState<string>("");

    const setModelWithValidation = useCallback((newModel: string) => {
        setModel(newModel);
        if (newModel === 'zipformer') {
            const validLanguages = ['en', 'zh'];
            if (!validLanguages.includes(language)) {
                setLanguage('en');
            }
        }
    }, [language]);

    const stopRecording = useCallback(() => {
        if (processorRef.current) {
            processorRef.current.disconnect();
            processorRef.current = null;
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

        // Close existing if any (though usually handled by cleanup)
        if (socketRef.current) {
            socketRef.current.close();
        }

        const wsUrl = `ws://localhost:8000/ws/transcribe?language=${language}&model_type=${model}&mode=${mode}`;
        console.log(`Connecting to WebSocket: ${wsUrl}`);
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            console.log('WebSocket Connected');
            isConnectedRef.current = true;
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                // Backend now sends {"text": "...", "is_final": boolean}
                // Fallback for old backend: if no is_final, assume true? No, old backend didn't send is_final.

                if (data.text) {
                    if (data.is_final === false) {
                        setPartialText(data.text);
                    } else {
                        // Final result
                        setText(prev => prev + (prev ? " " : "") + data.text);
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
            stopRecording();
        };

        socketRef.current = ws;
    }, [language, model, mode, stopRecording]); // Recreate if mode changes

    const startRecording = useCallback(async () => {
        try {
            if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
                connectWebSocket();
                // Wait a bit for connection
                await new Promise(resolve => setTimeout(resolve, 500));
            }

            setIsRecording(true);
            setPartialText(""); // Clear previous partials

            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            streamRef.current = stream;

            const audioContext = new AudioContext(); // Use default sample rate (usually 44100 or 48000)
            audioContextRef.current = audioContext;

            const source = audioContext.createMediaStreamSource(stream);

            // Use ScriptProcessor for raw audio access (simpler for this demo than AudioWorklet)
            // Buffer size 4096 = ~0.25s at 16kHz
            const processor = audioContext.createScriptProcessor(4096, 1, 1);
            processorRef.current = processor;

            processor.onaudioprocess = (e) => {
                if (!isConnectedRef.current || !socketRef.current) return;

                const inputData = e.inputBuffer.getChannelData(0);
                // Downsample to 16000Hz if needed
                const targetRate = 16000;
                const currentRate = audioContext.sampleRate;

                if (socketRef.current.readyState === WebSocket.OPEN) {
                    if (currentRate === targetRate) {
                        socketRef.current.send(inputData.buffer);
                    } else {
                        // Simple downsampling
                        const ratio = currentRate / targetRate;
                        const newLength = Math.floor(inputData.length / ratio);
                        const result = new Float32Array(newLength);
                        for (let i = 0; i < newLength; i++) {
                            result[i] = inputData[Math.floor(i * ratio)];
                        }
                        socketRef.current.send(result.buffer);
                    }
                }
            };

            source.connect(processor);
            processor.connect(audioContext.destination);

            setIsRecording(true);
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
    }, [connectWebSocket]); // Recreate if connectWebSocket changes



    const endSession = useCallback(() => {
        stopRecording();
        // Maybe close socket if strictly ending? 
        // keeping it open for now in case user restarts immediately
    }, [stopRecording]);

    const clearText = useCallback(() => {
        // Close socket to reset backend state (force new stream on next start)
        if (socketRef.current) {
            socketRef.current.close();
        }
        setText("");
        setPartialText("");
    }, []);

    // Initialize WebSocket
    useEffect(() => {
        connectWebSocket();
        return () => {
            socketRef.current?.close();
        };
    }, [connectWebSocket]);

    return {
        isRecording,
        text,
        partialText,
        language,
        setLanguage,
        model,
        setModel: setModelWithValidation,
        mode,
        setMode,
        startRecording,
        stopRecording,
        endSession,
        clearText
    };
};

