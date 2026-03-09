$key = "TU_API_KEY"
$token = "TU_TOKEN"

# IDs de listas del tablero "Plan Mkt y comunicacion 26"
$L_ESTRATEGIA = "695bc7fa2c4329f2e7595d7e"
$L_Q1 = "69540b8f9949627e96ecdeef"
$L_Q2 = "69540ba64e8e3447b2bee993"
$L_Q3 = "69540bc1f1f2117b0484be86"
$L_TAREAS = "69540b41714cd45de3d5bcdc"

function New-TrelloCard($listId, $name, $desc) {
    $body = @{
        idList = $listId
        name   = $name
        desc   = $desc
        key    = $key
        token  = $token
    }
    try {
        $r = Invoke-RestMethod -Uri "https://api.trello.com/1/cards" -Method POST -Body $body
        Write-Host "OK: $name" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR: $name - $_" -ForegroundColor Red
    }
    Start-Sleep -Milliseconds 300
}

# =========================================================
# LISTA: Estrategia
# =========================================================

New-TrelloCard $L_ESTRATEGIA "Farming B2C (T2) - Base 1000+ clientes" @"
[EJE ESTRATEGICO] Farming B2C - Target T2 (B2C cliente actual)

Base instalada: 1000+ clientes con distintos productos
- 500+ con PRE (piso radiante) -> candidatos FV y termostatos
- Clientes de invierno -> ofrecerles productos de verano (medias temporadas)
- Clientes de verano -> ofrecerles productos de invierno
- Clientes con solo termotanque -> candidatos para todo el portfolio

Idea principal: retener y aumentar valor por cliente -> mantenimiento + upgrades + cross-selling + referidos
"@

New-TrelloCard $L_ESTRATEGIA "Farming B2B (T4) - Clientes FV existentes" @"
[EJE ESTRATEGICO] Farming B2B - Target T4 (B2B cliente actual)

Empresas que ya trabajan con NE (FV, balance neto, eficiencia)
Objetivo: 2+ servicios/anio por cliente

70% del revenue B2B ya es recurrente o por referidos -> sistematizar.

Servicios a ofrecer:
- Gestion energetica recurrente (informes, alertas, revision trimestral)
- Ampliaciones de capacidad FV
- Upgrades a baterias/backup
- Gestoria regulatoria (Balance Neto, tramites EDESA/COPAIPA)
"@

New-TrelloCard $L_ESTRATEGIA "Hunting B2B (T3) - Prospects Edesa + LinkedIn" @"
[EJE ESTRATEGICO] Hunting B2B - Target T3 (B2B no cliente)

Target: Duenios de pymes ~50 anios, prolijos, les preocupa costo/eficiencia/riesgo
Flujo: Factura -> Diagnostico simple -> Reunion calificada -> Propuesta -> Contrato

Palancas disponibles:
- Base Prospects Edesa (NIS de empresas con alto consumo electrico) <- PRIORIDAD
- LinkedIn de Agustin (2.477 seguidores)
- Red Vistage
- Pipeline activo: $4.968M ARS nominal

Deal clave en pipeline: La Guapeada ($315M, en etapa final de cierre)
"@

New-TrelloCard $L_ESTRATEGIA "Marca Personal Agustin - Motor de Leads B2B" @"
[EJE ESTRATEGICO] Marca Personal - Target T3 (B2B inbound)

Agustin = Ingeniero Civil + CEO + Speaker + Asesor energetico
Diferencial: primero eficiencia, despues solar
Canales: LinkedIn (2.477 seg) + Instagram (4.500 seg)

Loop:
Empresa con problema energetico -> Consultoria -> Eficiencia -> Renovables -> Cliente T4 recurrente

Activos disponibles:
- Esquema de posteos LinkedIn ya planificado (workspace LinkedIn Writer)
- Casos de exito con datos reales (tabacalero, Dal Borgo, estacion GNC)
- Logos de empresas clientes reconocidas
- 2 episodios de podcast grabados (a reactivar)
- Presentaciones Vistage/UIS
"@

