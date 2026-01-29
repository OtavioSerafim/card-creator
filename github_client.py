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
    
    def ensure_labels_exist(self, frontend_label: str, backend_label: str):
        """
        Garante que as labels necessárias existem no repositório.
        
        Args:
            frontend_label: Nome da label para Front-End
            backend_label: Nome da label para Back-End
        """
        labels_to_create = [
            {"name": frontend_label, "color": "0e8a16", "description": "Issues relacionadas ao front-end"},
            {"name": backend_label, "color": "d73a4a", "description": "Issues relacionadas ao back-end"}
        ]
        
        for label_data in labels_to_create:
            label_name = label_data["name"]
            url = f"{self.base_url}/repos/{self.owner}/{self.repo}/labels/{label_name}"
            
            try:
                response = requests.get(url, headers=self.headers)
                if response.status_code == 404:
                    create_url = f"{self.base_url}/repos/{self.owner}/{self.repo}/labels"
                    create_response = requests.post(create_url, json=label_data, headers=self.headers)
                    if create_response.status_code in [201, 200]:
                        print(f"Label '{label_name}' criada com sucesso")
                    else:
                        print(f"Erro ao criar label '{label_name}': {create_response.status_code}")
                elif response.status_code == 200:
                    print(f"Label '{label_name}' já existe")
            except Exception as e:
                print(f"Erro ao verificar/criar label '{label_name}': {e}")
    
    def create_issue(self, card: Card, frontend_label: str, backend_label: str) -> Optional[str]:
        """
        Cria uma issue no GitHub a partir de um card.
        
        Args:
            card: Card a ser convertido em issue
            frontend_label: Nome da label para Front-End
            backend_label: Nome da label para Back-End
            
        Returns:
            ID da issue criada (número como string) ou None em caso de erro
        """
        label = frontend_label if card.type.value == "Front-End" else backend_label
        
        acceptance_criteria_text = "\n".join([
            f"- [ ] {criterion}" for criterion in card.acceptance_criteria
        ])
        
        body = f"""## Descrição

{card.description}

## Critérios de Aceitação

{acceptance_criteria_text}

---
*Gerado automaticamente a partir da especificação técnica*
"""
        
        issue_data = {
            "title": card.title,
            "body": body,
            "labels": [label]
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
        cards: List[Card], 
        frontend_label: str, 
        backend_label: str
    ) -> List[str]:
        """
        Cria múltiplas issues a partir de uma lista de cards.
        
        Args:
            cards: Lista de cards para converter em issues
            frontend_label: Nome da label para Front-End
            backend_label: Nome da label para Back-End
            
        Returns:
            Lista de IDs das issues criadas
        """
        print(f"\nCriando {len(cards)} issues no GitHub...")
        
        self.ensure_labels_exist(frontend_label, backend_label)
        
        issue_numbers = []
        for card in cards:
            issue_number = self.create_issue(card, frontend_label, backend_label)
            if issue_number:
                issue_numbers.append(issue_number)
        
        print(f"\nTotal de issues criadas: {len(issue_numbers)}")
        return issue_numbers
