import streamlit as st
import pandas as pd
import math
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide", page_title="Local StatsHunters ČR")

st.title("MyMap")

# --- 1. MATEMATICKÉ FUNKCIE PRE DLAŽDICE ---
def tile_edges(x, y, zoom=14):
    n = 2.0 ** zoom
    lon1 = x / n * 360.0 - 180.0
    lat1_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat1 = math.degrees(lat1_rad)
    lon2 = (x + 1) / n * 360.0 - 180.0
    lat2_rad = math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n)))
    lat2 = math.degrees(lat2_rad)
    return lat1, lon1, lat2, lon2

def zisti_kraj(x, y):
    # Rýchly a presný matematický orez pre kraje v ČR na zoome 14
    # Súradnice preklopené na hrubé zóny krajov
    lat, lon, _, _ = tile_edges(x, y)
    
    if 49.0 <= lat <= 49.3 and 16.2 <= lon <= 16.9:
        return "Jihomoravský kraj", 3420
    elif 49.9 <= lat <= 50.2 and 14.2 <= lon <= 14.7:
        return "Hlavní město Praha", 145
    elif 49.8 <= lat <= 50.3 and 13.9 <= lon <= 15.3:
        return "Středočeský kraj", 5210
    elif 50.1 <= lat <= 50.5 and 15.2 <= lon <= 16.5:
        return "Královéhradecký kraj", 2310
    else:
        return "Ostatné kraje / Pohraničie", 15000

# --- 2. NAČÍTANIE TVOJICH DÁT Z GOOGLE DRIVE ---

GOOGLE_DRIVE_FILE_ID = "1dEzLAxhkrfR8yZ2BI_bgCsaWibG-gnl5"
url = f"https://docs.google.com/uc?export=download&id={GOOGLE_DRIVE_FILE_ID}"

@st.cache_data(ttl=600)
def load_data_from_drive():
    try:
        return pd.read_csv(url)
    except Exception as e:
        st.error(f"Chyba pri načítaní dát z Google Drive: {e}")
        return pd.read_csv("navstivene_dlazdice.csv")

# 1. Stiahneme čisté dáta (obsahujú len xtile, ytile)
df = load_data_from_drive()

# 2. DOPLNENIE: Prepočítame a pridáme stĺpce 'Kraj' a 'Celkovo_Kraj' pre stiahnuté dáta
kraje = []
celkovo_limity = []

for _, row in df.iterrows():
    kraj, celkovo = zisti_kraj(row['xtile'], row['ytile'])
    kraje.append(kraj)
    celkovo_limity.append(celkovo)

df['Kraj'] = kraje
df['Celkovo_Kraj'] = celkovo_limity

# --- 3. TVORBA STRÁNKY (LAYOUT) ---
col1, col2 = st.columns([1, 3])

with col1:
    st.header("Stats")
    
    # Výpočet percent pre každý kraj
    stats = df.groupby(['Kraj', 'Celkovo_Kraj']).size().reset_index(name='Navštívené')
    stats['Pokrytie'] = (stats['Navštívené'] / stats['Celkovo_Kraj'] * 100).round(2)
    
    for _, r in stats.iterrows():
        st.metric(label=f"{r['Kraj']}", value=f"{r['Pokrytie']}%", delta=f"{r['Navštívené']} / {r['Celkovo_Kraj']} tiles")

with col2:
    st.header("Map")
    if not df.empty:
        stred_lat, stred_lon, _, _ = tile_edges(df.iloc[0]['xtile'], df.iloc[0]['ytile'])
        m = folium.Map(location=[stred_lat, stred_lon], zoom_start=11, tiles="OpenStreetMap")
        
        for _, row in df.iterrows():
            lat1, lon1, lat2, lon2 = tile_edges(row['xtile'], row['ytile'])
            folium.Rectangle(
                bounds=[[lat2, lon1], [lat1, lon2]],
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.4,
                weight=1
            ).add_to(m)
            
        st_folium(m, width=800, height=600)
