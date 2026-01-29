#!/usr/bin/env bash
# Roda main.py para cada arquivo .pdf na pasta (ou na pasta informada).

DIR="${1:-.}"

if [[ ! -d "$DIR" ]]; then
  echo "Pasta não encontrada: $DIR"
  exit 1
fi

shopt -s nullglob
count=0
for f in "$DIR"/*.pdf; do
  echo ""
  echo "=============================================="
  echo "Processando: $f"
  echo "=============================================="
  python main.py "$f"
  ((count++))
done

if [[ $count -eq 0 ]]; then
  echo "Nenhum arquivo .pdf encontrado em: $DIR"
  exit 0
fi

echo ""
echo "Concluído: $count PDF(s) processado(s)."
