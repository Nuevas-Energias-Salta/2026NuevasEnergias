$key = "TU_APPI_KEY"
$token = "TU_TOKEN"
$boardId = "69540b41714cd45de3d5bcac"

# 1. Crear Etiquetas si no existen (y mapear IDs)
Write-Host "Mapeando etiquetas..."
$labelMap = @{}
$existingLabels = curl.exe -s "https://api.trello.com/1/boards/$boardId/labels?key=$key&token=$token" | ConvertFrom-Json
$toCreate = @(
    @{name = "T1-B2C"; color = "green" },
    @{name = "T2-B2C"; color = "yellow" },
    @{name = "T3-B2B"; color = "orange" },
    @{name = "T4-B2B"; color = "purple" },
    @{name = "Marca Personal"; color = "blue" }
)

foreach ($tc in $toCreate) {
    $existing = $existingLabels | Where-Object { $_.name -eq $tc.name }
    if ($existing) {
        $labelMap[$tc.name] = $existing.id
    }
    else {
        $name = $tc.name; $color = $tc.color
        $newLab = curl.exe -X POST "https://api.trello.com/1/labels?key=$key&token=$token&name=$name&color=$color&idBoard=$boardId" | ConvertFrom-Json
        $labelMap[$tc.name] = $newLab.id
    }
}

# 2. Mapear tarjetas existentes
$cards = curl.exe -s "https://api.trello.com/1/boards/$boardId/cards?key=$key&token=$token&fields=name,id" | ConvertFrom-Json

# 3. Definir actualizaciones (Vencimiento + Etiqueta)
$updates = @(
    # Q1 - Marzo 2026
    @{match = "F1 - Upgrade Termostatos"; due = "2026-03-15T12:00:00Z"; label = "T2-B2C" },
    @{match = "F2 - Calefaccion Solar"; due = "2026-03-20T12:00:00Z"; label = "T2-B2C" },
    @{match = "H1 - Prospects Edesa"; due = "2026-03-15T12:00:00Z"; label = "T3-B2B" },
    @{match = "MP1 - Activar Esquema"; due = "2026-03-10T12:00:00Z"; label = "Marca Personal" },
    @{match = "T1-Obra - Programa"; due = "2026-03-31T12:00:00Z"; label = "T1-B2C" },
    @{match = "F3 - B2C a B2B"; due = "2026-03-25T12:00:00Z"; label = "T3-B2B" },
    @{match = "FB1 - Gestion Energetica"; due = "2026-03-31T12:00:00Z"; label = "T4-B2B" },
    
    # Q2 - Mayo 2026
    @{match = "F4 - Crosselling Estacional Verano->Invierno"; due = "2026-04-15T12:00:00Z"; label = "T2-B2C" },
    @{match = "H2 - Agro y Zonas Rurales"; due = "2026-05-15T12:00:00Z"; label = "T3-B2B" },
    @{match = "H3 - Backup para Empresas"; due = "2026-05-20T12:00:00Z"; label = "T3-B2B" },
    @{match = "MP3 - Diagnosticos Energeticos"; due = "2026-05-10T12:00:00Z"; label = "Marca Personal" },
    @{match = "H4 - Nuevos Residenciales"; due = "2026-06-15T12:00:00Z"; label = "T1-B2C" },
    
    # Q3 - Agosto 2026
    @{match = "N3 - Ads Biomasa"; due = "2026-08-01T12:00:00Z"; label = "T1-B2C" },
    @{match = "F4 - Crosselling Estacional Invierno->Verano"; due = "2026-08-20T12:00:00Z"; label = "T2-B2C" },
    
    # Setup / Estrategia
    @{match = "Farming B2C (T2)"; due = "2026-03-05T12:00:00Z"; label = "T2-B2C" },
    @{match = "Farming B2B (T4)"; due = "2026-03-05T12:00:00Z"; label = "T4-B2B" },
    @{match = "Hunting B2B (T3)"; due = "2026-03-05T12:00:00Z"; label = "T3-B2B" },
    @{match = "Marca Personal Agustin"; due = "2026-03-05T12:00:00Z"; label = "Marca Personal" },
    
    # Tareas
    @{match = "Disenar flujo de contacto"; due = "2026-03-05T12:00:00Z"; label = "T3-B2B" },
    @{match = "Configurar Nuevi"; due = "2026-03-07T12:00:00Z"; label = "T2-B2C" },
    @{match = "Subir planilla de Casos"; due = "2026-03-08T12:00:00Z"; label = "Marca Personal" },
    @{match = "Reactivar Podcast"; due = "2026-03-20T12:00:00Z"; label = "Marca Personal" }
)

Write-Host "Aplicando fechas y etiquetas..."
foreach ($upd in $updates) {
    $card = $cards | Where-Object { $_.name -like "*$($upd.match)*" }
    if ($card) {
        $cardId = $card.id
        $due = $upd.due
        $labelId = $labelMap[$upd.label]
        
        # Update Due Date
        curl.exe -X PUT "https://api.trello.com/1/cards/$cardId?key=$key&token=$token&due=$due" -s > $null
        
        # Add Label
        if ($labelId) {
            curl.exe -X POST "https://api.trello.com/1/cards/$cardId/idLabels?key=$key&token=$token&value=$labelId" -s > $null
        }
        
        Write-Host "OK: $($card.name)" -ForegroundColor Green
    }
    else {
        Write-Host "No encontrada: $($upd.match)" -ForegroundColor Gray
    }
}

Write-Host "`n=== CALENDARIO Y LABELS COMPLETOS ===" -ForegroundColor Cyan
