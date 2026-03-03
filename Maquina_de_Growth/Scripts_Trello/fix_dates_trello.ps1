$key = "TU_APPI_KEY"
$token = "TU_TOKEN"

function Update-TrelloCard($cardId, $due, $labelName) {
    # 1. Update Due Date
    if ($due) {
        $body = @{ due = $due } | ConvertTo-Json
        Invoke-RestMethod -Uri "https://api.trello.com/1/cards/$cardId?key=$key&token=$token" -Method PUT -Body $body -ContentType "application/json" > $null
    }
    
    # 2. Add Label (we need label ID)
    # Mapping label IDs from board (I'll hardcode them based on existing labels to be safe)
    # T1-B2C: 699e2d6cfa9e3992b8cb6744
    # T2-B2C: 699e2d6d429b0ada642d48d3
    # T3-B2B: 699e2d6d429b0ada642d48d4
    # T4-B2B: 699e2d6e429b0ada642d48d5
    # Marca Personal: 699e2d6e429b0ada642d48d6
    
    $labelIds = @{
        "T1-B2C"         = "699e2d6cfa9e3992b8cb6744"
        "T2-B2C"         = "699e2d6d429b0ada642d48d3"
        "T3-B2B"         = "699e2d6d429b0ada642d48d4"
        "T4-B2B"         = "699e2d6e429b0ada642d48d5"
        "Marca Personal" = "699e2d6e429b0ada642d48d6"
    }
    
    if ($labelName -and $labelIds.ContainsKey($labelName)) {
        $lid = $labelIds[$labelName]
        try {
            Invoke-RestMethod -Uri "https://api.trello.com/1/cards/$cardId/idLabels?key=$key&token=$token&value=$lid" -Method POST > $null
        }
        catch {}
    }
}

Write-Host "Iniciando actualizacion masiva de fechas..."

# Q1
Update-TrelloCard "699e2a2a3152ef1206e787b5" "2026-03-15T12:00:00Z" "T2-B2C" # F1
Update-TrelloCard "699e2a2b3e1a471d3a5c8c8a" "2026-03-20T12:00:00Z" "T2-B2C" # F2
Update-TrelloCard "699e2a2cd60cd63455363c9b" "2026-03-15T12:00:00Z" "T3-B2B" # H1
Update-TrelloCard "699e2a2da107395ddf505637" "2026-03-10T12:00:00Z" "Marca Personal" # MP1
Update-TrelloCard "699e2b210a26342961d075f6" "2026-03-31T12:00:00Z" "T1-B2C" # T1-Obra
Update-TrelloCard "699e2a2ef8522186945b8c23" "2026-03-25T12:00:00Z" "T3-B2B" # F3
Update-TrelloCard "699e2a2fcbac4a2e26ef2f2c" "2026-03-31T12:00:00Z" "T4-B2B" # FB1

# Q2
Update-TrelloCard "699e2a307cb939d2f37d79fa" "2026-04-15T12:00:00Z" "T2-B2C" # F4
Update-TrelloCard "699e2a316f46577c1cc86f15" "2026-05-15T12:00:00Z" "T3-B2B" # H2
Update-TrelloCard "699e2a32f2629f6f688ddb65" "2026-05-20T12:00:00Z" "T3-B2B" # H3
Update-TrelloCard "699e2a331822183d75ca2606" "2026-05-10T12:00:00Z" "Marca Personal" # MP3
Update-TrelloCard "699e2a347b0fdef1d1305e93" "2026-06-15T12:00:00Z" "T1-B2C" # H4

# Q3
Update-TrelloCard "699e2a3698ae5606a5722b94" "2026-08-01T12:00:00Z" "T1-B2C" # N3 (Ads Biomasa)
Update-TrelloCard "699e2a37b1404136506d4a62" "2026-08-20T12:00:00Z" "T2-B2C" # F4 (Invitero->Verano)

# Setup/Tasks
Update-TrelloCard "699e2a372d5892109918b4f1" "2026-03-05T12:00:00Z" "T3-B2B"
Update-TrelloCard "699e2a39f28dee3a61b91057" "2026-03-07T12:00:00Z" "T2-B2C"
Update-TrelloCard "699e2a39b5fd347c5966e866" "2026-03-08T12:00:00Z" "Marca Personal"
Update-TrelloCard "699e2a3ad27bd58261248c5e" "2026-03-20T12:00:00Z" "Marca Personal"

Update-TrelloCard "699e2a2681b48aff5d624969" "2026-03-05T12:00:00Z" "T2-B2C" # Farming B2C
Update-TrelloCard "699e2a27a2bd62e5d4354e5f" "2026-03-05T12:00:00Z" "T4-B2B" # Farming B2B
Update-TrelloCard "699e2a2822bd1ff30528aa5e" "2026-03-05T12:00:00Z" "T3-B2B" # Hunting B2B
Update-TrelloCard "699e2a2922fb91a5b9acc39e" "2026-03-05T12:00:00Z" "Marca Personal" # Marca Personal

Write-Host "Actualizacion finalizada."
