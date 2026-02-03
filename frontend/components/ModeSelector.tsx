import React from 'react';
import { FormControl, InputLabel, Select, MenuItem, SelectChangeEvent } from '@mui/material';

interface ModeSelectorProps {
    mode: string;
    onChange: (mode: string) => void;
    disabled?: boolean;
}

export function ModeSelector({ mode, onChange, disabled }: ModeSelectorProps) {
    const handleChange = (event: SelectChangeEvent) => {
        onChange(event.target.value);
    };

    return (
        <FormControl fullWidth size="small">
            <InputLabel id="mode-select-label">Mode</InputLabel>
            <Select
                labelId="mode-select-label"
                value={mode}
                label="Mode"
                onChange={handleChange}
                disabled={disabled}
            >
                <MenuItem value="offline">Offline (Wait for silence)</MenuItem>
                <MenuItem value="streaming">Streaming (Real-time)</MenuItem>
            </Select>
        </FormControl>
    );
}
