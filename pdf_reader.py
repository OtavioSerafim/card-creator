import pdfplumber
import json
from typing import List, Dict
from models import PDFContent


def extract_tables_from_pdf(pdf_path: str) -> List[Dict]:
    """
    Extrai tabelas do PDF usando pdfplumber e converte para JSON.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        Lista de dicionários representando as tabelas
    """
    tables = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_tables = page.extract_tables()
                
                for table_num, table in enumerate(page_tables, start=1):
                    if not table or len(table) == 0:
                        continue
                    
                    table_dict = {
                        "page": page_num,
                        "table_number": table_num,
                        "headers": table[0] if table else [],
                        "rows": table[1:] if len(table) > 1 else [],
                        "row_count": len(table) - 1 if len(table) > 1 else 0
                    }
                    tables.append(table_dict)
    
    except Exception as e:
        print(f"Erro ao extrair tabelas: {e}")
        return []
    
    return tables


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extrai todo o texto do PDF.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        Texto completo do PDF
    """
    text_content = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_content.append(text)
    
    except Exception as e:
        print(f"Erro ao extrair texto: {e}")
        return ""
    
    return "\n\n".join(text_content)


def read_pdf(pdf_path: str) -> PDFContent:
    """
    Lê o PDF e extrai tanto texto quanto tabelas.
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        PDFContent com texto e tabelas em JSON
    """
    print(f"Lendo PDF: {pdf_path}")
    
    text = extract_text_from_pdf(pdf_path)
    tables = extract_tables_from_pdf(pdf_path)
    
    print(f"Texto extraído: {len(text)} caracteres")
    print(f"Tabelas encontradas: {len(tables)}")
    
    return PDFContent(text=text, tables_json=tables)
