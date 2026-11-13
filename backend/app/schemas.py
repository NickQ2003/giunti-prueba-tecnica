import re
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StringConstraints,
    computed_field,
    model_validator,
)
from pydantic_core import PydanticCustomError

ItemType = Literal[
    "escala_likert", "seleccion_multiple", "verdadero_falso", "desarrollo", "emparejamiento"
]
Value = StrictInt | str
NonBlankText = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10_000)
]


class Alternative(BaseModel):
    model_config = ConfigDict(extra="ignore")

    valor: Value
    texto: NonBlankText

    @model_validator(mode="after")
    def check_value(self):
        if isinstance(self.valor, str) and not self.valor.strip():
            raise ValueError("alternative value cannot be blank")
        return self


class Item(BaseModel):
    model_config = ConfigDict(extra="ignore")

    numero: StrictInt = Field(gt=0)
    enunciado: NonBlankText
    tipo: ItemType
    alternativas: list[Alternative] = Field(max_length=100)
    respuesta_correcta: Value | None = None

    @model_validator(mode="after")
    def check_alternatives(self):
        values = [
            (type(a.valor), a.valor.strip().casefold() if isinstance(a.valor, str) else a.valor)
            for a in self.alternativas
        ]
        if len(set(values)) != len(values):
            raise ValueError("duplicate alternative values")
        if self.tipo == "desarrollo" and self.alternativas:
            raise ValueError("open-ended items cannot have alternatives")
        if (
            self.tipo in ("seleccion_multiple", "verdadero_falso")
            and self.respuesta_correcta is not None
        ):
            answer = self.respuesta_correcta
            exact = [
                a.valor
                for a in self.alternativas
                if type(a.valor) is type(answer) and a.valor == answer
            ]
            if len(exact) == 1:
                return self
            if isinstance(answer, str):
                matches = [
                    a.valor
                    for a in self.alternativas
                    if isinstance(a.valor, str) and _answer_key(a.valor) == _answer_key(answer)
                ]
                if len(matches) == 1:
                    self.respuesta_correcta = matches[0]
                    return self
            raise PydanticCustomError(
                "inconsistent_answer", "answer does not uniquely match an alternative"
            )
        return self


def _answer_key(value: str) -> str:
    value = value.strip().casefold()
    # Punctuation is only removed for single-letter option labels, not arbitrary text.
    return value[:-1] if re.fullmatch(r"[a-z][.)]", value) else value


class Questionnaire(BaseModel):
    model_config = ConfigDict(extra="ignore")

    titulo: NonBlankText
    idioma: Literal["es", "it", "en", "und"]
    items: list[Item] = Field(max_length=1000)

    @model_validator(mode="after")
    def check_numbers(self):
        numbers = [item.numero for item in self.items]
        if len(set(numbers)) != len(numbers):
            raise ValueError("duplicate item numbers")
        return self

    @computed_field
    @property
    def total_items(self) -> int:
        return len(self.items)
