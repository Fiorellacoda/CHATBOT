from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import spacy
from typing import List, Optional
import uvicorn

nlp = spacy.load("es_core_news_md")

productos_df = pd.read_csv('GG.csv')
guia_talles_df = pd.read_excel('4EW.xlsx')

app = FastAPI()

class UserRequest(BaseModel):
    mensaje: str
    talla: Optional[str] = None

def procesar_preferencia(texto_usuario: str):
    doc = nlp(texto_usuario.lower())

    colores = [
        "rojo", "azul", "verde", "negro", "blanco", "amarillo", "rosa", "naranja", "morado", 
        "gris", "turquesa", "violeta", "beige", "lila", "lavanda", "celeste", "rosa fucsia", "dorado", "plateado"
    ]
    
    estilos = [
        "casual", "elegante", "preppy", "coctel", "street", "noche", "playa", "formal", "sofisticado", 
        "deportivo", "chic", "vintage", "moderno", "minimalista", "bohemio", "romántico", "punk", "rockero"
    ]

    precios = []
    if "barato" in texto_usuario:
        precios = [0, 25000]
    elif "normal" in texto_usuario:
        precios = [25001, 60000]
    elif "caro" in texto_usuario:
        precios = [60001, 2000000]
    elif "d" in texto_usuario:
        precios = [0, 25000]
    elif "c" in texto_usuario:
        precios = [25001, 40000]
    elif "b" in texto_usuario:
        precios = [40001, 60000]
    elif "a" in texto_usuario:
        precios = [60001, 2000000]

    preferencias = {
        "colores": [color for color in colores if color in texto_usuario.lower()],
        "estilos": [estilo for estilo in estilos if estilo in texto_usuario.lower()],
        "precios": precios
    }

    return preferencias

def recomendar_productos(preferencias):
    recomendaciones = productos_df

    if preferencias["colores"]:
        recomendaciones = recomendaciones[recomendaciones['Color'].str.lower().isin(preferencias["colores"])]

    if preferencias["estilos"]:
        recomendaciones = recomendaciones[recomendaciones['Estilo'].str.lower().isin(preferencias["estilos"])]
    
    if preferencias["precios"]:
        min_precio, max_precio = preferencias["precios"]
        recomendaciones = recomendaciones[(recomendaciones['Precio'] >= min_precio) & (recomendaciones['Precio'] <= max_precio)]

    if len(recomendaciones) < 5:
        colores_similares = preferencias["colores"] or recomendaciones['Color'].unique().tolist()
        estilos_similares = preferencias["estilos"] or recomendaciones['Estilo'].unique().tolist()
        
        recomendaciones_similares = productos_df[
            productos_df['Color'].str.lower().isin(colores_similares) |
            productos_df['Estilo'].str.lower().isin(estilos_similares)
        ]
        
        recomendaciones = recomendaciones_similares.head(5)

    return recomendaciones

def recomendar_talla(talla_usuario):
    talla_recomendada = guia_talles_df[guia_talles_df['Talla'].str.lower() == talla_usuario.lower()]
    return talla_recomendada

def generar_respuesta_amigable(productos_recomendados, talla_recomendada):
    if productos_recomendados.empty:
        return {
            "mensaje": "¡Ups! No encontramos productos que coincidan exactamente con tu búsqueda. Aquí tienes algunas recomendaciones similares:",
            "productos_recomendados": [],
            "talla_recomendada": talla_recomendada
        }

    respuesta = {
        "mensaje": "¡La opción perfecta para ti es...",
        "productos_recomendados": productos_recomendados.to_dict(orient='records'),
        "talla_recomendada": talla_recomendada.to_dict(orient='records') if talla_recomendada is not None else None
    }

    return respuesta

@app.post("/chatbot/")
async def chatbot(request: UserRequest):
    preferencias = procesar_preferencia(request.mensaje)

    productos_recomendados = recomendar_productos(preferencias)
    
    talla_recomendada = None
    if request.talla:
        talla_recomendada = recomendar_talla(request.talla)

    respuesta = generar_respuesta_amigable(productos_recomendados, talla_recomendada)

    return respuesta

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
