# S0 · Repaso: IA y Python para agentes

## IA, en cinco ideas

- **Predictiva, generativa y agéntica.** La predictiva clasifica o estima, la generativa produce texto o imágenes y la agéntica **actúa**: decide qué herramienta usar, la usa y sigue.
- **Un LLM predice el siguiente token.** No consulta una base de datos ni tiene reloj. Por eso un agente necesita tools para los datos actuales, como el clima, la inflación o los gastos.
- **Contexto y temperatura.** El contexto es todo lo que el modelo ve en una llamada: instrucciones, mensaje y resultados de tools. Tiene un límite de tokens. La temperatura controla cuánto varía la respuesta.
- **Límites.** Alucina (inventa con seguridad), tiene fecha de corte, cuesta cuota por token y puede obedecer a texto malicioso. Se compensa con tools que devuelven su fuente, con instrucciones como «si no está, dilo» y con mínimo privilegio.
- **Un buen prompt** dice el rol, la tarea, el formato y los límites.

## Python que usa el curso

- **uv** gestiona Python, el entorno y las dependencias:
  - `uv sync` instala lo de `pyproject.toml` y `uv.lock` en `.venv/`;
  - `uv run archivo.py` ejecuta con ese entorno;
  - `uv add paquete` añade una dependencia.
- **Anotaciones de tipo:** `def f(pais: str, anio: int) -> dict:`. Pydantic AI las lee para armar el contrato de cada tool: no son decoración.
- **`dataclass` o `BaseModel`:** una dataclass solo agrupa campos. Un `BaseModel` de Pydantic **valida**: con `monto: float = Field(gt=0)`, un monto negativo se rechaza.

```python
from pydantic import BaseModel, Field
from typing import Literal

class Gasto(BaseModel):
    descripcion: str = Field(min_length=3, description="Qué se gastó")
    monto: float = Field(gt=0, description="Cuánto se gastó")
    categoria: Literal["comida", "transporte", "entretenimiento", "otros"]   # solo estos valores
```

- **pydantic-settings** (`config.py`): una clase `Settings(BaseSettings)` lee el `.env` y valida cada variable con su tipo. `SecretStr` evita imprimir una clave por accidente: se lee con `.get_secret_value()`. Si falta una variable obligatoria, falla al arrancar con un mensaje claro. Una variable del entorno (la terminal, Render) gana a la del `.env`.
- **Decoradores** (`@capability.tool_plain`): una línea encima de una función que la registra en otro objeto. La función sigue siendo normal y la puedes llamar tú para probarla.
- **`if __name__ == "__main__":`** marca el código que corre solo al ejecutar ese archivo, no cuando otro archivo lo importa.
- **Windows:** abre los archivos con `encoding="utf-8"` y usa Git Bash, para que los comandos sean los mismos que en Mac o Linux.
