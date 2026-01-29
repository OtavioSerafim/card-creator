import os
import json
import time
from typing import List, Optional, Tuple
import google.genai as genai
from google.genai.errors import ClientError
from models import Card, PDFContent


DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash-lite")


def list_available_models(client: genai.Client):
    """
    Lista os modelos disponíveis na API do Gemini.
    
    Args:
        client: Cliente do Gemini
    """
    try:
        print("\n" + "=" * 60)
        print("Buscando modelos disponíveis...")
        print("=" * 60)
        
        # Tenta diferentes formas de listar modelos
        models_list = []
        
        try:
            # Método 1: client.models.list()
            models_list = list(client.models.list())
        except AttributeError:
            try:
                # Método 2: client.list_models()
                models_list = list(client.list_models())
            except AttributeError:
                try:
                    # Método 3: genai.list_models()
                    models_list = list(genai.list_models())
                except:
                    pass
        
        if models_list:
            print(f"\nModelos disponíveis ({len(models_list)} encontrados):\n")
            for model in models_list:
                name = getattr(model, 'name', None) or getattr(model, 'display_name', 'N/A')
                display_name = getattr(model, 'display_name', None) or name
                supported_methods = getattr(model, 'supported_generation_methods', None) or getattr(model, 'supported_methods', [])
                
                print(f"  Nome: {name}")
                if display_name != name:
                    print(f"  Display Name: {display_name}")
                if supported_methods:
                    print(f"  Métodos suportados: {', '.join(supported_methods)}")
                print()
        else:
            print("\nNão foi possível listar modelos automaticamente.")
            print("Modelos comuns para tentar:")
            print("  - gemini-1.5-pro")
            print("  - gemini-1.5-flash")
            print("  - gemini-pro")
            print("  - gemini-1.0-pro")
            print("\nConsulte a documentação: https://ai.google.dev/gemini-api/docs/models")
        
        print("=" * 60)
    except Exception as e:
        print(f"\nErro ao listar modelos: {e}")
        print("\nModelos comuns para tentar:")
        print("  - gemini-1.5-pro")
        print("  - gemini-1.5-flash")
        print("  - gemini-pro")
        print("  - gemini-1.0-pro")
        print("\nConsulte a documentação: https://ai.google.dev/gemini-api/docs/models\n")


