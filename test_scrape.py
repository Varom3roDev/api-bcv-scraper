import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://www.bcv.org.ve/"

month_map = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

def obtener_tasa_bcv():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "es-US,es;q=0.9,en;q=0.8"
    }

    print("Obteniendo datos del BCV...")
    response = requests.get(URL, headers=headers, timeout=20, verify=False)
    response.raise_for_status()

    texto = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)

    usd_match = re.search(r"USD\s*([0-9.,]+)", texto)
    fecha_match = re.search(r"Fecha\s*Valor:\s*([A-Za-zÁÉÍÓÚáéíóúñÑ]+,\s*\d{1,2}\s*[A-Za-záéíóúñÑ]+\s*\d{4})", texto, re.IGNORECASE)

    if not usd_match or not fecha_match:
        raise RuntimeError("No fue posible encontrar la tasa USD o la fecha valor en la página del BCV.")

    tasa_texto = usd_match.group(1)
    tasa_usd = float(tasa_texto.replace(".", "").replace(",", "."))
    
    fecha_texto = fecha_match.group(1).strip()
    
    parts = [p.strip() for p in re.split(r'[,\s]+', fecha_texto) if p.strip()]
    if len(parts) >= 4:
        day = parts[1].zfill(2)
        month_name = parts[2].lower()
        year = parts[3]
        month = month_map.get(month_name)
        if not month:
            raise ValueError(f"Mes no reconocido: {month_name}")
        fecha_valor_fecha = f"{year}-{month}-{day}"
    else:
        raise ValueError(f"Formato de fecha inesperado: {fecha_texto}")

    return {
        "moneda": "USD",
        "tasa": tasa_usd,
        "fecha_valor_texto": fecha_texto,
        "fecha_valor_fecha": fecha_valor_fecha
    }

data = obtener_tasa_bcv()
print(data)
