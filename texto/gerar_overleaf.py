"""Gera o pacote do artigo para o Overleaf.

Uso:
    python texto/gerar_overleaf.py                 # gera texto/overleaf.zip (Upload Project)
    python texto/gerar_overleaf.py --enviar URL    # envia ao projeto pela integração Git

URL é o endereço Git do projeto (Menu -> Integrations -> Git), como
https://git.overleaf.com/<id>. Só é preciso informá-lo na primeira vez: o clone
fica em texto/overleaf/ e é reaproveitado nos envios seguintes. O Git pede a
autenticação ao clonar (usuário "git", senha = token do Overleaf) e o
gerenciador de credenciais a guarda; o token não é gravado neste repositório.
"""
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

TEXTO = Path(__file__).resolve().parent
RAIZ = TEXTO.parent
CLONE = TEXTO / "overleaf"

ARQUIVOS = {
    "main.tex": TEXTO / "artigo.tex",
    "referencias.bib": TEXTO / "referencias.bib",
    "unsrt-pt.bst": TEXTO / "unsrt-pt.bst",
    "figuras/conectividade.pdf": RAIZ / "figuras" / "conectividade.pdf",
    "figs/unifor_logo.png": TEXTO / "figs" / "unifor_logo.png",  # opcional
}


def presentes():
    for nome, origem in ARQUIVOS.items():
        if origem.exists():
            yield nome, origem
        else:
            print("ausente: ", nome)


def gerar_zip():
    destino = TEXTO / "overleaf.zip"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as zf:
        for nome, origem in presentes():
            zf.write(origem, nome)
            print("incluído:", nome)
    print("Gerado", destino)


def git(*args):
    return subprocess.run(["git", "-C", str(CLONE), *args], check=True,
                          capture_output=True, text=True).stdout


def enviar(url):
    if not CLONE.exists():
        if url is None:
            sys.exit("Informe o endereço Git do projeto na primeira vez: --enviar URL")
        subprocess.run(["git", "clone", url, str(CLONE)], check=True)
    antes = git("rev-parse", "HEAD")
    git("pull", "--ff-only")
    if git("rev-parse", "HEAD") != antes:
        sys.exit("Há edições novas feitas no Overleaf (veja texto/overleaf/). Passe-as "
                 "para texto/artigo.tex e rode de novo; nada foi sobrescrito.")
    for nome, origem in presentes():
        alvo = CLONE / nome
        alvo.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origem, alvo)
        print("copiado: ", nome)
    git("add", *ARQUIVOS)
    if not git("status", "--porcelain"):
        print("O projeto no Overleaf já está atualizado.")
        return
    git("commit", "-m", "Atualiza o artigo a partir do repositório de análise")
    git("push")
    print("Enviado ao Overleaf.")


if __name__ == "__main__":
    if "--enviar" in sys.argv:
        i = sys.argv.index("--enviar")
        enviar(sys.argv[i + 1] if len(sys.argv) > i + 1 else None)
    else:
        gerar_zip()