def generate_cards(
    pdf_content: PDFContent,
    api_key: str,
    existing_issues: Optional[List[Tuple[str, str]]] = None
) -> List[Card]:
    """
    Envia o conteúdo do PDF para o Gemini e gera cards estruturados.
    
    Args:
        pdf_content: Conteúdo extraído do PDF
        api_key: Chave da API do Google Gemini
        existing_issues: Lista de (título, descrição) das issues já no Project, para o modelo não gerar duplicatas
        
    Returns:
        Lista de Cards gerados
    """
    client = genai.Client(api_key=api_key)
    model_to_use = DEFAULT_GEMINI_MODEL
    
    existing_block = ""
    if existing_issues:
        lines = []
        for i, (title, body) in enumerate(existing_issues, 1):
            desc_snippet = (body or "").strip()[:280].replace("\n", " ")
            if desc_snippet:
                lines.append(f"{i}. Título: {title}\n   Descrição (resumo): {desc_snippet}...")
            else:
                lines.append(f"{i}. Título: {title}")
        existing_block = """
CARTÕES JÁ EXISTENTES NO PROJETO (não gere cards duplicados ou equivalentes a estes):
""" + "\n".join(lines) + """

- Verificação de duplicação RIGOROSA: compare cada requisito do documento com a lista acima. Se um requisito do PDF já está coberto (mesmo tema, mesmo escopo, mesma funcionalidade) por alguma issue existente, NÃO crie card para ele.
- NÃO crie cards que sejam "mais internos", sub-itens, detalhes de implementação ou desdobramentos de requisitos JÁ COBERTOS pelas issues existentes. Se um card existente já cobre um fluxo/problema inteiro, NÃO crie novos cards que sejam apenas partes, etapas ou sub-tarefas desse mesmo fluxo — eles não serão utilizados.
- Um card novo só é válido se representar um requisito TOTALMENTE NOVO (outro fluxo/feature), não uma subdivisão de algo que já está na lista.
- Se NENHUM requisito do documento for realmente novo em relação à lista, retorne um array vazio: []
- NÃO tente "achar" issues ao redor do que já existe nem inventar fluxos que não estão documentados no PDF. Se não houver nada novo a criar, retorne [].
- Gere APENAS cards para requisitos que sejam CLARAMENTE NOVOS e EXPLICITAMENTE documentados no PDF. Em dúvida (requisito pode ser parte de um card existente), NÃO crie o card — retorne [].
"""
    else:
        existing_block = ""
    
    prompt = f"""Você é um assistente especializado em análise de especificações técnicas de software.

Analise o seguinte conteúdo de um PDF de especificação técnica e gere cards de desenvolvimento estruturados.

{pdf_content.to_prompt()}
{existing_block}
DOCUMENTO A RISCA:
- O documento deve ser seguido À RISCA. Gere cards SOMENTE para o que está EXPLICITAMENTE descrito no PDF (texto e tabelas).
- NÃO extrapole, NÃO invente requisitos, NÃO inclua fluxos ou funcionalidades que não estejam documentados no conteúdo fornecido.
- Cada card deve corresponder a um requisito que aparece de forma clara no documento.

CONTEXTO OBRIGATÓRIO:
- O projeto Node.js já existe; não assuma criação do zero.
- Gere SOMENTE alterações funcionais, incrementais ou adições reais de comportamento.
- NÃO crie cards para: setup de ambiente, virtualenv, configurações iniciais, criação de módulos do zero, reescrever pipeline, ou tarefas genéricas que não alteram comportamento.
- NÃO inclua: "Configurar projeto", "Setup inicial", "Criar estrutura base", "Configurar dependências", "Configurar ambiente", "Criar repositório", ou equivalentes.
- Foque em: correções de comportamento, novas funcionalidades descritas na especificação, alterações incrementais em fluxos existentes.

SEÇÃO PROIBIDA (IGNORAR SEMPRE):
- Todo documento terá uma seção "4. Próximos Fluxos a Serem Planejados" (ou equivalente, ex.: "Próximos fluxos", "Fluxos a planejar").
- ESSA SEÇÃO JAMAIS DEVE SER LEVADA EM CONSIDERAÇÃO na criação dos cards.
- NÃO gere cards a partir do conteúdo dessa seção; ela pode estar presente em outros documentos e geraria duplicatas ou escopo incorreto.

INSTRUÇÕES:
1. Analise o texto e tabelas fornecidos EXCLUINDO qualquer seção "4. Próximos Fluxos a Serem Planejados" (e equivalentes).
2. Identifique APENAS requisitos que representem mudança funcional real (novas features, correções de regra de negócio, telas/APIs novas ou alteradas).
3. Para cada um desses requisitos, gere um card de desenvolvimento.
4. Classifique cada card como "Front-End" ou "Back-End" seguindo estas regras:
   - UI, telas, formulários, UX, componentes visuais → Front-End
   - API, banco de dados, autenticação, regras de negócio, serviços → Back-End
5. Para cada card, defina critérios de aceitação claros.
6. DESCRIÇÕES TÉCNICAS: em "description" e nos critérios de aceitação, seja técnico: mencione endpoints, componentes, camadas, regras de negócio, payloads, validações, fluxos de dados ou telas concretas quando aplicável (evite descrições genéricas).
7. HIERARQUIA (trace / parent): quando um requisito depender de outro ou for sub-item de outro na mesma lista, use "parent_index": índice (0-based) do card PAI nesta mesma lista. O card pai DEVE aparecer ANTES do filho no array. Use null quando não houver pai. Ex.: primeiro card é "Implementar módulo X", segundo é "Endpoint GET /x" com parent_index: 0.

FORMATO DE RESPOSTA (JSON válido):
[
  {{
    "title": "Título do card",
    "description": "Descrição TÉCNICA do requisito (endpoints, componentes, regras, payloads, validações, etc.)",
    "type": "Front-End" ou "Back-End",
    "acceptance_criteria": [
      "Critério técnico 1",
      "Critério técnico 2",
      "Critério técnico 3"
    ],
    "parent_index": null ou número (índice 0-based do card pai nesta lista; o pai deve vir antes do filho)
  }}
]

IMPORTANTE:
- Retorne APENAS o JSON válido, sem markdown, sem código, sem explicações
- O JSON deve ser um array de objetos (ou array vazio [] se não houver nada novo)
- Se NENHUM requisito do documento for realmente novo em relação às issues existentes, retorne [] — não invente "issues ao redor" nem fluxos não documentados
- NÃO crie cards que sejam sub-itens ou "mais internos" de requisitos já cobertos pelos cards existentes (ex.: se já existe "Implementar fluxo X", NÃO crie "Validar campo Y do fluxo X" ou "Endpoint Z do fluxo X" — o problema inteiro já está coberto)
- Cada objeto deve ter: title, description, type, acceptance_criteria e opcionalmente parent_index
- O campo type deve ser exatamente "Front-End" ou "Back-End"
- O campo acceptance_criteria deve ser um array de strings
- parent_index: use apenas quando o card tiver um "pai" na mesma lista (índice 0-based); o card pai deve aparecer antes no array
- description e acceptance_criteria devem ser técnicos (não genéricos)
"""
    
    max_retries = 3
    retry_delay = 5
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                wait_time = retry_delay * (2 ** (attempt - 1))
                print(f"Aguardando {wait_time} segundos antes de tentar novamente (tentativa {attempt + 1}/{max_retries})...")
                time.sleep(wait_time)
            
            print(f"Enviando conteúdo para o Gemini (modelo: {model_to_use})...")
            response = client.models.generate_content(
                model=model_to_use,
                contents=prompt
            )
            
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
        
        except ClientError as e:
            error_code = getattr(e, 'status_code', None)
            error_message = str(e)
            
            if error_code == 429 or 'RESOURCE_EXHAUSTED' in error_message:
                if attempt < max_retries - 1:
                    print(f"\nErro 429 (Rate Limit): Limite de requisições atingido.")
                    print(f"Tentando novamente em {retry_delay * (2 ** attempt)} segundos...")
                    continue
                else:
                    print(f"\nErro 429 (Rate Limit): Limite de requisições atingido após {max_retries} tentativas.")
                    print("\nSoluções possíveis:")
                    print("  1. Aguarde alguns minutos e tente novamente")
                    print("  2. Verifique seus limites de quota na API do Gemini")
                    print("  3. Considere usar um modelo diferente ou reduzir o tamanho do conteúdo")
                    print("  4. Se estiver na conta gratuita, considere fazer upgrade")
                    raise
            
            print(f"\nErro ao gerar cards com Gemini: {e}")
            
            if error_code == 404 or 'not found' in error_message.lower():
                print("\nModelo não encontrado. Listando modelos disponíveis...")
                list_available_models(client)
                print("\nDica: você pode setar `GEMINI_MODEL` no .env (ex: GEMINI_MODEL=models/gemini-2.0-flash-lite).")
            
            raise
        
        except Exception as e:
            error_str = str(e)
            
            if '429' in error_str or 'RESOURCE_EXHAUSTED' in error_str:
                if attempt < max_retries - 1:
                    print(f"\nErro 429 detectado. Tentando novamente em {retry_delay * (2 ** attempt)} segundos...")
                    continue
                else:
                    print(f"\nErro 429 após {max_retries} tentativas.")
                    print("\nSoluções possíveis:")
                    print("  1. Aguarde alguns minutos e tente novamente")
                    print("  2. Verifique seus limites de quota na API do Gemini")
                    print("  3. Considere usar um modelo diferente ou reduzir o tamanho do conteúdo")
                    raise
            
            print(f"Erro ao gerar cards com Gemini: {e}")
            
            if '404' in error_str or 'not found' in error_str.lower():
                print("\nErro 404 detectado. Listando modelos disponíveis...")
                list_available_models(client)
                print("\nDica: você pode setar `GEMINI_MODEL` no .env (ex: GEMINI_MODEL=models/gemini-2.0-flash-lite).")
            
            raise
    
    raise Exception("Falha após todas as tentativas")
