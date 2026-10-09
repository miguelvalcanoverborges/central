# Central da Consultoria — instalação (Windows). Rodar uma vez, pelo INSTALAR.bat.
# Instala o que falta, baixa as ferramentas do PDF e cria o ícone de gorila na área de trabalho.
$ErrorActionPreference = 'Continue'
$ProgressPreference = 'SilentlyContinue'
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $raiz
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Passo($t) { Write-Host ""; Write-Host "==> $t" -ForegroundColor White }
function Ok($t) { Write-Host "    $t" -ForegroundColor Green }
function Falha($t) {
    Write-Host ""; Write-Host "    $t" -ForegroundColor Red
    Write-Host ""; Read-Host "Pressione Enter para fechar"; exit 1
}

Write-Host ""
Write-Host "  CENTRAL DA CONSULTORIA  ·  FORÇA & INTELIGÊNCIA" -ForegroundColor White
Write-Host "  Instalação (só precisa fazer uma vez; leva alguns minutos e usa a internet)"

# ------------------------------------------------------------ 1. Python
Passo "Procurando o Python"
function Achar-Python {
    foreach ($cmd in @('py -3.12', 'py -3.11', 'py -3', 'python')) {
        $partes = $cmd.Split(' ')
        $prog = $partes[0]
        $extra = @($partes | Select-Object -Skip 1)
        if (-not (Get-Command $prog -ErrorAction SilentlyContinue)) { continue }
        try {
            $exe = & $prog @extra -c "import sys; print(sys.executable if sys.version_info >= (3, 10) else '')" 2>$null
            if ($LASTEXITCODE -eq 0 -and $exe -and (Test-Path $exe.Trim())) { return $exe.Trim() }
        } catch {}
    }
    foreach ($p in @("$env:LOCALAPPDATA\Programs\Python\Python312\python.exe", "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe")) {
        if (Test-Path $p) { return $p }
    }
    return $null
}
$python = Achar-Python
if (-not $python) {
    Write-Host "    Python não encontrado. Instalando o Python 3.12..."
    try {
        if (-not (Get-Command winget -ErrorAction SilentlyContinue)) { Falha "Instale o Python pelo site python.org (marque 'Add Python to PATH') e rode o INSTALAR de novo." }
        winget install -e --id Python.Python.3.12 --scope user --accept-source-agreements --accept-package-agreements --silent | Out-Null
    } catch {}
    $python = Achar-Python
    if (-not $python) { Falha "Não consegui instalar o Python. Instale pelo site python.org (marque 'Add Python to PATH') e rode o INSTALAR de novo." }
}
Ok "Python: $python"

# ------------------------------------------------------------ 2. ambiente do programa
Passo "Preparando o programa"
$venv = Join-Path $raiz '.venv'
if (-not (Test-Path "$venv\Scripts\python.exe")) { & $python -m venv $venv; if ($LASTEXITCODE) { Falha "Falha ao criar o ambiente do programa." } }
$py = "$venv\Scripts\python.exe"
& $py -m pip install --upgrade pip --quiet --disable-pip-version-check | Out-Null
& $py -m pip install -r (Join-Path $raiz 'requirements.txt') --quiet --disable-pip-version-check
if ($LASTEXITCODE) { Falha "Falha ao instalar as bibliotecas. Confira a internet e rode o INSTALAR de novo." }
Ok "Bibliotecas instaladas"

Passo "Instalando o gerador de PDF"
& $py -m playwright install chromium
if ($LASTEXITCODE) { Falha "Falha ao baixar o gerador de PDF (Chromium). Confira a internet e rode o INSTALAR de novo." }
Ok "Gerador de PDF pronto"

# ------------------------------------------------------------ 3. Poppler (conferência PDF × planilha)
Passo "Instalando a conferência do PDF"
$ferr = Join-Path $raiz 'ferramentas\poppler'
$tem = Get-ChildItem -Path $ferr -Recurse -Filter pdftotext.exe -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $tem) {
    New-Item -ItemType Directory -Force -Path $ferr | Out-Null
    $url = $null
    try {
        $rel = Invoke-RestMethod -ErrorAction Stop -Uri 'https://api.github.com/repos/oschwartz10612/poppler-windows/releases/latest' -Headers @{ 'User-Agent' = 'central-consultoria' }
        $url = ($rel.assets | Where-Object { $_.name -like 'Release-*.zip' } | Select-Object -First 1).browser_download_url
    } catch {}
    if (-not $url) { $url = 'https://github.com/oschwartz10612/poppler-windows/releases/download/v25.12.0-0/Release-25.12.0-0.zip' }
    $zip = Join-Path $env:TEMP 'poppler-central.zip'
    try {
        Invoke-WebRequest -ErrorAction Stop -Uri $url -OutFile $zip -UseBasicParsing
        Expand-Archive -ErrorAction Stop -Path $zip -DestinationPath $ferr -Force
        Remove-Item $zip -Force
    } catch { Falha "Falha ao baixar o Poppler ($url). Confira a internet e rode o INSTALAR de novo." }
    $tem = Get-ChildItem -Path $ferr -Recurse -Filter pdftotext.exe -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $tem) { Falha "O Poppler foi baixado, mas o pdftotext.exe não apareceu." }
}
Ok "Conferência pronta"

# ------------------------------------------------------------ 4. teste rápido do motor
Passo "Testando a geração de PDF com o aluno de exemplo"
$env:PATH = "$($tem.DirectoryName);$env:PATH"
$env:PYTHONUTF8 = '1'
$tmp = Join-Path $env:TEMP 'central-teste'
& $py "$raiz\motor\consultoria-planilha\scripts\extrair_dados.py" "$raiz\motor\consultoria-planilha\exemplos\exemplo.xlsx" --saida $tmp | Out-Null
& $py "$raiz\motor\consultoria-planilha\scripts\gerar_pdf.py" "$tmp\dados.json" --saida "$tmp\teste.pdf"
if ($LASTEXITCODE) { Write-Host "    Aviso: o teste não passou. O programa abre, mas confira 'Conferir instalação' em Configurações." -ForegroundColor Yellow }
else { Ok "PDF de exemplo gerado e conferido" }
Remove-Item $tmp -Recurse -Force -ErrorAction SilentlyContinue

# ------------------------------------------------------------ 5. atalhos com o ícone de gorila
Passo "Criando o ícone na área de trabalho"
$shell = New-Object -ComObject WScript.Shell
$alvos = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
foreach ($pasta in $alvos) {
    $lnk = $shell.CreateShortcut((Join-Path $pasta 'Central da Consultoria.lnk'))
    $lnk.TargetPath = "$venv\Scripts\pythonw.exe"
    $lnk.Arguments = "`"$raiz\Central.pyw`""
    $lnk.WorkingDirectory = $raiz
    $lnk.IconLocation = "$raiz\icone\gorila.ico,0"
    $lnk.Description = 'Central da Consultoria — FORÇA & INTELIGÊNCIA'
    $lnk.Save()
}
Ok "Ícone criado na área de trabalho e no menu Iniciar"

Write-Host ""
Write-Host "  Pronto! Abra a Central pelo ícone de gorila na área de trabalho." -ForegroundColor Green
Write-Host "  Abrindo agora..."
Start-Process -FilePath "$venv\Scripts\pythonw.exe" -ArgumentList "`"$raiz\Central.pyw`"" -WorkingDirectory $raiz
Start-Sleep -Seconds 4
