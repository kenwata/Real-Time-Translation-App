import { FormControl, InputLabel, Select, MenuItem, SelectChangeEvent } from "@mui/material";

interface LanguageSelectorProps {
    language: string;
    onChange: (lang: string) => void;
    disabled?: boolean;
}

export function LanguageSelector({ language, onChange, disabled }: LanguageSelectorProps) {
    const handleChange = (event: SelectChangeEvent) => {
        onChange(event.target.value as string);
    };

    return (
        <FormControl fullWidth size="small" sx={{ minWidth: 120, mt: 1 }}>
            <InputLabel id="language-select-label">Language</InputLabel>
            <Select
                labelId="language-select-label"
                id="language-select"
                value={language}
                label="Language"
                onChange={handleChange}
                disabled={disabled}
            >
                <MenuItem value="en">English</MenuItem>
                <MenuItem value="ja">Japanese</MenuItem>
                <MenuItem value="ko">Korean</MenuItem>
                <MenuItem value="zh">Chinese</MenuItem>
                <MenuItem value="yue">Cantonese</MenuItem>
                <MenuItem value="auto">Auto Detect</MenuItem>
            </Select>
        </FormControl>
    );
}
