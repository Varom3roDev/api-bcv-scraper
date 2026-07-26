import os
import re
import requests
import urllib3
from bs4 import BeautifulSoup
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta

# Disable SSL Warnings since we are intentionally ignoring them
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

URL = "https://www.bcv.org.ve/"

month_map = {
    'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
    'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
    'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
}

def obtener_tasa_bcv():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; BCV-Bot/1.0)"
    }

    print("Obteniendo datos del BCV...")
    # verify=False is the key to bypass the UnknownIssuer SSL error
    response = requests.get(URL, headers=headers, timeout=20, verify=False)
    response.raise_for_status()

    # Extract text from HTML
    texto = BeautifulSoup(response.text, "html.parser").get_text(" ", strip=True)

    # 1. Tasa USD
    usd_match = re.search(r"USD\s*([0-9.,]+)", texto)
    # 2. Fecha Valor
    fecha_match = re.search(r"Fecha\s*Valor:\s*([A-Za-zÁÉÍÓÚáéíóúñÑ]+,\s*\d{1,2}\s*[A-Za-záéíóúñÑ]+\s*\d{4})", texto, re.IGNORECASE)

    if not usd_match or not fecha_match:
        raise RuntimeError("No fue posible encontrar la tasa USD o la fecha valor en la página del BCV.")

    tasa_texto = usd_match.group(1)
    tasa_usd = float(tasa_texto.replace(".", "").replace(",", "."))
    
    # "Lunes, 27 Julio 2026"
    fecha_texto = fecha_match.group(1).strip()
    
    # Parse date
    # Split by spaces and commas
    parts = [p.strip() for p in re.split(r'[,\s]+', fecha_texto) if p.strip()]
    # ['Lunes', '27', 'Julio', '2026']
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

def main():
    try:
        data = obtener_tasa_bcv()
        print(f"Tasa extraída: {data['tasa']} (Fecha Valor: {data['fecha_valor_fecha']})")
        
        # Conectar a Supabase
        supabase_url = os.environ.get("SUPABASE_URL")
        supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            print("Variables de entorno SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY no encontradas. Saltando guardado.")
            return

        print("Conectando a Supabase...")
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Upsert
        response = supabase.table("tasas_bcv").upsert(
            {
                "moneda": data["moneda"],
                "tasa": data["tasa"],
                "fecha_valor_texto": data["fecha_valor_texto"],
                "fecha_valor_fecha": data["fecha_valor_fecha"]
            },
            on_conflict="fecha_valor_fecha"
        ).execute()
        
        print("Guardado en base de datos exitoso.")
        
    except Exception as e:
        print(f"Error durante la ejecución: {e}")
        exit(1)

if __name__ == "__main__":
    main()
