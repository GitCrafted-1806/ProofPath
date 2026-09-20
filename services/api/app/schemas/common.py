from typing import Any, Optional
from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str
    detail: Optional[Any] = None
