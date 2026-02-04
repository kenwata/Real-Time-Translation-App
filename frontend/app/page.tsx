"use client";

import { Box, Container, CssBaseline, Paper, Typography, Stack } from "@mui/material";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { Controls } from "@/components/Controls";
import { useEffect, useRef } from "react";
import { ModelSelector } from "@/components/ModelSelector";
import { LanguageSelector } from "@/components/LanguageSelector";
import { ModeSelector } from "@/components/ModeSelector";

export default function Home() {
  const {
    isRecording,
    text,
    partialText,
    model,
    setModel,
    language,
    setLanguage,
    mode,
    setMode,
    startRecording,
    pauseRecording,
    endSession,
    clearText
  } = useAudioRecorder();

  const scrollAnchorRef = useRef<HTMLDivElement>(null);

  // History segmentation logic
  // We match sentences ending in punctuation
  const matches = text.match(/[^.!?。]+[.!?。]+/g) || [];
  const joinedMatches = matches.join('');
  const historySegments = matches;

  // Calculate Active Segment (remainder)
  const activeSegment = text.slice(joinedMatches.length);

  // Combined active text: The tail of finalized text + current streaming partial
  const displayActiveText = (activeSegment + (partialText || "")).trim();

  // Auto-scroll to bottom of history
  useEffect(() => {
    if (scrollAnchorRef.current) {
      scrollAnchorRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [text, activeSegment]);

  // Logic for mode support
  const isStreamingSupported = model === 'zipformer' && language === 'en';

  return (
    <>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', pb: 15, bgcolor: '#f5f5f5' }}>
        <Container maxWidth="lg" sx={{ mt: 4, flex: 1, display: 'flex', flexDirection: 'column', gap: 2 }}>

          {/* Header Area with Title and Selectors */}
          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mb: 2 }}>
            <Typography variant="h4" component="h1" sx={{ fontWeight: 'bold', color: '#1976d2' }}>
              Real-time Transcription
            </Typography>

            {/* Top Right Selectors */}
            <Stack direction="row" spacing={2} alignItems="center">
              <Box sx={{ width: 180 }}>
                <ModelSelector
                  model={model}
                  onChange={setModel}
                  disabled={isRecording}
                />
              </Box>
              <Box sx={{ width: 150 }}>
                <LanguageSelector
                  language={language}
                  onChange={setLanguage}
                  disabled={isRecording}
                  model={model}
                />
              </Box>
              <Box sx={{ width: 180 }}>
                <ModeSelector
                  mode={mode}
                  onChange={setMode}
                  disabled={isRecording || !isStreamingSupported}
                />
              </Box>
            </Stack>
          </Stack>

          {/* History Section (Top) */}
          <Paper
            elevation={2}
            sx={{
              flex: 1, // Takes all remaining space
              p: 3,
              overflowY: 'auto', // Scrollable
              bgcolor: 'white',
              borderRadius: 2,
              border: '1px solid #e0e0e0'
            }}
          >
            {historySegments.length > 0 ? (
              <Box>
                {/* Trimmed Map to handle key uniqueness better if needed, but index is fine for simple list */}
                {historySegments.map((segment, index) => (
                  <Box
                    key={index}
                    sx={{
                      p: 2,
                      // White vs Gray-Blue
                      bgcolor: index % 2 === 0 ? 'white' : '#eef2f6',
                      // Accent Border (Lighter Blue)
                      borderLeft: index % 2 === 0 ? '4px solid transparent' : '4px solid #64b5f6',
                      borderBottom: '1px solid #e0e0e0',
                      '&:last-child': { borderBottom: 'none' },
                      transition: 'background-color 0.2s'
                    }}
                  >
                    <Typography variant="body1" sx={{ lineHeight: 1.6, color: 'text.primary' }}>
                      {segment.trim()}
                    </Typography>
                  </Box>
                ))}
                <div ref={scrollAnchorRef} />
              </Box>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', color: 'text.secondary' }}>
                <Typography>No transcription history yet.</Typography>
              </Box>
            )}
          </Paper>

          {/* Active Segment Section (Bottom) */}
          <Paper
            elevation={3}
            sx={{
              height: '240px', // Fixed height (~2x original)
              flexShrink: 0,   // Prevent shrinking
              p: 3,
              bgcolor: '#fff',
              borderTop: '4px solid #1976d2',
              borderRadius: 2,
              overflowY: 'auto' // Scrollable active text
            }}
          >
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              {isRecording ? "Live Transcription" : "Active Segment"}
            </Typography>

            {displayActiveText ? (
              <Typography variant="h6" component="div" sx={{ color: 'text.primary', fontWeight: 500 }}>
                {displayActiveText}
                {isRecording && (
                  <Typography component="span" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                    ...
                  </Typography>
                )}
              </Typography>
            ) : isRecording ? (
              <Typography component="div" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                (Listening...)
              </Typography>
            ) : (
              <Typography variant="body1" color="text.secondary">
                Press Start to begin...
              </Typography>
            )}
          </Paper>

        </Container>

        <Controls
          isRecording={isRecording}
          onStart={startRecording}
          onStop={pauseRecording}
          onEnd={endSession}
          onClear={clearText}
        />
      </Box>
    </>
  );
}
