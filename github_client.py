import os
import requests
from typing import List, Optional
from models import Card


class GitHubClient:
    def __init__(self, token: str, owner: str, repo: str):
        """
        Inicializa o cliente do GitHub.
        
        Args:
            token: Token de autenticação do GitHub
            owner: Proprietário do repositório
            repo: Nome do repositório
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
    
    def create_issue(self, card: Card, parent_issue_number: Optional[str] = None) -> Optional[str]:
        """
        Cria uma issue no GitHub a partir de um card.
        
        Args:
            card: Card a ser convertido em issue
            parent_issue_number: Número da issue pai (#), se houver (para incluir no body)
            
        Returns:
            ID da issue criada (número como string) ou None em caso de erro
        """
        acceptance_criteria_text = "\n".join([
            f"- [ ] {criterion}" for criterion in card.acceptance_criteria
        ])
        
        parent_line = ""
        if parent_issue_number:
            parent_line = f"\n**Issue pai:** #{parent_issue_number}\n"
        
        body = f"""## Descrição
{parent_line}
{card.description}

## Critérios de Aceitação

{acceptance_criteria_text}

---
*Gerado automaticamente a partir da especificação técnica*
"""
        
        issue_data = {
            "title": card.title,
            "body": body
        }
        
        url = f"{self.base_url}/repos/{self.owner}/{self.repo}/issues"
        
        try:
            response = requests.post(url, json=issue_data, headers=self.headers)
            response.raise_for_status()
            
            issue = response.json()
            issue_number = str(issue["number"])
            issue_url = issue["html_url"]
            
            print(f"Issue criada: #{issue_number} - {card.title} ({issue_url})")
            return issue_number
        
        except requests.exceptions.RequestException as e:
            print(f"Erro ao criar issue '{card.title}': {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Resposta: {e.response.text}")
            return None
    
    def create_issues_from_cards(
        self, 
        cards: List[Card]
    ) -> List[str]:
        """
        Cria múltiplas issues a partir de uma lista de cards.
        
        Args:
            cards: Lista de cards para converter em issues
            
        Returns:
            Lista de IDs das issues criadas
        """
        print(f"\nCriando {len(cards)} issues no GitHub...")
        
        issue_numbers = []
        for i, card in enumerate(cards):
            parent_num = None
            pi = getattr(card, "parent_index", None)
            if pi is not None and 0 <= pi < len(issue_numbers):
                parent_num = issue_numbers[pi]
            issue_number = self.create_issue(card, parent_issue_number=parent_num)
            if issue_number:
                issue_numbers.append(issue_number)
        
        print(f"\nTotal de issues criadas: {len(issue_numbers)}")
        return issue_numbers
