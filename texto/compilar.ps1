# Compila o artigo e gera texto/artigo.pdf.
# Uso (na raiz do repositório ou em texto/):  powershell -File texto/compilar.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force build | Out-Null

# Duas passagens para resolver referências cruzadas e citações.
foreach ($passagem in 1..2) {
    pdflatex -interaction=nonstopmode -file-line-error -aux-directory=build artigo.tex | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Erro na compilação. Veja texto/build/artigo.log"
        exit 1
    }
}
Write-Host "PDF gerado em $PSScriptRoot\artigo.pdf"
