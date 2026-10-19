"""Gera texto/overleaf.zip para criar o projeto no Overleaf (New Project -> Upload Project).

Uso: python texto/gerar_overleaf.py
"""
import zipfile
from pathlib import Path

TEXTO = Path(__file__).resolve().parent
RAIZ = TEXTO.parent

ARQUIVOS = {
    "main.tex": TEXTO / "artigo.tex",
    "referencias.bib": TEXTO / "referencias.bib",
    "unsrt-pt.bst": TEXTO / "unsrt-pt.bst",
    "figuras/conectividade.pdf": RAIZ / "figuras" / "conectividade.pdf",
    "figs/unifor_logo.png": TEXTO / "figs" / "unifor_logo.png",  # opcional
}

destino = TEXTO / "overleaf.zip"
with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
    for nome, origem in ARQUIVOS.items():
        if origem.exists():
            zf.write(origem, nome)
            print("incluído:", nome)
        else:
            print("ausente: ", nome)
print("Gerado", destino)
