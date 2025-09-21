from __future__ import annotations
from typing import List, Optional

# MVP: keyword-only stub; upgrade to OpenAI Vision later.
# Keep the function async to make the swap trivial.

async def extract_tags(image_url: Optional[str]) -> List[str]:
    if not image_url:
        return []
    # TODO: call your OpenAI vision client and return labels.
    # For now, return empty list (routing relies on text/category).
    return []
