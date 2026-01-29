import os
import requests
from typing import List, Optional
from models import Card


class GitHubProjectClient:
    def __init__(
        self, 
        token: str, 
        owner: str, 
        repo: str,
        project_id: str,
        status_field_id: str,
        area_field_id: str
    ):
        """
        Inicializa o cliente do GitHub Projects v2.
        
        Args:
            token: Token de autenticação do GitHub
            owner: Proprietário do repositório
            repo: Nome do repositório
            project_id: ID do GitHub Project (Projects v2)
            status_field_id: ID do campo de status no Project
            area_field_id: ID do campo de área no Project
        """
        self.token = token
        self.owner = owner
        self.repo = repo
        self.project_id = project_id
        self.status_field_id = status_field_id
        self.area_field_id = area_field_id
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def get_project_item_id(self, issue_number: str) -> Optional[str]:
        """
        Obtém o ID do item do Project associado a uma issue.
        
        Args:
            issue_number: Número da issue
            
        Returns:
            ID do item do Project ou None
        """
        query = """
        query($owner: String!, $repo: String!, $issueNumber: Int!) {
            repository(owner: $owner, name: $repo) {
                issue(number: $issueNumber) {
                    id
                    projectItems(first: 10) {
                        nodes {
                            id
                            project {
                                id
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "owner": self.owner,
            "repo": self.repo,
            "issueNumber": int(issue_number)
        }
        
        try:
            response = requests.post(
                self.graphql_url,
                json={"query": query, "variables": variables},
                headers=self.headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "errors" in data:
                print(f"Erro GraphQL ao buscar issue #{issue_number}: {data['errors']}")
                return None
            
            issue = data.get("data", {}).get("repository", {}).get("issue")
            if not issue:
                return None
            
            issue_id = issue.get("id")
            return issue_id
        
        except Exception as e:
            print(f"Erro ao buscar issue #{issue_number}: {e}")
            return None
    
    def add_issue_to_project(self, issue_number: str, card: Card) -> bool:
        """
        Adiciona uma issue ao Project e configura seus campos.
        
        Args:
            issue_number: Número da issue
            card: Card associado à issue
            
        Returns:
            True se bem-sucedido, False caso contrário
        """
        issue_id = self.get_project_item_id(issue_number)
        if not issue_id:
            print(f"Não foi possível obter ID da issue #{issue_number}")
            return False
        
        area_value = "Front-End" if card.type.value == "Front-End" else "Back-end"
        
        add_item_mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
            addProjectV2ItemById(input: {
                projectId: $projectId
                contentId: $contentId
            }) {
                item {
                    id
                }
            }
        }
        """
        
        try:
            add_variables = {
                "projectId": self.project_id,
                "contentId": issue_id
            }
            
            add_response = requests.post(
                self.graphql_url,
                json={"query": add_item_mutation, "variables": add_variables},
                headers=self.headers
            )
            add_response.raise_for_status()
            
            add_data = add_response.json()
            
            if "errors" in add_data:
                print(f"Erro GraphQL ao adicionar issue #{issue_number} ao Project: {add_data['errors']}")
                return False
            
            add_item_result = add_data.get("data", {}).get("addProjectV2ItemById", {})
            if not add_item_result:
                print(f"Erro: não foi possível adicionar issue #{issue_number} ao Project")
                return False
            
            item_id = add_item_result.get("item", {}).get("id")
            if not item_id:
                print(f"Erro: não foi possível obter ID do item do Project para issue #{issue_number}")
                return False
            
            update_field_mutation = """
            mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $value: String!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $projectId
                    itemId: $itemId
                    fieldId: $fieldId
                    value: {
                        text: $value
                    }
                }) {
                    projectV2Item {
                        id
                    }
                }
            }
            """
            
            status_variables = {
                "projectId": self.project_id,
                "itemId": item_id,
                "fieldId": self.status_field_id,
                "value": "Backlog Dev"
            }
            
            status_response = requests.post(
                self.graphql_url,
                json={"query": update_field_mutation, "variables": status_variables},
                headers=self.headers
            )
            status_response.raise_for_status()
            
            status_data = status_response.json()
            if "errors" in status_data:
                print(f"Aviso: erro ao atualizar status da issue #{issue_number}: {status_data['errors']}")
            
            area_variables = {
                "projectId": self.project_id,
                "itemId": item_id,
                "fieldId": self.area_field_id,
                "value": area_value
            }
            
            area_response = requests.post(
                self.graphql_url,
                json={"query": update_field_mutation, "variables": area_variables},
                headers=self.headers
            )
            area_response.raise_for_status()
            
            area_data = area_response.json()
            if "errors" in area_data:
                print(f"Aviso: erro ao atualizar área da issue #{issue_number}: {area_data['errors']}")
            
            print(f"Issue #{issue_number} adicionada ao Project com Status='Backlog Dev' e Area='{area_value}'")
            return True
        
        except Exception as e:
            print(f"Erro ao adicionar issue #{issue_number} ao Project: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    print(f"Detalhes do erro: {error_data}")
                except:
                    print(f"Resposta: {e.response.text}")
            return False
    
    def add_issues_to_project(self, issue_numbers: List[str], cards: List[Card]) -> int:
        """
        Adiciona múltiplas issues ao Project.
        
        Args:
            issue_numbers: Lista de números de issues
            cards: Lista de cards correspondentes
            
        Returns:
            Número de issues adicionadas com sucesso
        """
        print(f"\nAdicionando {len(issue_numbers)} issues ao GitHub Project...")
        
        if len(issue_numbers) != len(cards):
            print("Erro: número de issues não corresponde ao número de cards")
            return 0
        
        success_count = 0
        for issue_number, card in zip(issue_numbers, cards):
            if self.add_issue_to_project(issue_number, card):
                success_count += 1
        
        print(f"\nTotal de issues adicionadas ao Project: {success_count}/{len(issue_numbers)}")
        return success_count
