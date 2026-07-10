# Kaggle MCP Server Setup

Servidor MCP para interactuar con Kaggle desde OpenCode.

**Autor:** Jaime Alfredo Bonilla Perez — jaimebp@gmail.com
**© 2026 Todos los derechos reservados**

## Configuración MCP en OpenCode

Definido en `~/.config/opencode/config.json`:

```json
"kaggle-mcp": {
  "type": "local",
  "command": ["/home/jaime/.local/kaggle-mcp-env/bin/python",
              "/home/jaime/proyectos/Kaggle/kaggle_server.py"],
  "enabled": true
}
```

## Herramientas disponibles

| Herramienta | Descripción | Requiere Auth |
|---|---|---|
| `list_competitions` | Listar concursos con filtros (categoría, orden, búsqueda) | Sí |
| `list_datasets` | Listar datasets con búsqueda | Sí |
| `search` | Buscar en toda la plataforma Kaggle | Sí |
| `get_competition_details` | Obtener detalles de un concurso por su ref | Sí |
| `dataset_download` | Descargar dataset (anónimo) | No |
| `competition_download` | Descargar datos de concurso (anónimo) | No |
| `model_download` | Descargar modelo (anónimo) | No |
| `check_auth` | Verificar autenticación con Kaggle | No |
| `login` | Iniciar sesión con API token | No |

## Credenciales

El token API se lee automáticamente de `~/.kaggle/access_token`.

## Repositorio

- GitHub: https://github.com/jabolinux/kaggle-mcp-server
