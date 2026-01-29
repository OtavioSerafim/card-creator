import os
import json
from typing import List
import google.generativeai as genai
from models import Card, PDFContent


def initialize_gemini(api_key: str):
    """
    Inicializa o cliente do Gemini com a API key.
    
    Args:
        api_key: Chave da API do Google Gemini
    """
    genai.configure(api_key=api_key)


def generate_cards(pdf_content: PDFContent, api_key: str) -> List[Card]:
    """
    Envia o conteúdo do PDF para o Gemini e gera cards estruturados.
    
    Args:
        pdf_content: Conteúdo extraído do PDF
        api_key: Chave da API do Google Gemini
        
    Returns:
        Lista de Cards gerados
    """
    initialize_gemini(api_key)
    
    model = genai.GenerativeModel('gemini-pro')
    
    prompt = f"""Você é um assistente especializado em análise de especificações técnicas de software.

Analise o seguinte conteúdo de um PDF de especificação técnica e gere cards de desenvolvimento estruturados.

{pdf_content.to_prompt()}

INSTRUÇÕES:
1. Analise o texto e tabelas fornecidos
2. Identifique requisitos funcionais e não funcionais
3. Para cada requisito, gere um card de desenvolvimento
4. Classifique cada card como "Front-End" ou "Back-End" seguindo estas regras:
   - UI, telas, formulários, UX, componentes visuais → Front-End
   - API, banco de dados, autenticação, regras de negócio, serviços → Back-End
5. Para cada card, defina critérios de aceitação claros

FORMATO DE RESPOSTA (JSON válido):
[
  {{
    "title": "Título do card",
    "description": "Descrição detalhada do requisito",
    "type": "Front-End" ou "Back-End",
    "acceptance_criteria": [
      "Critério 1",
      "Critério 2",
      "Critério 3"
    ]
  }}
]

IMPORTANTE:
- Retorne APENAS o JSON válido, sem markdown, sem código, sem explicações
- O JSON deve ser um array de objetos
- Cada objeto deve ter exatamente os campos: title, description, type, acceptance_criteria
- O campo type deve ser exatamente "Front-End" ou "Back-End"
- O campo acceptance_criteria deve ser um array de strings
"""
    
    try:
        print("Enviando conteúdo para o Gemini...")
        response = model.generate_content(prompt)
        
        response_text = response.text.strip()
        
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        response_text = response_text.strip()
        
        cards_data = json.loads(response_text)
        
        if not isinstance(cards_data, list):
            raise ValueError("Resposta do Gemini não é uma lista")
        
        cards = [Card.from_dict(card_data) for card_data in cards_data]
        
        print(f"Cards gerados: {len(cards)}")
        for i, card in enumerate(cards, 1):
            print(f"  {i}. [{card.type.value}] {card.title}")
        
        return cards
    
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON do Gemini: {e}")
        print(f"Resposta recebida: {response_text[:500]}")
        raise
    except Exception as e:
        print(f"Erro ao gerar cards com Gemini: {e}")
        raise
