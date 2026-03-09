# 📅 Guía: Sincronización de Fechas Trello → Notion

## ✅ Última Ejecución Exitosa

**Fecha**: $(date)  
**Proyectos actualizados**: 50/50  
**Tarjetas Trello consultadas**: 746

---

## 🎯 ¿Qué hace el script?

El script `sync_dates_from_trello.py` sincroniza las fechas de las tarjetas de Trello con los proyectos en Notion.

**Lógica:**
1. Lee todas las tarjetas del tablero "Kanban Nuevas Energías"
2. Busca proyectos en Notion que coincidan con nombres de tarjetas
3. Actualiza:
   - **Fecha Inicio**: `dateLastActivity` de Trello
   - **Fecha Fin Estimada**: Fecha Inicio + 30 días

---

## 🚀 Uso

### Ejecutar manualmente:

```bash
cd c:\Users\Gonza\Desktop\Notion-project
python sync_dates_from_trello.py
```

### Resultado esperado:

```
============================================================
🔄 ACTUALIZANDO FECHAS DESDE TRELLO
============================================================
📋 Obteniendo tarjetas de Trello...
   ✓ 746 tarjetas encontradas
📊 Obteniendo proyectos de Notion...
   ✓ 50 proyectos encontrados

🔄 Procesando proyectos...

[1/50]    ✅ Proyecto X
      📅 Inicio: 2025-12-19
      📅 Fin: 2026-01-18
...

============================================================
✨ PROCESO COMPLETADO
============================================================
   ✅ Actualizados: 50
```

---

## ⚙️ Configuración

### Variables importantes:

- **BOARD_ID**: `612f6ea39c967b8bef5c2186` (Kanban Nuevas Energías)
- **PROYECTOS_DB_ID**: `2e0c81c3-5804-8159-b677-fd8b76761e2f`
- **Estimación de duración**: 30 días por defecto

### Para cambiar la duración estimada:

En la línea 131, modificar:
```python
fecha_fin = (dt + timedelta(days=30)).strftime('%Y-%m-%d')
```

Por ejemplo, para 60 días:
```python
fecha_fin = (dt + timedelta(days=60)).strftime('%Y-%m-%d')
```

---

## 🔄 Automatización (Próximo Paso)

### Opción 1: Windows Task Scheduler

Para que se ejecute automáticamente cada día:

1. Abrir **Task Scheduler** (Programador de tareas)
2. Crear nueva tarea básica
3. Nombre: "Sync Trello Dates"
4. Trigger: Diario a las 8:00 AM
5. Acción: Ejecutar programa
   - Programa: `python`
   - Argumentos: `sync_dates_from_trello.py`
   - Directorio: `c:\Users\Gonza\Desktop\Notion-project`

### Opción 2: Script programado

Crear un archivo `.bat`:

```batch
@echo off
cd c:\Users\Gonza\Desktop\Notion-project
python sync_dates_from_trello.py
pause
```

Guardar como `sync_dates.bat` y ejecutar cuando lo necesites.

---

## 📊 Limitaciones Actuales

1. **Solo procesa primeros 50 proyectos** (1 página de Notion)
2. **No procesa proyectos nuevos automáticamente** (hay que ejecutar manual)
3. **Fechas estimadas**: Usa `dateLastActivity` + 30 días (no due date de Trello)

---

## 🔧 Mejoras Futuras

### Para procesar TODOS los proyectos:

Modificar líneas 48-70 para hacer paginación completa:

```python
while has_more:
    payload = {"page_size": 100}
    if cursor:
        payload["start_cursor"] = cursor
    
    res = requests.post(url, headers=HEADERS_NOTION, json=payload)
    data = res.json()
    all_projects.extend(data.get("results", []))
    has_more = data.get("has_more", False)
    cursor = data.get("next_cursor")
```

### Para usar due date de Trello:

Modificar línea 122 para leer `due` en lugar de calcular:

```python
if trello_card.get('due'):
    fecha_fin = parse_date(trello_card['due'])
```

---

## ✅ Checklist Post-Ejecución

Después de ejecutar, verificar en Notion:

- [ ] Las fechas de inicio son razonables
- [ ] Las fechas de fin están + 30 días después
- [ ] No hay proyectos con fechas faltantes (que estén en Trello)
- [ ] Las fechas viejas (29 dic, 7 ene) fueron reemplazadas

---

## 🐛 Solución de Problemas

**P: Algunos proyectos no se actualizaron**  
R: El nombre en Notion debe coincidir EXACTAMENTE con el nombre en Trello.

**P: "No encontrados en Trello"**  
R: La tarjeta no existe en Trello o tiene nombre diferente.

**P: El script se cuelga**  
R: Revisar conexión a internet. El script hace ~150 llamadas API.

**P: Fechas incorrectas**  
R: Trello usa `dateLastActivity`, no fecha real del proyecto. Considera usar custom fields.

---

## 📝 Notas

- El script es **idempotente**: Se puede ejecutar múltiples veces sin duplicar
- **Rate limiting**: Espera 0.3s entre cada proyecto para no saturar las APIs
- **Timeout**: 10 segundos por llamada API
