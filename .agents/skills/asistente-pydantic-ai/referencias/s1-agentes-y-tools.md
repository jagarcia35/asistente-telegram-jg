# S1 · Pydantic AI: agente, tools y capabilities

En esta plantilla el modelo viene de `config.py`: `from config import modelo`.

## Un agente = modelo + instrucciones

```python
from pydantic_ai import Agent

mi_agente = Agent(modelo, instructions="Responde en español y en una sola frase")
resultado = mi_agente.run_sync("Ayer me gasté 50 Bs. en un corte de cabello feo")   # en un script
print(resultado.output)
print(resultado.usage)       # tokens de entrada y salida: lo que cuesta cada llamada
```

En el bot, que es async, se usa `await mi_agente.run(...)` (ver `s5-async-y-despliegue.md`).

## Salida tipada

```python
agente_extractor = Agent(modelo, output_type=Gasto, instructions="Extrae el gasto del texto")
gasto = agente_extractor.run_sync("Ayer me gasté 50 Bs. en un corte de cabello feo")
gasto.output                         # un objeto Gasto, ya validado
gasto.output.model_dump_json(indent=4)
```

Si la respuesta no cumple el modelo de Pydantic, Pydantic AI le pide al LLM que la corrija.

## Tools agrupadas en una Capability

```python
from pydantic_ai.capabilities import Capability

apis = Capability(
    id="apis_publicas",
    description="Consulta indicadores económicos (Banco Mundial) y clima (Open Meteo)",
    instructions="Usa las APIs para obtener datos reales. Si una API no tiene el dato, dilo, y no inventes datos",
)

@apis.tool_plain
def inflacion(pais: str, anio: int) -> dict:
    """Inflación anual de un país en un año, según el Banco Mundial.

    Args:
        pais: código ISO del país, por ejemplo 'BO' para Bolivia
        anio: año, por ejemplo 2024
    """
    url = f"https://api.worldbank.org/v2/country/{pais}/indicator/FP.CPI.TOTL.ZG"
    respuesta = httpx.get(url, params={"date": anio, "format": "json"}, timeout=10)
    respuesta.raise_for_status()
    datos = respuesta.json()
    if len(datos) < 2 or not datos[1] or datos[1][0]["value"] is None:
        return {"error": f"No hay datos de inflación para {pais} en {anio}"}   # un aviso, no un raise
    registro = datos[1][0]
    return {"pais": registro["country"]["value"], "anio": registro["date"],
            "inflacion_pct": round(registro["value"], 2), "fuente": "Banco Mundial"}

investigador = Agent(modelo, instructions="Eres un investigador económico", capabilities=[apis])
```

- **El contrato de la tool** es su nombre, su docstring (con `Args:`) y sus tipos: es lo único que lee el modelo para decidir cuándo usarla y con qué argumentos.
- El modelo elige solo los parámetros. La URL y el indicador los fija tu código.
- Devuelve **solo lo útil**, con su `fuente`: así hay menos tokens y el modelo no inventa la cita.
- Si no hay dato, devuelve un aviso (`{"error": ...}`), que el modelo lee y comunica. Un `raise` cortaría la ejecución.
- La tool es una función normal: pruébala sola con `print(inflacion("BO", 2022))`.
- `@x.tool_plain` es una tool sin contexto. Basta para todo lo que vimos en clase.

**Más APIs abiertas sin clave** para personalizar:
- Open-Meteo, para otras ciudades: cambia `latitude` y `longitude`.
- REST Countries: `https://restcountries.com/v3.1/name/{pais}`.
- Wikipedia: `https://es.wikipedia.org/api/rest_v1/page/summary/{titulo}`.
- Frankfurter (tipos de cambio): `https://api.frankfurter.dev/v1/latest?base=USD`.

## Mi contador: leer y escribir en SQLite

```python
Categoria = Literal["transporte", "alimentacion", "educacion", "ocio", "salud"]   # lista cerrada

@consulta.tool_plain
def consultar_gastos(categoria: Categoria) -> dict:
    """Gastos de una categoría y su total en bolivianos."""
    conexion = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)   # SOLO lectura
    conexion.row_factory = sqlite3.Row                                        # filas como diccionario
    filas = conexion.execute(
        "SELECT fecha, descripcion, monto FROM gastos WHERE categoria = ?", (categoria,)   # valores en ?
    ).fetchall()
    conexion.close()
    return {"categoria": categoria, "total_bs": sum(f["monto"] for f in filas), "gastos": [dict(f) for f in filas]}

@registro.tool_plain
def registrar_gasto(fecha: str, categoria: Categoria, descripcion: str, monto: float) -> str:
    """Anota un gasto nuevo. La fecha va como AAAA-MM-DD y el monto en bolivianos."""
    conexion = sqlite3.connect(DB)
    try:
        with conexion:                                   # transacción: guarda todo o nada
            conexion.execute("INSERT INTO gastos VALUES (?, ?, ?, ?)", (fecha, categoria, descripcion, monto))
    except sqlite3.IntegrityError:                       # CHECK (monto > 0) en la tabla
        return f"No se guardó: el monto debe ser mayor que 0 (recibí {monto})."
    finally:
        conexion.close()
    return f"Gasto registrado: {descripcion}, {monto} Bs en {categoria} el {fecha}."
```

- La lectura y la escritura van en **capabilities separadas** (`consulta` y `registro`): a otro agente le podrías dar solo la lectura.
- **Nunca** armes el SQL con lo que manda el modelo (`f"... '{arg}'"`): usa `?`.
- La base también valida con `CHECK`: no confíes solo en el modelo.
- El modelo no sabe qué día es. La plantilla se lo dice con una instrucción dinámica, una función en `instructions=[..., hoy]` que se evalúa en cada mensaje.
- En Render Free el disco se borra al reiniciar: `gastos.db` vuelve a crearse desde `gastos.csv`, y los gastos registrados se pierden. Es un límite conocido.

**Para personalizar:** cambia `gastos.csv` y las categorías por tu tema (libros que lees, entrenamientos, ventas de tu emprendimiento…). Ajusta la tabla en `crear_base()` y los `Literal`.
