#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

from pdf_reader import read_pdf
from gemini_client import generate_cards
from github_client import GitHubClient
from project_client import GitHubProjectClient
from models import Card


def load_environment():
    """Carrega variáveis de ambiente do arquivo .env"""
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("Erro: arquivo .env não encontrado!")
        print("Crie um arquivo .env baseado no .env.example")
        sys.exit(1)
    
    load_dotenv(env_path)
    
    required_vars = [
        "GEMINI_API_KEY",
        "GITHUB_TOKEN",
        "GITHUB_OWNER",
        "GITHUB_REPO",
        "GITHUB_PROJECT_ID",
        "GITHUB_STATUS_FIELD_ID",
        "GITHUB_AREA_FIELD_ID"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"Erro: variáveis de ambiente faltando: {', '.join(missing_vars)}")
        sys.exit(1)
    
    return {
        "gemini_api_key": os.getenv("GEMINI_API_KEY"),
        "github_token": os.getenv("GITHUB_TOKEN"),
        "github_owner": os.getenv("GITHUB_OWNER"),
        "github_repo": os.getenv("GITHUB_REPO"),
        "github_project_id": os.getenv("GITHUB_PROJECT_ID"),
        "github_status_field_id": os.getenv("GITHUB_STATUS_FIELD_ID"),
        "github_area_field_id": os.getenv("GITHUB_AREA_FIELD_ID"),
        "frontend_label": os.getenv("FRONTEND_LABEL", "frontend"),
        "backend_label": os.getenv("BACKEND_LABEL", "backend"),
        "fullstack_label": os.getenv("FULLSTACK_LABEL", "fullstack")
    }


def main():
    if len(sys.argv) != 2:
        print("Uso: python main.py <caminho_do_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    
    if not os.path.exists(pdf_path):
        print(f"Erro: arquivo PDF não encontrado: {pdf_path}")
        sys.exit(1)
    
    print("=" * 60)
    print("Sistema de Automação: PDF → GitHub Projects")
    print("=" * 60)
    print()
    
    env = load_environment()
    
    try:
        print("ETAPA 1: Extraindo conteúdo do PDF...")
        pdf_content = read_pdf(pdf_path)
        
        if not pdf_content.text.strip() and not pdf_content.tables_json:
            print("Erro: nenhum conteúdo encontrado no PDF")
            sys.exit(1)
        
        print()
        print("ETAPA 2: Gerando cards com Gemini...")
        cards = generate_cards(pdf_content, env["gemini_api_key"])
        
        if not cards:
            print("Erro: nenhum card foi gerado")
            sys.exit(1)
        
        print()
        print("ETAPA 3: Criando issues no GitHub...")
        github_client = GitHubClient(
            token=env["github_token"],
            owner=env["github_owner"],
            repo=env["github_repo"]
        )
        
        issue_numbers = github_client.create_issues_from_cards(
            cards=cards,
            frontend_label=env["frontend_label"],
            backend_label=env["backend_label"]
        )
        
        if not issue_numbers:
            print("Erro: nenhuma issue foi criada")
            sys.exit(1)
        
        print()
        print("ETAPA 4: Adicionando issues ao GitHub Project...")
        project_client = GitHubProjectClient(
            token=env["github_token"],
            owner=env["github_owner"],
            repo=env["github_repo"],
            project_id=env["github_project_id"],
            status_field_id=env["github_status_field_id"],
            area_field_id=env["github_area_field_id"]
        )
        
        project_client.add_issues_to_project(issue_numbers, cards)
        
        print()
        print("=" * 60)
        print("Processo concluído com sucesso!")
        print("=" * 60)
        print(f"Total de cards processados: {len(cards)}")
        print(f"Total de issues criadas: {len(issue_numbers)}")
        
        frontend_count = sum(1 for c in cards if c.type.value == "Front-End")
        backend_count = sum(1 for c in cards if c.type.value == "Back-End")
        print(f"  - Front-End: {frontend_count}")
        print(f"  - Back-End: {backend_count}")
    
    except KeyboardInterrupt:
        print("\n\nProcesso interrompido pelo usuário")
        sys.exit(1)
    except Exception as e:
        print(f"\nErro durante a execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
