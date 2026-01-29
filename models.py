from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class CardType(str, Enum):
    FRONTEND = "Front-End"
    BACKEND = "Back-End"


@dataclass
class Card:
    title: str
    description: str
    type: CardType
    acceptance_criteria: List[str]
    parent_index: Optional[int] = None  # índice (0-based) do card pai na mesma lista; null = sem pai

    def to_dict(self) -> dict:
        d = {
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "acceptance_criteria": self.acceptance_criteria
        }
        if self.parent_index is not None:
            d["parent_index"] = self.parent_index
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        raw_parent = data.get("parent_index")
        parent_index = None
        if raw_parent is not None:
            try:
                parent_index = int(raw_parent)
            except (TypeError, ValueError):
                parent_index = None
        return cls(
            title=data["title"],
            description=data["description"],
            type=CardType(data["type"]),
            acceptance_criteria=data.get("acceptance_criteria", []),
            parent_index=parent_index
        )


@dataclass
class PDFContent:
    text: str
    tables_json: List[dict]

    def to_prompt(self) -> str:
        prompt = "=== TEXTO DO PDF ===\n\n"
        prompt += self.text
        prompt += "\n\n=== TABELAS DO PDF ===\n\n"
        prompt += str(self.tables_json)
        return prompt
