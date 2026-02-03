"use client";

import { Box, Container, Typography, Paper, ThemeProvider, createTheme, CssBaseline } from "@mui/material";
import { useAudioRecorder } from "@/hooks/useAudioRecorder";
import { Controls } from "@/components/Controls";
import { useMemo } from "react";

export default function Home() {
  const { isRecording, text, partialText, language, setLanguage, model, setModel, mode, setMode, startRecording, stopRecording, endSession, clearText } = useAudioRecorder();

  const theme = useMemo(() => createTheme({
    palette: {
      mode: 'light',
      primary: {
        main: '#1976d2',
      },
    },
  }), []);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', pb: 15 }}>
        <Container maxWidth="md" sx={{ mt: 4, flex: 1 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center" sx={{ mb: 4 }}>
            Real-time Transcription
          </Typography>

          <Paper elevation={3} sx={{ p: 4, minHeight: '60vh', borderRadius: 2 }}>
            {text || partialText ? (
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                {text}
                <Typography component="span" color="text.secondary" sx={{ fontStyle: 'italic', ml: text ? 1 : 0 }}>
                  {partialText}
                </Typography>
              </Typography>
            ) : (
              <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mt: 10, gap: 2 }}>
                <Typography variant="body1" color="text.secondary" align="center">
                  {isRecording ? "Listening..." : "Press Start to begin transcription..."}
                </Typography>
                {isRecording && (
                  <Typography variant="caption" color="primary" sx={{ animation: 'pulse 1.5s infinite' }}>
                    ● Recording
                  </Typography>
                )}
              </Box>
            )}
          </Paper>
        </Container>

        <Controls
          isRecording={isRecording}
          onStart={startRecording}
          onStop={stopRecording}
          onEnd={endSession}
          onClear={clearText}
          language={language}
          setLanguage={setLanguage}
          model={model}
          setModel={setModel}
          mode={mode}
          setMode={setMode}
        />

      </Box>
    </ThemeProvider>
  );
}