# =========================================================
# LISTA: Q1 - Hasta Marzo
# =========================================================

New-TrelloCard $L_Q1 "[URGENTE] F1 - Upgrade Termostatos Smart (QUICK WIN - T2)" @"
TARGET: T2 (clientes PRE existentes)
Producto: Termostato WiFi - upgrade sin obra
Timing: AHORA -> antes del invierno (marzo)

Mensaje clave: Controla tu calefaccion desde el celu, sin obra ni rompimiento de piso
CTA: Solicitar presupuesto por WA
Canal: WhatsApp via Whaticket - base propia

NOTAS:
- Base no segmentada (analogico vs digital), pero casi todos tienen los viejos
- Lanzar a TODA la base PRE
- Nuevi (agente virtual) puede automatizar la primera etapa hasta fase de precio

CHECKLIST PRE-LANZAMIENTO:
[ ] Exportar base PRE de NoCRM
[ ] Preparar mensaje WA (copy aprobado)
[ ] Configurar flujo en Nuevi
[ ] Definir precio y condiciones del upgrade
[ ] Brief de diseno para flyer WA
[ ] Aprobar pieza grafica
[ ] Lanzar campania
[ ] Medir: tasa de respuesta + conversiones
"@

New-TrelloCard $L_Q1 "[URGENTE] F2 - Calefaccion Solar: Calefacciona Gratis (T2)" @"
TARGET: T2 (clientes PRE con alta factura electrica en invierno)
Producto: PRE + FV On-Grid Balance Neto
Timing: Marzo-Abril - ANTES del invierno

Mensaje clave: Cuanto pagas de luz en invierno? Con solar, te lo eliminamos
CTA: Compartir ultima factura de EDESA para analisis gratuito
Canal: WhatsApp (Whaticket) + Email

TACTICA EXTRA: Para clientes en obra -> iniciar tramites de Balance Neto ahora -> al terminar obra se conectan directo

CHECKLIST PRE-LANZAMIENTO:
[ ] Segmentar base PRE por zona/perfil
[ ] Redactar mensaje WA + email
[ ] Preparar template de analisis de factura
[ ] Brief diseno flyer Calefacciona Gratis
[ ] Aprobar pieza grafica
[ ] Lanzar campania
[ ] Medir: leads calificados, propuestas enviadas
"@

New-TrelloCard $L_Q1 "[URGENTE] H1 - Prospects Edesa: Contacto Saliente B2B (T3)" @"
TARGET: T3 (B2B no cliente - empresas con alto consumo)
Producto: FV On-Grid Autoconsumo
Timing: MARZO - arrancar YA

Palanca: Base de datos con NIS de empresas de alto consumo electrico (workspace Prospects Edesa)
Canal: WhatsApp directo + LinkedIn + Visitas
Mensaje clave: Tu factura de EDESA dice mas de lo que pensas. Analizamosla juntos
CTA: Analisis energetico gratuito (revision factura/potencia/reactiva)

Flujo T3:
1. Contacto inicial (WA/LinkedIn) con propuesta de analisis gratuito
2. Empresa comparte factura
3. Hacemos diagnostico basico (potencia contratada, reactiva, horario)
4. Reunion de presentacion de resultados
5. Propuesta comercial

CHECKLIST:
[ ] Exportar y limpiar base Prospects Edesa
[ ] Disenar mensaje de apertura (WA y LinkedIn)
[ ] Definir plantilla de analisis de factura rapido
[ ] Asignar responsable comercial
[ ] Arrancar contacto: objetivo 20 empresas/semana
[ ] Medir: reuniones conseguidas, propuestas enviadas
"@

