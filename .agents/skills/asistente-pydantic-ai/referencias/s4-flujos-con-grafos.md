# S4 · Flujos agénticos con Pydantic Graph

Un agente decide **qué tool** usar. Un **flujo** fija con código **el orden de los pasos**: primero extraer, luego convertir y después confirmar. Se arma como un **grafo**:
- **pasos (nodos):** funciones, con IA o sin ella;
- **aristas:** qué paso va después de cuál;
- **estado:** una cajita que comparten todos los pasos;
- **decisión:** según lo que devolvió un paso, se sigue por una rama u otra.

```python
from pydantic_graph import GraphBuilder, StepContext, TypeExpression
```

## Cadena: un paso tras otro

```python
g = GraphBuilder(input_type=str, output_type=str)

@g.step
async def extraer(ctx: StepContext[None, None, str]) -> Gasto:          # con IA
    return (await extractor.run(ctx.inputs)).output

@g.step
async def convertir(ctx: StepContext[None, None, Gasto]) -> str:        # sin IA: una cuenta es código
    return f"{ctx.inputs.descripcion} = {round(ctx.inputs.monto_bs / 6.96, 2)} USD"

@g.step
async def confirmar(ctx: StepContext[None, None, str]) -> str:
    return (await confirmador.run(ctx.inputs)).output

g.add(
    g.edge_from(g.start_node).to(extraer),
    g.edge_from(extraer).to(convertir),
    g.edge_from(convertir).to(confirmar),
    g.edge_from(confirmar).to(g.end_node),
)
grafo = g.build()                                  # revisa que todo esté conectado
salida = await grafo.run(inputs="Hoy desayuné api con pastel a 20 Bs")
print(grafo.render())                              # el diagrama en Mermaid (mermaid.live)
```

- **`ctx: StepContext[estado, deps, entrada]`.** `ctx.inputs` es lo que devolvió el paso anterior y `ctx.state`, la cajita compartida. Los corchetes son para el editor. El parámetro `ctx` es **obligatorio** y los pasos son **`async def`**.
- **Paso a paso:** `async with grafo.iter(inputs=...) as ejecucion: async for paso in ejecucion: print(paso)`, y al final `ejecucion.output`.

## Router: estado + decisión

```python
class Ruta(BaseModel):
    destino: Literal["clima", "cocina", "charla"]

router = Agent(modelo, output_type=NativeOutput(Ruta),     # JSON directo: más fiable para clasificar
               instructions="Clasifica el pedido, no lo respondas. clima: …; cocina: …; charla: lo demás")

@dataclass
class Consulta:
    pedido: str = ""
    destino: str = ""

g = GraphBuilder(state_type=Consulta, input_type=str, output_type=str)

@g.step
async def clasificar(ctx: StepContext[Consulta, None, str]) -> Literal["clima", "cocina", "charla"]:
    ctx.state.pedido = ctx.inputs
    ctx.state.destino = (await router.run(ctx.inputs)).output.destino
    return ctx.state.destino

@g.step
async def clima(ctx: StepContext[Consulta, None, object]) -> str:   # object: recibe la ruta y no la usa
    return (await meteorologo.run(ctx.state.pedido)).output
# … cocina y charla igual, cada una con su agente especialista y sus tools

g.add(
    g.edge_from(g.start_node).to(clasificar),
    g.edge_from(clasificar).to(
        g.decision()
        .branch(g.match(TypeExpression[Literal["clima"]]).to(clima))
        .branch(g.match(TypeExpression[Literal["cocina"]]).to(cocina))
        .branch(g.match(TypeExpression[Literal["charla"]]).to(charla))
    ),
    g.edge_from(clima, cocina, charla).to(g.end_node),
)
respuesta = await grafo.run(state=Consulta(), inputs="¿Qué lleva el silpancho?")
```

## Un grafo dentro de tu bot

Hay dos formas de usarlo:

1. **Como una tool** del asistente, que la usa cuando hace falta:

```python
@mi_capacidad.tool_plain
async def registrar_con_conversion(texto: str) -> str:
    """Extrae un gasto de un texto libre, lo convierte a dólares y lo confirma."""
    return await grafo.run(inputs=texto)
```

2. **Como el núcleo del bot:** en `asistente.py`, `responder` llama al grafo en vez de al agente.

```python
async def responder(mensaje: str) -> str:
    return await grafo.run(state=Consulta(), inputs=mensaje)
```

## Extras que no vimos en clase

Pydantic Graph también hace pasos en paralelo (`g.join(reduce_dict_update, ...)`), ciclos con un tope en el estado (escritor y revisor) y pasos que esperan la aprobación de una persona. Documentación: <https://pydantic.dev/docs/ai/graph/>.

## Errores típicos

- Un paso con `def` en vez de `async def` pasa `build()`, pero al ejecutar da `TypeError: object … can't be used in 'await' expression`.
- Un paso sin parámetro da `takes 0 positional arguments but 1 was given`.
- `def paso(texto: str)` recibe igualmente el contexto: `'StepContext' object has no attribute 'upper'`. Usa `ctx.inputs`.
- Una rama sin camino a `g.end_node` hace que `build()` dé `GraphValidationError`.
- En un script va **un solo** `asyncio.run(main())` con `await grafo.run(...)` dentro.
