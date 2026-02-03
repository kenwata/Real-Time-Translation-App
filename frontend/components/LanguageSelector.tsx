import { FormControl, InputLabel, Select, MenuItem, SelectChangeEvent } from "@mui/material";

interface LanguageSelectorProps {
    language: string;
    onChange: (lang: string) => void;
    disabled?: boolean;
    model?: string;
}

export function LanguageSelector({ language, onChange, disabled, model }: LanguageSelectorProps) {
    const handleChange = (event: SelectChangeEvent) => {
        onChange(event.target.value as string);
    };

    const isZipformer = model === 'zipformer';

    return (
        <FormControl fullWidth size="small" sx={{ minWidth: 120 }}>
            <InputLabel id="language-select-label">Language</InputLabel>
            <Select
                labelId="language-select-label"
                id="language-select"
                value={language}
                label="Language"
                onChange={handleChange}
                disabled={disabled}
            >
                <MenuItem value="en">English (default)</MenuItem>

                {!isZipformer && <MenuItem value="ja">Japanese</MenuItem>}
                {!isZipformer && <MenuItem value="ko">Korean</MenuItem>}

                <MenuItem value="zh">Chinese</MenuItem>

                {!isZipformer && <MenuItem value="yue">Cantonese</MenuItem>}
                {!isZipformer && <MenuItem value="auto">Auto Detect</MenuItem>}
            </Select>
        </FormControl>
    );
}
