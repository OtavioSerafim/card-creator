# Card Creator

Automação em Python que transforma documentos PDF de especificação técnica em **issues** no GitHub e as adiciona a um **GitHub Project (v2)** com Status e Área configurados automaticamente.

## O que faz

1. **Extrai** texto e tabelas do PDF (via `pdfplumber`)
2. **Envia** o conteúdo para a API do **Google Gemini**
3. **Gera** cards de desenvolvimento estruturados (título, descrição, critérios de aceitação)
4. **Classifica** cada card como **Front-End** ou **Back-End**
5. **Cria** issues no repositório GitHub (sem labels; setor fica só no Project)
6. **Adiciona** cada issue ao GitHub Project v2 com:
   - **Status** → Backlog (via option ID)
   - **Área** → Front-End ou Back-End (via option IDs)

## Requisitos

- **Python 3.11+**
- Conta no [Google AI Studio](https://aistudio.google.com/apikey) (API key do Gemini)
- Token do GitHub com permissão para criar issues e gerenciar Projects
- Um **GitHub Project (v2)** com campos **Status** (single select) e **Área** (single select)

## Instalação

```bash
# Clone o repositório
git clone https://github.com/OtavioSerafim/card-creator.git
cd card-creator

# Crie e ative o ambiente virtual
python3 -m venv venv
source venv/bin/activate   # Linux/macOS
# ou: venv\Scripts\activate   # Windows

# Instale as dependências
pip install -r requirements.txt
```

## Configuração

1. Copie o arquivo de exemplo e preencha com suas credenciais e IDs:

```bash
cp .env.example .env
```

2. Edite o `.env` com:

| Variável | Descrição |
|----------|-----------|
| `GEMINI_API_KEY` | Chave da API do Google Gemini ([obter aqui](https://aistudio.google.com/apikey)) |
| `GITHUB_TOKEN` | Token do GitHub com escopo `repo` e `project` |
| `GITHUB_OWNER` | Proprietário do repositório (ex: `OtavioSerafim`) |
| `GITHUB_REPO` | Nome do repositório (ex: `card-creator`) |
| `GITHUB_PROJECT_ID` | ID do GitHub Project (v2) |
| `GITHUB_STATUS_FIELD_ID` | ID do campo **Status** no Project |
| `STATUS_BACKLOG_OPTION_ID` | ID da opção **Backlog** no campo Status |
| `GITHUB_AREA_FIELD_ID` | ID do campo **Área** no Project |
| `AREA_FRONTEND_OPTION_ID` | ID da opção **Front-End** no campo Área |
| `AREA_BACKEND_OPTION_ID` | ID da opção **Back-End** no campo Área |

3. **(Opcional)** Para usar outro modelo do Gemini:

```env
GEMINI_MODEL=models/gemini-2.0-flash-lite
```

### Como obter os IDs do GitHub Project (v2)

- Use a **API GraphQL** do GitHub ([documentação](https://docs.github.com/en/graphql)) ou
- Abra o Project no navegador, abra **DevTools → Network**, filtre por **graphql** e inspecione as requisições ao interagir com o Project (adicionar item, mudar status, etc.) para ver os IDs nos payloads.

## Uso

```bash
python main.py "caminho/para/seu/documento.pdf"
```

**Exemplo:**

```bash
python main.py "Planejamento de Estrutura de Software_ Emissão de Boleto de Cobrança.pdf"
```

### Saída esperada

- Logs das etapas: extração do PDF, geração de cards, criação de issues, vinculação ao Project
- Resumo ao final: total de cards, issues criadas e quantidade por Front-End e Back-End

### Erros comuns

- **404 (modelo não encontrado)**  
  O script lista os modelos disponíveis na sua conta. Ajuste `GEMINI_MODEL` no `.env` se necessário (ex: `models/gemini-2.0-flash-lite`).

- **429 (Resource Exhausted / rate limit)**  
  O script faz até 3 tentativas com backoff. Se continuar falhando, aguarde alguns minutos ou verifique sua cota na API do Gemini.

## Estrutura do projeto

```
card-creator/
├── main.py           # Ponto de entrada
├── pdf_reader.py     # Extração de texto e tabelas do PDF
├── gemini_client.py  # Integração com a API do Gemini
├── github_client.py  # Criação de issues no GitHub
├── project_client.py # Integração com GitHub Projects v2 (GraphQL)
├── models.py        # Estruturas de dados (Card, PDFContent)
├── requirements.txt
├── .env.example
└── README.md
```

## Regras de classificação (Gemini)

- **Front-End:** UI, telas, formulários, UX, componentes visuais
- **Back-End:** API, banco de dados, autenticação, regras de negócio, serviços

## Licença

MIT License - veja o arquivo [LICENSE](LICENSE).
