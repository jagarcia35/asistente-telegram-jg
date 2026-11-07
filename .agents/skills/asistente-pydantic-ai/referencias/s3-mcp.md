# S3 · Interoperabilidad y MCP

**MCP (Model Context Protocol)** es un estándar para que un programa (el **servidor**) ofrezca tools a cualquier agente o app (el **cliente**): Pydantic AI, Claude, ChatGPT, VS Code… El servidor **anuncia** sus tools (`tools/list`) y el cliente las llama (`tools/call`).

Para usarlo en esta plantilla, añade el extra: `uv add "pydantic-ai-slim[google,openai,mcp]==2.59.0"`. Trae el cliente (`fastmcp`) y el SDK oficial (`mcp`).

## Usar un servidor ya hecho (stdio)

```python
from fastmcp.client.transports import StdioTransport
from pydantic_ai.capabilities import MCP

# stdio = «lanza este programa y háblale por su entrada y salida estándar»
hora = MCP(local=StdioTransport(command="uvx", args=["mcp-server-time", "--local-timezone=America/La_Paz"]))
asistente = Agent(modelo, capabilities=[hora])
```

No escribes ninguna tool: el agente las descubre al conectarse.

## Tu propio servidor, con las tools del contador

```python
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

servidor = MCPServer("Contador Alex")
servidor.add_tool(consultar_gastos)       # funciones que ya tenías, sin cambiarlas
servidor.add_tool(registrar_gasto)

@servidor.tool()
def gastos_del_dia(fecha: str) -> dict:
    """Gastos del día a partir de una fecha en formato AAAA-MM-DD"""
    try:
        date.fromisoformat(fecha)
    except ValueError:
        raise ToolError(f"Fecha inválida: {fecha}. Debe ser AAAA-MM-DD")   # este mensaje SÍ llega al modelo
    ...

def lanzar_servidor() -> StdioTransport:   # el mismo archivo, con --servidor
    return StdioTransport(command=sys.executable, args=[__file__, "--servidor"])

if __name__ == "__main__":
    if "--servidor" in sys.argv:
        servidor.run()                     # stdio: aquí no se imprime nada
    else:
        contador = Agent(modelo, capabilities=[MCP(local=lanzar_servidor())])
        print(contador.run_sync("¿Qué gastos tengo en alimentación?").output)
```

Para probar sin modelo: `async with Client(lanzar_servidor()) as c: await c.list_tools()`.

- `MCP(local="servidor.py")` **falla**: ese argumento solo acepta una URL. Usa `StdioTransport`.
- Solo `ToolError` deja pasar su mensaje. Un `ValueError` se enmascara («Error executing tool»).
- `MCP(local=..., allowed_tools=["consultar_gastos"])` hace que el modelo **ni vea** las tools que escriben (mínimo privilegio).

## Un servidor por HTTP: el muro de la clase

```python
servidor.run(transport="streamable-http", host="0.0.0.0", port=8000, stateless_http=True)
```

- Para conectarte, usa `MCP("http://127.0.0.1:8000/mcp")`, o la URL del túnel terminada en `/mcp`.
- Con `host="127.0.0.1"`, el SDK responde **421** a dominios ajenos: detrás de un túnel o de Render, usa `0.0.0.0`.
- Para abrirlo a internet desde tu equipo: `cloudflared tunnel --url http://localhost:8000`.
- Cualquiera con la URL puede llamar a las tools. Acota lo que llega (por ejemplo, máximo 140 caracteres) y no expongas tools peligrosas.

**MCP dentro del bot en Render:** un servidor por HTTP ya publicado se usa con `MCP("https://…/mcp")` en `capabilities`. Uno por stdio con `uvx` también funciona, porque Render tiene uv, pero se lanza en cada mensaje y tarda más.

**Cuidado con lo que lee el agente:** un texto externo (una web, un documento, un mensaje del muro) puede traer órdenes escondidas, lo que se llama inyección indirecta. Trátalo como dato, no como orden. Y no le des al mismo agente tools que lean contenido externo y tools que hagan algo delicado.
