# Script para construir y ejecutar el contenedor Docker localmente
# Esto te permite probar antes de subir a Railway

Write-Host "🐳 Construyendo imagen Docker..." -ForegroundColor Cyan

# Construir la imagen
docker build -t backend-taller:local .

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Imagen construida exitosamente" -ForegroundColor Green
    Write-Host ""
    Write-Host "Para ejecutar el contenedor localmente, usa:" -ForegroundColor Yellow
    Write-Host "docker run -p 8000:8000 --env-file .env backend-taller:local" -ForegroundColor White
    Write-Host ""
    Write-Host "Luego accede a: http://localhost:8000" -ForegroundColor Cyan
} else {
    Write-Host "❌ Error al construir la imagen" -ForegroundColor Red
}
