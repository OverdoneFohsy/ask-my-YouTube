from typing import List, Dict, Optional

def chunk_transcript(
        segments: List[Dict],
        max_chars: int = 2000,
        overlap_chars: int = 300,
) -> List[Dict]:
    chunks = []
    current_text: List[str] = []
    current_len = 0

    current_start: Optional[float] = None
    current_end: Optional[float] = None

    for seg in segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        seg_start = seg.get("start", 0.0)
        seg_dur = seg.get("duration", 0.0)
        seg_end = seg_start + seg_dur

        if current_start is None:
            current_start = seg_start
        
        if current_len + len(text) + 1 > max_chars and current_text:
            chunk_text = " ".join(current_text).strip()

            chunks.append({
                "text": chunk_text,
                "start": current_start,
                "end": current_end
            })

            if overlap_chars > 0:
                overlap_text = chunk_text[-overlap_chars:]
                current_text = [overlap_text]
                current_len = len(overlap_text)
            else:
                current_text = []
                current_len = 0

            current_start = seg_start

        current_text.append(text)
        current_len += len(text) + 1
        current_end = seg_end

    if current_text:
        chunk_text = " ".join(current_text).strip()

        chunks.append({
            "text": chunk_text,
            "start": current_start,
            "end": current_end
        })
    
    return chunks