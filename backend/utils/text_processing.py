import re

def beautify_text(text: str) -> str:
    """
    Real-time text beautification for streaming transcripts.
    Converts uppercase output to sentence case and fixes 'I' capitalization.
    Includes Chinese-to-English punctuation normalization.
    """
    if not text:
        return ""
    
    # 1. Lowercase first (essential for Punctuation models trained on lower/mixed case)
    # Note: If text comes in as ALL CAPS, we lower it.
    # But this function might be called AFTER punctuation, so we assume input 
    # might already be punctuated but still potentially messy casing.
    
    # Actually, the plan says we lowercase BEFORE punctuation in HybridService.
    # So this function receives "punctuated text" which might be "hello world." or "Hello World."
    # If the punctuation model restored casing, great. If not, we fix it.
    
    # However, to be safe and consistent with the user's request:
    # "beautify_text" should handle the final polish.
    
    # Normalize punctuation first (Chinese -> English)
    text = text.replace("。", ".").replace("，", ",").replace("？", "?").replace("！", "!")
    text = text.replace("：", ":").replace("；", ";").replace("“", '"').replace("”", '"')

    # Fix spacing after periods (e.g., "word.word" -> "word. word")
    # Using regex to target periods followed immediately by a letter
    text = re.sub(r'\.(?=[a-zA-Z])', '. ', text)

    # 2. Capitalize sentences
    # Regex to find sentence boundaries and capitalize the next letter
    def capitalize_match(match):
        return match.group().upper()
    
    # Match Start of string or Punctuation+Space followed by a letter
    p = re.compile(r'(^|[.?!]\s+)([a-z])')
    text = p.sub(capitalize_match, text)
    
    # 3. Capitalize "I"
    # Standalone "i"
    p_i = re.compile(r'(?<!\w)i(?!\w)')
    text = p_i.sub("I", text)
    
    # "i'm", "i'll", "i've", "i'd"
    p_im = re.compile(r'(?<!\w)i(?=\'[a-z])')
    text = p_im.sub("I", text)

    return text
