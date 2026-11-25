param(
    [ValidateSet('estudiantes', 'certificados')]
    [string]$Recurso = 'estudiantes'
)

$clave = 'educonnect-demo-clave-2026'
$veces = if ($Recurso -eq 'certificados') { 3 } else { 6 }
$url = "http://localhost:8000/api/$Recurso"

Write-Host "Recurso: $Recurso | Solicitudes previstas: $veces"
Write-Host "Inicio: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

1..$veces | ForEach-Object {
    $codigo = curl.exe -s -o NUL -w "%{http_code}" `
        -H "apikey: $clave" $url
    Write-Host "Solicitud $_ -> HTTP $codigo"
}
Write-Host "Fin: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
