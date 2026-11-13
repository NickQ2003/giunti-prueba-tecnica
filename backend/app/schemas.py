from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, computed_field

ItemType = Literal[
    "escala_likert", "seleccion_multiple", "verdadero_falso", "desarrollo", "emparejamiento"
]
Value = StrictInt | str


class Alternative(BaseModel):
    model_config = ConfigDict(extra="ignore")

    valor: Value
    texto: str = Field(min_length=1)


class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")

    numero: int = Field(gt=0)
    enunciado: str = Field(min_length=1)
    tipo: ItemType
    alternativas: list[Alternative]
    respuesta_correcta: Value | None = None


class Questionnaire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    titulo: str = Field(min_length=1)
    idioma: str = Field(min_length=2, max_length=3)
    items: list[Item]

    @computed_field
    @property
    def total_items(self) -> int:
        return len(self.items)
