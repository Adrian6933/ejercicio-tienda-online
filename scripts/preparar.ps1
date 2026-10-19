$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envFile = Join-Path $projectRoot '.env'
if (-not (Test-Path -LiteralPath $envFile)) {
    $passwordBytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($passwordBytes)
    $databasePassword = ([BitConverter]::ToString($passwordBytes)).Replace('-','').ToLower()
    $encryptionBytes = New-Object byte[] 24
    [System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($encryptionBytes)
    $encryptionKey = ([BitConverter]::ToString($encryptionBytes)).Replace('-','').ToLower()
    $template = Get-Content -LiteralPath (Join-Path $projectRoot '.env.example') -Raw
    $template = $template.Replace('POSTGRES_PASSWORD=', 'POSTGRES_PASSWORD=' + $databasePassword)
    $template += "`nKIBANA_ENCRYPTION_KEY=$encryptionKey`n"
    Set-Content -LiteralPath $envFile -Value $template -Encoding UTF8
    Write-Host '.env local creado con contraseña aleatoria. No se publica en Git.'
}
Push-Location $projectRoot
try {
    docker compose config --quiet
    if ($LASTEXITCODE -ne 0) { throw 'La configuración de Docker no es válida' }
    Write-Host 'Preparado. Arranca con: docker compose up --build -d'
} finally { Pop-Location }
