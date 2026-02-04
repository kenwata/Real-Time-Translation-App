import React from 'react';
import { FormControl, Select, MenuItem, SelectChangeEvent, InputLabel } from '@mui/material';

interface ModelSelectorProps {
    model: string;
    onChange: (model: string) => void;
    disabled?: boolean;
}

export const ModelSelector: React.FC<ModelSelectorProps> = ({
    model,
    onChange,
    disabled = false
}) => {
    const handleChange = (event: SelectChangeEvent) => {
        onChange(event.target.value as string);
    };

    return (
        <FormControl fullWidth size="small">
            <InputLabel id="model-select-label">Model</InputLabel>
            <Select
                labelId="model-select-label"
                value={model}
                label="Model"
                onChange={handleChange}
                disabled={disabled}
            >
                <MenuItem value="sensevoice">SenseVoice</MenuItem>
                <MenuItem value="zipformer">Zipformer</MenuItem>
            </Select>
        </FormControl>
    );
};
