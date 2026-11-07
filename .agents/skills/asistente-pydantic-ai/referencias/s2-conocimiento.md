# S2 · Conocimiento: la web y tus documentos (RAG)

## Conocimiento externo: darle internet al agente

```python
from pydantic_ai.capabilities import WebFetch, WebSearch
from pydantic_ai.common_tools.tavily import tavily_search_tool
from pydantic_ai.common_tools.web_fetch import web_fetch_tool

leer_pagina = web_fetch_tool(max_content_length=20000)   # recorta para no llenar el contexto

# native=False → la tool corre en tu computadora (o en Render), con cualquier modelo
buscador_tavily = Agent(modelo, capabilities=[
    WebSearch(native=False, local=tavily_search_tool(tavily_api_key, max_results=5)),
    WebFetch(native=False, local=leer_pagina),
])
buscador_duckduckgo = Agent(modelo, capabilities=[
    WebSearch(native=False, local=True),            # DuckDuckGo, sin clave; a veces bloquea
    WebFetch(native=False, local=leer_pagina),
])
# local=False → las tools nativas de Gemini, que corren en los servidores de Google: NO entran en la capa gratis (429)
```

Antes de agregarlo a esta plantilla:
1. Instala los extras: `uv add "pydantic-ai-slim[google,openai,tavily,duckduckgo,web-fetch]==2.59.0"`.
2. Para Tavily, crea una cuenta gratis en app.tavily.com (1000 búsquedas al mes, sin tarjeta).
3. Agrega `tavily_api_key: SecretStr = SecretStr("")` a `Settings`, en `config.py`.
4. Pon la clave en `.env` y en *Environment* de Render.

## Conocimiento interno: RAG con tus PDFs

1. **Leer:** `PdfReader(pdf).pages[i].extract_text()`.
2. **Fragmentar:** `RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)`. Los trozos se solapan para no cortar una idea por la mitad.
3. **Embeddings:** cada trozo se convierte en un vector. Textos de significado parecido dan vectores cercanos: «alquiler» encuentra «canon de arrendamiento», cosa que una búsqueda por palabras no logra.
4. **Indexar en Chroma**, con el id como fuente: `contrato_alquiler-1`.
5. **Buscar:** el embedding de la pregunta trae los k trozos más cercanos (similitud de coseno: 1 = idéntico).
6. **RAG agéntico:** la búsqueda es una **tool**, y las instrucciones piden citar `[fuente]` y decir «no lo encuentro» cuando no está.

```python
cliente = OpenAI(api_key=..., base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

def embeddings_de(textos: list[str]) -> list[list[float]]:
    respuesta = cliente.embeddings.create(model="gemini-embedding-001", input=textos)
    return [item.embedding for item in respuesta.data]

coleccion = chromadb.EphemeralClient().get_or_create_collection("documentos", configuration={"hnsw": {"space": "cosine"}})
coleccion.upsert(ids=[...], documents=trozos, embeddings=embeddings_de(trozos))
r = coleccion.query(query_embeddings=embeddings_de([pregunta]), n_results=3)
# r["ids"][0], r["documents"][0], r["distances"][0]   (similitud = 1 - distancia)
```

En la plantilla (`capacidades.py`):
- `indice()` indexa la **primera vez** que alguien busca y guarda el resultado con `@cache`.
- `buscar()` devuelve los trozos con su fuente.
- `buscar_documentos` es la tool.

**Para personalizar:** cambia los PDFs de `datos/documentos/` por los de tu tema (ficticios). Si quieres usar Markdown o texto, léelos con `archivo.read_text(encoding="utf-8")` en lugar de `PdfReader`. Ajusta `description` e `instructions` de la capability `documentos`.

- El modelo de embeddings por defecto de Chroma (all-MiniLM) está entrenado en inglés y encuentra mal en español: usa `gemini-embedding-001`.
- Cada arranque en Render vuelve a indexar, una llamada de embeddings por PDF. Con muchos PDFs, la primera búsqueda tarda más.

## Extras que no vimos en clase (si quieres ir más allá)

- **Memoria de la conversación.** Para que recuerde lo anterior, pasa `conversation=resultado_anterior.conversation` en el siguiente `run`. Hay que guardarla **por persona** (por número de chat), y en Render Free se pierde al reiniciar. Documentación: <https://pydantic.dev/docs/ai/core-concepts/message-history/>.
