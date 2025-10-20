# Script de verificación pre-despliegue
Write-Host "🔍 Verificando configuración para Railway..." -ForegroundColor Cyan
Write-Host ""

$errors = @()
$warnings = @()

# Verificar archivos necesarios
$requiredFiles = @(
    "Dockerfile",
    "requirements.txt",
    "manage.py",
    "railway.json",
    ".dockerignore",
    ".gitignore"
)

Write-Host "📁 Verificando archivos necesarios..." -ForegroundColor Yellow
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (no encontrado)" -ForegroundColor Red
        $errors += "Archivo faltante: $file"
    }
}

Write-Host ""

# Verificar .env.example
if (Test-Path ".env.example") {
    Write-Host "✅ .env.example existe (plantilla para variables)" -ForegroundColor Green
} else {
    Write-Host "⚠️  .env.example no encontrado" -ForegroundColor Yellow
    $warnings += ".env.example no encontrado"
}

Write-Host ""

# Verificar que .env no esté en Git
if (Test-Path ".env") {
    Write-Host "⚠️  Archivo .env encontrado localmente" -ForegroundColor Yellow
    Write-Host "   Asegúrate de que esté en .gitignore" -ForegroundColor Yellow
    
    $gitignoreContent = Get-Content ".gitignore" -ErrorAction SilentlyContinue
    if ($gitignoreContent -match "\.env") {
        Write-Host "   ✅ .env está en .gitignore" -ForegroundColor Green
    } else {
        Write-Host "   ❌ .env NO está en .gitignore" -ForegroundColor Red
        $errors += ".env no está en .gitignore"
    }
}

Write-Host ""

# Verificar que whitenoise esté en requirements.txt
$requirements = Get-Content "requirements.txt" -ErrorAction SilentlyContinue
if ($requirements -match "whitenoise") {
    Write-Host "✅ whitenoise en requirements.txt" -ForegroundColor Green
} else {
    Write-Host "❌ whitenoise NO está en requirements.txt" -ForegroundColor Red
    $errors += "whitenoise faltante en requirements.txt"
}

Write-Host ""

# Verificar gunicorn
if ($requirements -match "gunicorn") {
    Write-Host "✅ gunicorn en requirements.txt" -ForegroundColor Green
} else {
    Write-Host "❌ gunicorn NO está en requirements.txt" -ForegroundColor Red
    $errors += "gunicorn faltante en requirements.txt"
}

Write-Host ""

# Verificar Git
Write-Host "📦 Verificando Git..." -ForegroundColor Yellow
if (Test-Path ".git") {
    Write-Host "  ✅ Repositorio Git inicializado" -ForegroundColor Green
    
    # Verificar si hay cambios sin commitear
    $gitStatus = git status --porcelain 2>&1
    if ($gitStatus) {
        Write-Host "  ⚠️  Hay cambios sin commitear" -ForegroundColor Yellow
        $warnings += "Hay cambios sin commitear en Git"
    } else {
        Write-Host "  ✅ No hay cambios pendientes" -ForegroundColor Green
    }
} else {
    Write-Host "  ❌ Git no inicializado" -ForegroundColor Red
    $errors += "Repositorio Git no inicializado"
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Gray

# Resumen
if ($errors.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host ""
    Write-Host "🎉 TODO LISTO PARA DESPLEGAR EN RAILWAY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Próximos pasos:" -ForegroundColor Cyan
    Write-Host "1. Sube tu código a GitHub" -ForegroundColor White
    Write-Host "   git push origin main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Ve a railway.app y crea un nuevo proyecto" -ForegroundColor White
    Write-Host "3. Conecta tu repositorio GitHub" -ForegroundColor White
    Write-Host "4. Agrega PostgreSQL a tu proyecto" -ForegroundColor White
    Write-Host "5. Configura las variables de entorno" -ForegroundColor White
    Write-Host ""
} elseif ($errors.Count -eq 0) {
    Write-Host ""
    Write-Host "⚠️  ADVERTENCIAS ENCONTRADAS ($($warnings.Count))" -ForegroundColor Yellow
    foreach ($warning in $warnings) {
        Write-Host "  • $warning" -ForegroundColor Yellow
    }
    Write-Host ""
    Write-Host "Puedes continuar, pero revisa las advertencias." -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ ERRORES ENCONTRADOS ($($errors.Count))" -ForegroundColor Red
    foreach ($error in $errors) {
        Write-Host "  • $error" -ForegroundColor Red
    }
    Write-Host ""
    Write-Host "Corrige los errores antes de desplegar." -ForegroundColor Red
}

Write-Host ""
