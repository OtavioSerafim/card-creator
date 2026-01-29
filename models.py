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

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "description": self.description,
            "type": self.type.value,
            "acceptance_criteria": self.acceptance_criteria
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Card":
        return cls(
            title=data["title"],
            description=data["description"],
            type=CardType(data["type"]),
            acceptance_criteria=data.get("acceptance_criteria", [])
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
