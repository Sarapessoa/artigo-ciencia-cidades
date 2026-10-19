# Compila o artigo e gera texto/artigo.pdf.
# Uso (na raiz do repositório ou em texto/):  powershell -File texto/compilar.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force build | Out-Null

function Executar($programa, $argumentos) {
    & $programa @argumentos | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro em $programa. Veja texto/build/artigo.log (ou artigo.blg, para o BibTeX)"
        exit 1
    }
}

$pdflatex = @("-interaction=nonstopmode", "-file-line-error", "-aux-directory=build", "artigo.tex")
# pdflatex -> bibtex -> pdflatex 2x, para resolver citações e referências cruzadas.
Executar pdflatex $pdflatex
Executar bibtex @("build/artigo")
Executar pdflatex $pdflatex
Executar pdflatex $pdflatex
Write-Host "PDF gerado em $PSScriptRoot\artigo.pdf"
