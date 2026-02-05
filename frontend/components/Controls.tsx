import React from 'react';
import { Box, Stack, Fab, Tooltip } from "@mui/material";
import { Mic, Stop, Pause, CleaningServices } from "@mui/icons-material";

interface ControlsProps {
  isRecording: boolean;
  isSessionActive: boolean; // Added
  onStart: () => void;
  onStop: () => void;
  onEnd: () => void;
  // onClear removed
}

export function Controls({
  isRecording,
  isSessionActive,
  onStart,
  onStop,
  onEnd,
}: ControlsProps) {

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
      <Stack direction="row" spacing={4} justifyContent="center" alignItems="center">

        {/* Clear Button (Broom) - DISABLED */}
        <Tooltip title="Clear Text (Disabled)">
          <span>
            <Fab
              disabled
              size="medium"
              sx={{ bgcolor: '#f5f5f5' }}
            >
              <CleaningServices color="action" />
            </Fab>
          </span>
        </Tooltip>

        {/* Start / Pause Toggle (Mic / Pause) */}
        <Tooltip title={isRecording ? "Pause" : "Start Transcribing"}>
          <Fab
            color={isRecording ? "warning" : "primary"}
            onClick={isRecording ? onStop : onStart}
            size="large"
            sx={{ width: 72, height: 72 }} // Slightly larger for emphasis
          >
            {isRecording ? <Pause sx={{ fontSize: 32 }} /> : <Mic sx={{ fontSize: 32 }} />}
          </Fab>
        </Tooltip>

        {/* Stop Button (Square/Stop) */}
        <Tooltip title={isSessionActive ? "Stop & Save" : "Start recording to enable stop"}>
          <span>
            <Fab
              color="error"
              onClick={onEnd}
              disabled={!isSessionActive}
              size="medium"
            >
              <Stop />
            </Fab>
          </span>
        </Tooltip>

      </Stack>
    </Box>
  );
}
