from typing import Annotated
from pydantic import BaseModel

from pydantic import Field


class HairToneOutSchema(BaseModel):
    id: Annotated[int, Field(description="ID оттенка")]
    tone: Annotated[str, Field(description="Код или название оттенка")]
    photo_url: Annotated[str | None, Field(default=None, description="Ссылка на фото оттенка")]
