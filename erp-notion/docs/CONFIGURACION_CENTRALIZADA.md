# 🚀 Configuración Centralizada - Sistema Notion ERP

## ✅ ¡Listo! Tu proyecto ahora tiene configuración centralizada

### 📁 Archivos Creados:

```
config/
├── settings.py          # Configuración centralizada
└── .env.example         # Plantilla de variables de entorno

requirements.txt         # Dependencias del proyecto
```

### 🔧 Cambios Realizados:

1. **55 scripts actualizados** automáticamente para usar configuración centralizada
2. **Tokens centralizados** en `config/settings.py`
3. **Manejo de errores** para configuración faltante
4. **Validación automática** de configuración

### 🚀 Próximos Pasos:

#### 1. Instalar Dependencias:
```bash
pip install -r requirements.txt
```

#### 2. Configurar Variables de Entorno:
```bash
# Copiar plantilla
cp .env.example .env

# Editar con tus tokens reales
notepad .env
```

#### 3. Validar Configuración:
```bash
python config/settings.py
```

#### 4. Probar Scripts:
```bash
# Script principal con nueva configuración
python src/automation/auto_generate_accounts.py
```

### 💡 Beneficios:

- ✅ **Sin repetición**: Tokens en un solo lugar
- ✅ **Seguridad**: Variables de entorno
- ✅ **Validación**: Detecta configuración faltante  
- ✅ **Mantenimiento**: Cambios en un solo archivo
- ✅ **Escalabilidad**: Fácil agregar nueva configuración

### 🎯 Archivos Principales Actualizados:

- `src/notion/*.py` - 47 scripts de Notion
- `src/trello/*.py` - 6 scripts de Trello  
- `src/automation/*.py` - Scripts de automatización
- `src/utils/*.py` - Utilidades compartidas

### 🔄 Para Actualizar Tokens:

Ahora solo edita `.env` o `config/settings.py` y todos los scripts usarán la nueva configuración automáticamente.

---

*¡Configuración centralizada implementada con éxito!* 🎉