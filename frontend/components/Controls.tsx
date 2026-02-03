import React from 'react';
import { Box, Button, Stack } from "@mui/material";
import { Mic, Stop, Clear, Logout } from "@mui/icons-material";
import { LanguageSelector } from "./LanguageSelector";
import { ModelSelector } from "./ModelSelector";
import { ModeSelector } from "./ModeSelector";

interface ControlsProps {
  isRecording: boolean;
  onStart: () => void;
  onStop: () => void;
  onEnd: () => void;
  onClear: () => void;
  language: string;
  setLanguage: (lang: string) => void;
  model: string;
  setModel: (model: string) => void;
  mode: string;
  setMode: (mode: string) => void;
}

export function Controls({
  isRecording,
  onStart,
  onStop,
  onEnd,
  onClear,
  language,
  setLanguage,
  model,
  setModel,
  mode,
  setMode
}: ControlsProps) {

  // Auto-switch mode if model changes to something that doesn't support streaming
  // Or disable the selector. simple approach: warn or disable.
  const isStreamingSupported = model === 'zipformer' && language === 'en';

  return (
    <Box sx={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      bgcolor: 'background.paper',
      boxShadow: 3,
      p: 2,
      zIndex: 1000
    }}>
      <Stack direction="row" spacing={2} justifyContent="center" alignItems="center">
        <Box sx={{ width: 200 }}>
          <ModelSelector
            model={model}
            onChange={setModel}
            disabled={isRecording}
          />
        </Box>
        <Box sx={{ width: 200 }}>
          <LanguageSelector
            language={language}
            onChange={setLanguage}
            disabled={isRecording}
            model={model}
          />
        </Box>
        <Box sx={{ width: 200 }}>
          <ModeSelector
            mode={mode}
            onChange={setMode}
            disabled={isRecording || !isStreamingSupported}
          />
        </Box>

        {!isRecording ? (
          <Button
            variant="contained"
            color="primary"
            size="large"
            startIcon={<Mic />}
            onClick={onStart}
            sx={{ minWidth: 150 }}
          >
            Start
          </Button>
        ) : (
          <Button
            variant="contained"
            color="error"
            size="large"
            startIcon={<Stop />}
            onClick={onStop}
            sx={{ minWidth: 150 }}
          >
            Stop
          </Button>
        )}

        <Button
          variant="outlined"
          color="warning"
          startIcon={<Clear />}
          onClick={onClear}
        >
          Clear
        </Button>

        <Button
          variant="outlined"
          color="secondary"
          startIcon={<Logout />}
          onClick={onEnd}
        >
          End Session
        </Button>
      </Stack>
    </Box>
  );
}
