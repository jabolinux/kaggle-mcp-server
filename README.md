# Kaggle MCP Server

Servidor MCP (Model Context Protocol) para interactuar con Kaggle desde OpenCode y otros clientes compatibles con MCP.

**Autor:** Jaime Alfredo Bonilla Perez — jaimebp@gmail.com  
**© 2026 Todos los derechos reservados**

## Herramientas disponibles

| Herramienta | Descripción | Auth |
|---|---|---|
| `list_competitions` | Listar concursos de Kaggle con filtros | Sí |
| `list_datasets` | Listar datasets de Kaggle | Sí |
| `search` | Buscar en toda la plataforma | Sí |
| `get_competition_details` | Detalles de un concurso | Sí |
| `dataset_download` | Descargar dataset | No (anónimo) |
| `competition_download` | Descargar datos de concurso | No (anónimo) |
| `model_download` | Descargar modelo | No (anónimo) |
| `check_auth` | Verificar autenticación | No |
| `login` | Autenticarse con API token | No |

## Requisitos

- Python 3.10+
- Kaggle API token (para funciones que requieren auth)

## Instalación

### 1. Clonar e instalar dependencias

```bash
git clone https://github.com/jabolinux/kaggle-mcp-server.git
cd kaggle-mcp-server
python3 -m venv venv
source venv/bin/activate
pip install kagglehub mcp
```

### 2. Configurar credenciales de Kaggle

Obtén tu API token en [Kaggle Settings](https://www.kaggle.com/settings/api) → Create New Token.

**Opción A — Archivo de token (recomendado):**
```bash
echo -n "tu_token_KGAT_..." > ~/.kaggle/access_token
chmod 600 ~/.kaggle/access_token
```

**Opción B — Variable de entorno:**
```bash
export KAGGLE_API_TOKEN=tu_token_KGAT_...
```

**Opción C — Legacy kaggle.json:**
```bash
mkdir -p ~/.kaggle
chmod 700 ~/.kaggle
# Coloca el kaggle.json descargado en ~/.kaggle/kaggle.json
```

### 3. Configurar en OpenCode

Añade al archivo `~/.config/opencode/config.json`:

```json
{
  "mcp": {
    "kaggle-mcp": {
      "type": "local",
      "command": ["/ruta/a/venv/bin/python", "/ruta/a/kaggle_server.py"],
      "enabled": true
    }
  }
}
```

O si usas variable de entorno:

```json
{
  "mcp": {
    "kaggle-mcp": {
      "type": "local",
      "command": ["/ruta/a/venv/bin/python", "/ruta/a/kaggle_server.py"],
      "environment": {
        "KAGGLE_API_TOKEN": "tu_token_KGAT_..."
      },
      "enabled": true
    }
  }
}
```

## Uso

```bash
# Listar concursos destacados
list_competitions category=featured page_size=10

# Buscar datasets
search query="customer churn" document_types=["DATASET"]

# Descargar dataset (sin autenticación)
dataset_download handle="datasnaek/chess"

# Descargar datos de concurso
competition_download competition="titanic"

# Verificar autenticación
check_auth
```

## Estructura

```
kaggle-mcp-server/
├── kaggle_server.py    # Servidor MCP principal
├── README.md
└── .gitignore
```

## Licencia

© 2026 Jaime Alfredo Bonilla Perez. Todos los derechos reservados.
