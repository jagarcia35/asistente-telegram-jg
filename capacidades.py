"""Las capabilities de tu asistente: lo que vimos en clase. Cámbialas o agrega las tuyas.

Una Capability junta tools + instrucciones en una pieza que se enchufa al agente (asistente.py).
El docstring y los tipos de cada tool son lo único que el modelo lee para decidir cuándo usarla.
"""

import csv
import sqlite3
from datetime import date
from functools import cache
from typing import Literal

import chromadb
import httpx
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pydantic_ai.capabilities import Capability
from pypdf import PdfReader

from config import DATOS, settings


# ═══ S1 · Mi contador: gastos en SQLite, una tool que lee y otra que escribe ══════════

Categoria = Literal["capacitacion", "auditoria"]
CSV = DATOS / "agenda.csv"  # 6 actividades de una agenda de noviembre 2026
DB = DATOS / "agenda.db"  # la base: se crea desde el CSV la primera vez


def crear_base() -> None:
    """Crea agenda.db desde cero con los datos del CSV."""
    DB.unlink(missing_ok=True)
    with CSV.open(encoding="utf-8-sig") as archivo:
        filas = [(g["fecha"], g["categoria"], g["descripcion"], g["empresa"]) for g in csv.DictReader(archivo)]
    conexion = sqlite3.connect(DB)
    with conexion:
        conexion.execute(
            "CREATE TABLE agenda (fecha TEXT, categoria TEXT, descripcion TEXT, empresa TEXT)"
        )
        conexion.executemany("INSERT INTO agenda VALUES (?, ?, ?, ?)", filas)
    conexion.close()


def hoy() -> str:
    """Instrucción dinámica: el modelo no sabe qué día es; se lo decimos en cada mensaje."""
    return f"Hoy es {date.today().isoformat()}."


# Lectura y escritura van en capabilities separadas: a otro agente le podrías dar solo la primera
consulta = Capability(
    id="consulta_agenda",
    description="Consulta agenda personal almacenada en una base de datos SQLite",
    instructions="Usa la base de datos para responder preguntas sobre la agenda. No inventes datos.",
)
registro = Capability(
    id="registro_agenda",
    description="Registra nuevas actividades en la base de datos SQLite",
    instructions=["Agrega nuevas actividades a la base de datos. Asegúrate de que los datos sean válidos.", hoy],
)


@consulta.tool_plain
def consultar_agenda(categoria: Categoria) -> dict:
    """Actividades de una categoría y su empresa."""
    if not DB.exists():
        crear_base()
    conexion = sqlite3.connect(DB.resolve().as_uri() + "?mode=ro", uri=True)  # solo lectura
    conexion.row_factory = sqlite3.Row  # cada fila como diccionario
    filas = conexion.execute(
        "SELECT fecha, descripcion, empresa FROM agenda WHERE categoria = ?",  # SQL fijo; el valor va en ?
        (categoria,),
    ).fetchall()
    conexion.close()
    return {"categoria": categoria, "actividades": [dict(f) for f in filas]}

#return {"categoria": categoria, "total_bs": sum(f["monto"] for f in filas), "gastos": [dict(f) for f in filas]}

@registro.tool_plain
def registrar_agenda(fecha: str, categoria: Categoria, descripcion: str, empresa: str) -> str:
    """Anota una actividad nueva. La fecha va como AAAA-MM-DD ."""
    if not DB.exists():
        crear_base()
    conexion = sqlite3.connect(DB)  # sin mode=ro: esta tool sí escribe
    try:
        with conexion:  # transacción: guarda todo o nada
            conexion.execute("INSERT INTO agenda VALUES (?, ?, ?, ?)", (fecha, categoria, descripcion, empresa))
    except sqlite3.IntegrityError:  # el CHECK de la tabla rechaza montos de 0 o negativos
        return f"No se guardó: la actividad no es válida."
    finally:
        conexion.close()
    return f"Actividad registrado: {descripcion}, {empresa} en {categoria} el {fecha}."


# ═══ S2 · RAG: buscar en mis documentos (PDFs) y citar la fuente ══════════════════════
DOCUMENTOS = DATOS / "documentos"  # PDFs ficticios de finanzas personales


def embeddings_de(textos: list[str]) -> list[list[float]]:
    """Convierte cada texto en un vector: textos de significado parecido dan vectores cercanos."""
    # Gemini también ofrece una API compatible con la de OpenAI; la usamos para los embeddings
    cliente = OpenAI(
        api_key=settings.gemini_api_key_local.get_secret_value(),
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    respuesta = cliente.embeddings.create(model="gemini-embedding-001", input=textos)
    return [item.embedding for item in respuesta.data]


@cache  # se indexa la primera vez que alguien busca, y una sola vez mientras el programa corre
def indice():
    # Base vectorial en memoria (se pierde al terminar); "cosine" mide la cercanía por el ángulo
    coleccion = chromadb.EphemeralClient().get_or_create_collection(
        "documentos", configuration={"hnsw": {"space": "cosine"}}
    )
    for pdf in sorted(DOCUMENTOS.glob("*.pdf")):
        texto = "\n".join(pagina.extract_text() for pagina in PdfReader(pdf).pages)
        # Trozos de ~300 caracteres que se solapan 50, para no cortar una idea por la mitad
        trozos = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50).split_text(texto)
        coleccion.upsert(
            ids=[f"{pdf.stem}-{i}" for i in range(len(trozos))],  # el id dice de qué PDF sale: sirve para citar
            documents=trozos,
            embeddings=embeddings_de(trozos),
        )
    return coleccion


def buscar(pregunta: str, k: int = 3) -> list[dict]:
    """Los k trozos más parecidos a la pregunta, con su fuente y su similitud (1 = idéntico)."""
    r = indice().query(query_embeddings=embeddings_de([pregunta]), n_results=k)
    return [
        {"fuente": fuente, "similitud": round(1 - distancia, 2), "texto": texto}
        for fuente, distancia, texto in zip(r["ids"][0], r["distances"][0], r["documents"][0])
    ]


documentos = Capability(
    id="mis_documentos",
    description="Documentos de finanzas personales: contratos, facturas y garantías",
    # Citar la fuente y admitir cuando no hay datos: así se ve qué sale de los documentos y qué no
    instructions=(
        "Para preguntas sobre pagos, contratos o garantías usa buscar_documentos y cita la fuente "
        "entre corchetes, por ejemplo [contrato_alquiler-1]. "
        "Si no hay información suficiente para responder, di que no lo encuentras, no lo inventes."
    ),
)


@documentos.tool_plain
def buscar_documentos(pregunta: str) -> list[dict]:
    """Busca en los documentos los fragmentos que responden a la pregunta."""
    resultados = buscar(pregunta, k=3)
    for r in resultados:  # en la terminal (o en los Logs de Render) se ve qué recuperó
        print(f"  📄 {r['fuente']} (similitud {r['similitud']})", flush=True)
    return resultados
