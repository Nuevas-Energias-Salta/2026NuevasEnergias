$key = "TU_APPI_KEY"
$token = "TU_TOKEN"
$boardId = "69540b41714cd45de3d5bcac"

# 1. Limpiar/Fix Etiquetas
$labels = curl.exe -s "https://api.trello.com/1/boards/$boardId/labels?key=$key&token=$token" | ConvertFrom-Json
$mapping = @{
    "green"  = "T1-B2C"
    "yellow" = "T2-B2C"
    "orange" = "T3-B2B"
    "purple" = "T4-B2B"
    "blue"   = "Marca Personal"
}

$labelIds = @{}

foreach ($color in $mapping.Keys) {
    $name = $mapping[$color]
    $existing = $labels | Where-Object { $_.color -eq $color } | Select-Object -First 1
    if ($existing) {
        $lid = $existing.id
        # Update name
        $body = @{ name = $name } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.trello.com/1/labels/$lid?key=$key&token=$token" -Method PUT -Body $body -ContentType "application/json" > $null
        $labelIds[$name] = $lid
    }
    else {
        # Create new
        $body = @{ name = $name; color = $color; idBoard = $boardId } | ConvertTo-Json
        $nl = Invoke-RestMethod -Uri "https://api.trello.com/1/labels?key=$key&token=$token" -Method POST -Body $body -ContentType "application/json"
        $labelIds[$name] = $nl.id
    }
}

# 2. Actualizar Tarjetas (Fechas + Labels)
$cards = curl.exe -s "https://api.trello.com/1/boards/$boardId/cards?key=$key&token=$token&fields=name,id" | ConvertFrom-Json

$updates = @(
    @{match = "F1 - Upgrade Termostatos"; due = "2026-03-15T12:00:00Z"; label = "T2-B2C" },
    @{match = "F2 - Calefaccion Solar"; due = "2026-03-20T12:00:00Z"; label = "T2-B2C" },
    @{match = "H1 - Prospects Edesa"; due = "2026-03-15T12:00:00Z"; label = "T3-B2B" },
    @{match = "MP1 - Activar Esquema"; due = "2026-03-10T12:00:00Z"; label = "Marca Personal" },
    @{match = "T1-Obra - Programa"; due = "2026-03-31T12:00:00Z"; label = "T1-B2C" },
    @{match = "F3 - B2C a B2B"; due = "2026-03-25T12:00:00Z"; label = "T3-B2B" },
    @{match = "FB1 - Gestion Energetica"; due = "2026-03-31T12:00:00Z"; label = "T4-B2B" },
    @{match = "F4 - Crosselling Estacional Verano->Invierno"; due = "2026-04-15T12:00:00Z"; label = "T2-B2C" },
    @{match = "H2 - Agro y Zonas Rurales"; due = "2026-05-15T12:00:00Z"; label = "T3-B2B" },
    @{match = "H3 - Backup para Empresas"; due = "2026-05-20T12:00:00Z"; label = "T3-B2B" },
    @{match = "MP3 - Diagnosticos Energeticos"; due = "2026-05-10T12:00:00Z"; label = "Marca Personal" },
    @{match = "H4 - Nuevos Residenciales"; due = "2026-06-15T12:00:00Z"; label = "T1-B2C" },
    @{match = "N3 - Ads Biomasa"; due = "2026-08-01T12:00:00Z"; label = "T1-B2C" },
    @{match = "F4 - Crosselling Estacional Invierno->Verano"; due = "2026-08-20T12:00:00Z"; label = "T2-B2C" },
    @{match = "Farming B2C (T2)"; due = "2026-03-05T12:00:00Z"; label = "T2-B2C" },
    @{match = "Farming B2B (T4)"; due = "2026-03-05T12:00:00Z"; label = "T4-B2B" },
    @{match = "Hunting B2B (T3)"; due = "2026-03-05T12:00:00Z"; label = "T3-B2B" },
    @{match = "Marca Personal Agustin"; due = "2026-03-05T12:00:00Z"; label = "Marca Personal" },
    @{match = "Disenar flujo de contacto"; due = "2026-03-05T12:00:00Z"; label = "T3-B2B" },
    @{match = "Configurar Nuevi"; due = "2026-03-07T12:00:00Z"; label = "T2-B2C" },
    @{match = "Subir planilla de Casos"; due = "2026-03-08T12:00:00Z"; label = "Marca Personal" },
    @{match = "Reactivar Podcast"; due = "2026-03-20T12:00:00Z"; label = "Marca Personal" }
)

foreach ($upd in $updates) {
    $card = $cards | Where-Object { $_.name -like "*$($upd.match)*" } | Select-Object -First 1
    if ($card) {
        $cid = $card.id
        $due = $upd.due
        $lid = $labelIds[$upd.label]
        
        # Update Due
        $body = @{ due = $due } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.trello.com/1/cards/$cid?key=$key&token=$token" -Method PUT -Body $body -ContentType "application/json" > $null
        
        # Add Label (check if already has it to avoid duplicates)
        # Actually POSTing to idLabels adds it if not present.
        if ($lid) {
            try {
                Invoke-RestMethod -Uri "https://api.trello.com/1/cards/$cid/idLabels?key=$key&token=$token&value=$lid" -Method POST > $null
            }
            catch {}
        }
        Write-Host "Update OK: $($card.name)"
    }
}
Write-Host "DONE"