New-TrelloCard $L_Q1 "MP1 - Activar Esquema de Posteos LinkedIn (T3 inbound)" @"
TARGET: T3 (B2B inbound via marca personal)
Canal: LinkedIn personal de Agustin (2.477 seguidores)
Timing: ACTIVAR YA - esquema de posteos ya planificado en workspace LinkedIn Writer

Mix de contenido:
- 40% casos/aprendizajes propios
- 30% educacion/conceptos energeticos
- 20% management/liderazgo
- 10% opinion del sector

Frecuencia: 2-3 posts/semana
Tono: conversacional con autoridad tecnica - historia -> aprendizaje
CTA: Escribime / charlemos / analizamos tu caso?

Series a lanzar:
- Antes de poner paneles, hace esto
- Lo que tu factura de EDESA no te dice

CHECKLIST:
[ ] Revisar y aprobar calendario de posteos (workspace LinkedIn Writer)
[ ] Redactar primeros 4 posts de la serie
[ ] Preparar imagenes/graficos de apoyo
[ ] Publicar con cadencia 2-3x/semana
[ ] Medir: nuevos seguidores, consultas inbound
"@

New-TrelloCard $L_Q1 "F3 - B2C a B2B: Ya ahorras en tu casa, y en tu empresa? (T2->T3)" @"
TARGET: T2 -> T3 (clientes PRE que son empresarios)
Producto: FV On-Grid Autoconsumo para empresas
Timing: Marzo - continuo

Mensaje clave: Ya ahorras en tu casa. Por que no en tu empresa?
CTA: Compartir factura energetica de la empresa para analisis gratuito
Canal: WhatsApp (Whaticket) + Email

NOTA: Base no segmentada por perfil empresarial, pero por domicilio se puede inferir quienes son decisores.

CHECKLIST:
[ ] Hacer primer filtro manual por zona geografica (inferir empresarios)
[ ] Redactar mensaje WA + email
[ ] Definir template de analisis de factura empresarial
[ ] Lanzar a segmento identificado
[ ] Medir: conversion T2->T3, ticket promedio
"@

New-TrelloCard $L_Q1 "FB1 - Gestion Energetica Recurrente clientes FV (T4)" @"
TARGET: T4 (B2B cliente FV activo)
Servicio: Informes periodicos, alertas, revision trimestral, gestoria regulatoria
Canal: WhatsApp + Email + Reuniones periodicas
Timing: Arrancar en Q1 - proceso continuo

Objetivo: 2+ servicios/anio por cliente. 70% del revenue B2B ya es recurrente.
Mensaje clave: Tu sistema sigue produciendo. Asegurate de aprovecharlo al maximo
CTA: Activar servicio de gestion energetica mensual

CHECKLIST:
[ ] Mapear clientes FV activos sin servicio de gestion
[ ] Definir oferta de gestion energetica (paquetes y precios)
[ ] Contactar clientes T4 uno a uno
[ ] Medir: % clientes con servicio activo, NPS, upsell rate
"@

# =========================================================
# LISTA: Q2 - Abril - Junio
# =========================================================

New-TrelloCard $L_Q2 "F4 - Crosselling Estacional Verano->Invierno (T2)" @"
TARGET: T2 (clientes con productos de verano)
Timing: Abril - media temporada

Productos a ofrecer a clientes de verano:
- Biomasa (Nuke/Ofen)
- PRE para obras en construccion
- FV Balance Neto para alto consumo

Canal: WhatsApp (Whaticket) + Email

CHECKLIST:
[ ] Segmentar base: clientes con bombas de calor pileta, hornos Aire Libre
[ ] Redactar mensaje para cada sub-segmento
[ ] Brief diseno pieza para cada producto
[ ] Lanzar en Abril
[ ] Medir respuesta y ventas cruzadas
"@

New-TrelloCard $L_Q2 "H2 - Agro y Zonas Rurales (T3)" @"
TARGET: T3 (B2B no cliente - productores agropecuarios)
Producto: Bombas Solares Sumergibles + FV Off-Grid
Timing: Q2

Mensaje clave: Agua y energia en el campo. Baja tus costos y se mas productivo
CTA: Relevamiento en campo
Canal: Red de contactos rurales + LinkedIn + eventos agropecuarios

IDEA: Merchandising como puerta de entrada en eventos rurales

CHECKLIST:
[ ] Mapear eventos agropecuarios del NOA en Q2
[ ] Identificar contactos rurales en la base existente
[ ] Redactar mensaje especifico para productor agropecuario
[ ] Preparar material de campo (presentacion, ficha tecnica)
[ ] Definir presupuesto de merchandising
[ ] Medir: leads rurales, presupuestos enviados
"@

New-TrelloCard $L_Q2 "H3 - Backup para Empresas (T3)" @"
TARGET: T3 (B2B no cliente - empresas con operaciones criticas)
Producto: Sistemas de Backup Electrico
Timing: Continuo - pico en verano por cortes - lanzar en Q2

Mensaje clave: Los cortes de luz te cuestan mas que la solucion
CTA: Analisis de criticidad electrica gratuito
Canal: LinkedIn + WhatsApp + red de contactos
Target especifico: servidores, produccion, salud, GNC, logistica

CHECKLIST:
[ ] Identificar en base Prospects Edesa las empresas con operaciones criticas
[ ] Redactar mensaje de apertura especifico
[ ] Preparar caso de uso (costo de 1 hora de corte vs costo del backup)
[ ] Lanzar via LinkedIn + WA
[ ] Medir: leads calificados, conversion a propuesta
"@

New-TrelloCard $L_Q2 "MP3 - Diagnosticos Energeticos como CTA Principal (T3)" @"
TARGET: T3 (B2B inbound via consultoria)
Servicio: Diagnostico energetico gratuito o de bajo costo como oferta de entrada
Canal: LinkedIn + IG + Red Vistage + referidos
Timing: Q2 en adelante - cuando el flujo de contenido este activo

Loop: Diagnostico -> Confianza -> Propuesta comercial

CHECKLIST:
[ ] Disenar template de diagnostico rapido (1 hoja)
[ ] Crear post de oferta diagnostico gratuito para LinkedIn
[ ] Definir limite de diagnosticos/mes para no saturar
[ ] Registrar cada diagnostico en NoCRM
[ ] Medir: diagnosticos/mes, conversion a propuesta
"@

New-TrelloCard $L_Q2 "H4 - Nuevos Residenciales en Obra (T1)" @"
TARGET: T1 (B2C no cliente - familias en obra o por construir)
Productos: PRE, Biomasa, Termotanque Solar, Balance Neto residencial
Timing: Q2 - pico en construccion primavera/verano

Mensaje clave: Construis sin gas. Nosotros te lo hacemos facil y eficiente
CTA: Pack claro, cotizacion en 24/48 hs por WA
Canal: Instagram (organico + ads) + referidos de T2 + estudios de arquitectura

CHECKLIST:
[ ] Identificar estudios de arquitectura de la zona para alianza
[ ] Crear contenido IG especifico para persona en obra
[ ] Definir packs de productos para obra sin gas
[ ] Medir: CPL, conversion WA->presupuesto, ticket promedio
"@

# =========================================================
# LISTA: Q3 - Julio - Sep
# =========================================================

New-TrelloCard $L_Q3 "N3 - Ads Biomasa Temporada Invierno (T1)" @"
TARGET: T1 (B2C no cliente - hogares)
Producto: Estufas Nuke + Estufas Pellet Ofen
Timing: Mayo-Agosto (pico invierno)

Mensaje clave: El invierno llego. Calefacciona con eficiencia y estilo
CTA: Ver catalogo / solicitar presupuesto
Canal: Instagram Ads + Facebook

CHECKLIST:
[ ] Definir presupuesto de pauta
[ ] Crear creatividades (fotos/videos de productos)
[ ] Configurar audiencia en Meta Ads (radio Salta)
[ ] A/B test: Nuke vs Ofen como hero product
[ ] Medir: CPL, conversiones, ventas directas
"@

New-TrelloCard $L_Q3 "F4 - Crosselling Estacional Invierno->Verano (T2)" @"
TARGET: T2 (clientes con productos de invierno)
Timing: Agosto-Septiembre (media temporada)

Productos a ofrecer a clientes de invierno:
- Bombas de calor para piletas
- Linea Aire Libre Nuke (parrillas, hornos)
- FV On-Grid (el ahorro del verano paga el invierno)

Canal: WhatsApp (Whaticket) + Email

CHECKLIST:
[ ] Segmentar base: clientes con PRE, Nuke, Ofen
[ ] Redactar mensaje para cada sub-segmento
[ ] Brief diseno pieza para cada producto
[ ] Lanzar en Agosto
[ ] Medir respuesta y ventas cruzadas
"@

# =========================================================
# LISTA: Lista de tareas
# =========================================================

New-TrelloCard $L_TAREAS "Disenar flujo de contacto saliente - Base Prospects Edesa" @"
Descripcion: La base Prospects Edesa tiene NIS de empresas con alto consumo electrico.
Es el activo mas diferencial para Hunting T3.

Tareas:
[ ] Exportar y limpiar la base de datos
[ ] Identificar los campos disponibles (NIS, nombre empresa, direccion, rubro)
[ ] Definir criterio de priorizacion (por consumo estimado, por rubro)
[ ] Disenar el mensaje de apertura (WA y LinkedIn) por rubro
[ ] Definir flujo de seguimiento (dia 1, dia 3, dia 7)
[ ] Integrar en NoCRM como pipeline T3
[ ] Asignar responsable comercial
"@

New-TrelloCard $L_TAREAS "Configurar Nuevi para campania F1 Termostatos" @"
Descripcion: Mapear que parte del flujo de F1 (Termostatos Smart) puede automatizar Nuevi.

Tareas:
[ ] Definir el script de conversacion de Nuevi para esta campania
[ ] Configurar respuestas automaticas para preguntas frecuentes
[ ] Definir punto de handoff (cuando pasa a humano)
[ ] Integrar con la base WA de clientes PRE
[ ] Testear el flujo antes del lanzamiento
[ ] Definir KPIs de Nuevi: tasa de respuesta, handoffs generados
"@

New-TrelloCard $L_TAREAS "Subir planilla de Casos de Exito con datos y links RRSS" @"
Descripcion: Tenemos casos documentados con datos reales y logos de empresas reconocidas.

Tareas:
[ ] Compilar todos los casos con: cliente, producto, kW, ahorro mensual estimado, tiempo de repago, foto, link post RRSS
[ ] Agregar logos de empresas clientes (con permiso)
[ ] Subir al workspace compartido
[ ] Definir cuales se usan con nombre y cuales son anonimos
[ ] Crear 3 posts de casos de exito para LinkedIn y 3 para Instagram
"@

New-TrelloCard $L_TAREAS "Reactivar Podcast - Definir cadencia y proximo episodio" @"
Estado: 2 episodios grabados - a reactivar
Cadencia sugerida: 1 episodio/quincena

Formato: caso de cliente real + aprendizaje + consejo accionable (20-30 min)

Distribucion: 1 episodio = 4 piezas de contenido:
- Episodio completo en Spotify/YouTube
- 1 clip para Instagram
- 1 post para LinkedIn
- Mencion en newsletter

Tareas:
[ ] Definir fecha de grabacion del proximo episodio
[ ] Elegir caso/tema del episodio 3
[ ] Preparar guion/estructura
[ ] Grabar y editar
[ ] Subir a Spotify y YouTube
[ ] Generar clips y posts derivados
"@

Write-Host "`n=== TODAS LAS TARJETAS CREADAS ===" -ForegroundColor Cyan
