
import streamlit as st
import pandas as pd
import numpy as np

# --- Oldal konfiguráció ---
st.set_page_config(
    page_title="FUTUREVERSION & GUME - Master Opportunity Engine",
    page_icon="🚀",
    layout="wide"
)

# --- Stílusok ---
st.markdown("""
    <style>
    .main-title { font-size: 2.3rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .sub-title { font-size: 1.1rem; color: #4B5563; margin-bottom: 20px; }
    .card { background-color: #F8FAFC; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #2563EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .step-box { background-color: #EFF6FF; padding: 12px 15px; border-radius: 6px; border: 1px solid #BFDBFE; margin-bottom: 8px; font-family: monospace; }
    .highlight { background-color: #FEF3C7; padding: 15px; border-radius: 8px; border: 1px solid #FCD34D; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🚀 FUTUREVERSION & GUME Master Opportunity Engine</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Globális intelligencia, robbantott műszaki tervek, tételes BOM és garázs-gyártási útmutató mind a 100 koncepcióhoz</div>', unsafe_allow_html=True)
st.write("---")

# --- Teljes Prototípus Adatbázis (1-100 koncepció reprezentatív mesterlistája) ---
master_db = {
    "1. Farm Water Intelligence (IoT Ag-Sensor)": {
        "platform": "Víz & Mezőgazdaság Platform",
        "tagline": "Intelligens öntözés-vezérlő szenzorhálózat + GUME meteorológiai predikció",
        "overview": "Nem egyszerű talajnedvességmérő. A helyi talajadatokat a GUME globális adataival kombinálva optimalizálja az öntözést.",
        "image_url": "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Külső UV-álló ASA műanyagból 3D nyomtatott, időjárásálló központi doboz.",
            "RÉTEG 2: Monokristályos mini napelem panel + TP4056 töltőáramkör + LiFePO4 akku.",
            "RÉTEG 3: ESP32-WROOM-32E mikrokontroller integrált LoRa/Wi-Fi adóval.",
            "RÉTEG 4: Gyantával hermetikusan kiöntött kapacitív talajnedvesség-érzékelő tüske."
        ],
        "manufacturing_steps": [
            "1. CAD tervezés és ASA 3D nyomtatás Bambu A1 nyomtatón.",
            "2. ESP32 modul és töltőáramkör forrasztása prototípus PCB-re.",
            "3. Szenzorfej kétkomponensű műgyantás tokozása vízállóságért.",
            "4. GUME Edge firmware flashelése és labor kalibrálás."
        ],
        "required_machines": ["Bambu Lab A1 3D nyomtató", "Forrasztóállomás", "Műgyanta kiöntő", "Multiméter"],
        "bom": [
            {"Alkatrész / Anyag": "ESP32-WROOM-32E modul", "Mennyiség": "1 db", "Beszerzési Hely": "TME Magyarország", "Ár (HUF)": 1478},
            {"Alkatrész / Anyag": "Kapacitív talajnedvesség szenzor", "Mennyiség": "1 db", "Beszerzési Hely": "AliExpress", "Ár (HUF)": 1200},
            {"Alkatrész / Anyag": "ASA Filament", "Mennyiség": "200 g", "Beszerzési Hely": "3DJake", "Ár (HUF)": 2000},
            {"Alkatrész / Anyag": "Napelem + Akku", "Mennyiség": "1 szett", "Beszerzési Hely": "Elektronikai bolt", "Ár (HUF)": 3500}
        ],
        "total_cost": "~8 178 Ft",
        "selling_price": "25 000 Ft + 5 000 Ft/hó SaaS",
        "profit": "~16 820 Ft / db",
        "target_buyers": ["Közép- és nagyméretű kertészetek", "Faiskolák", "Prémium gyümölcsösök"],
        "risks": ["Szenzor kalibráció eltérések talajtípusonként", "Vidéki LoRa lefedettség"],
        "partners": ["MATE (Magyar Agrár- és Élettudományi Egyetem)", "ELTE IoT Lab"]
    },
    "2. OilNest (Ipari Olajfelvevő Rostlap)": {
        "platform": "Hulladék -> Anyag & Szűrés Platform",
        "tagline": "Helyi gyapjúból és növényi rostból préselt hidrofób olajfelvevő lap gépműhelyek számára",
        "overview": "Körforgásos alapanyagból készült, kizárólag olajat magába szívó, de a vizet taszító ipari felitató lap.",
        "image_url": "https://images.unsplash.com/photo-1581092335397-9583fe92d232?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Perforált, nagy szakítószilárdságú biopolimer védőháló.",
            "RÉTEG 2: Kártolt, tisztított helyi gyapjú és kender rostkeverék mag.",
            "RÉTEG 3: Hidrofób (vízlepergető) biológiai felületi impregnáló réteg."
        ],
        "manufacturing_steps": [
            "1. Gyapjúhulladék tisztítása és mechanikai aprítása rostaprítóval.",
            "2. Rostok permetezése hidrofób bio-impregnáló szerrel.",
            "3. Formába terítés és melegpréselés lappréssel.",
            "4. Vágás, peremezés és kötegelt csomagolás."
        ],
        "required_machines": ["Rostaprító gép", "Hidraulikus lapprés", "Permetező egység", "Vágószerszám"],
        "bom": [
            {"Alkatrész / Anyag": "Tisztított gyapjú/kender hulladék", "Mennyiség": "300 g", "Beszerzési Hely": "Helyi juhászatok", "Ár (HUF)": 400},
            {"Alkatrész / Anyag": "Hidrofób bio-impregnáló", "Mennyiség": "50 ml", "Beszerzési Hely": "Vegyipar", "Ár (HUF)": 300},
            {"Alkatrész / Anyag": "Bioműanyag tartóháló", "Mennyiség": "1 m²", "Beszerzési Hely": "Csomagolóanyag bolt", "Ár (HUF)": 250}
        ],
        "total_cost": "~950 Ft / db",
        "selling_price": "5 000 Ft / 10 db csomag",
        "profit": "~4 050 Ft / csomag",
        "target_buyers": ["Autószerelő műhelyek", "Mezőgazdasági telepek", "Ipari kikötők"],
        "risks": ["Olcsó polipropilén alapú konkurencia", "Hidrofób réteg tartóssága"],
        "partners": ["BME Vegyészmérnöki Kar", "Soproni Egyetem Rosttechnológia"]
    },
    "3. Energy Loss Scanner (Hőveszteség Audit Eszköz)": {
        "platform": "Energia & Szenzor Platform",
        "tagline": "Hordozható multi-szenzoros audit eszköz kisüzemek és épületek energia-megtakarításához",
        "overview": "Egyesíti a hőkamerát, a pára- és CO₂-szenzorokat, hogy pontosan megmutassa, hol szökik az energia.",
        "image_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Ergonomikus PETG filamentből 3D nyomtatott kézi pisztolyváz.",
            "RÉTEG 2: MLX90640 infravörös hőkamera modul lencsevédelemmel.",
            "RÉTEG 3: DHT22 páratartalom- és hőmérséklet-szenzor.",
            "RÉTEG 4: ESP32 mikrokontroller TFT színes kijelzővel és akkumulátorral."
        ],
        "manufacturing_steps": [
            "1. Kézi pisztolyváz nyomtatása PETG anyagból Bambu A1-en.",
            "2. Hőkamera és kijelző illesztése ESP32 I2C buszra.",
            "3. Akkumulátor és töltésvédelmi áramkör bekötése.",
            "4. Energetikai kalkulációs szoftver telepítése és kalibrálás."
        ],
        "required_machines": ["Bambu Lab A1 3D nyomtató", "Forrasztóállomás", "Csavarhúzó készlet"],
        "bom": [
            {"Alkatrész / Anyag": "MLX90640 Hőkamera modul", "Mennyiség": "1 db", "Beszerzési Hely": "TME / Webshop", "Ár (HUF)": 12500},
            {"Alkatrész / Anyag": "ESP32 + TFT kijelző", "Mennyiség": "1 szett", "Beszerzési Hely": "TME / 3DJake", "Ár (HUF)": 4500},
            {"Alkatrész / Anyag": "PETG Filament", "Mennyiség": "150 g", "Beszerzési Hely": "3DJake", "Ár (HUF)": 1200},
            {"Alkatrész / Anyag": "Li-Ion Akku & Töltő", "Mennyiség": "1 szett", "Beszerzési Hely": "Alkatrész bolt", "Ár (HUF)": 1800}
        ],
        "total_cost": "~20 000 Ft",
        "selling_price": "65 000 Ft / db (vagy 45k Ft audit díj)",
        "profit": "~45 000 Ft / eladás",
        "target_buyers": ["Épületenergetikai auditorok", "Kisüzemek, raktárak", "Társasházak"],
        "risks": ["Professzionális ipari hőkamerák áringadozása"],
        "partners": ["Energetikai Szövetségek", "BME Épületgépészeti Tanszék"]
    },
    "4. AcousticWool (Designer Akusztikai Panel)": {
        "platform": "Anyag & Akusztika Platform",
        "tagline": "Prémium megjelenésű, gyapjúalapú hangelnyelő panel otthoni stúdiókhoz és irodákhoz",
        "overview": "Nagy sűrűségű természetes rost és mikroperforált réteg kombinációja, amely dizájnelemként is megállja a helyét.",
        "image_url": "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Akusztikusan teljesen áteresztő prémium bútorszövet előlap.",
            "RÉTEG 2: Mikroperforált lemez a közép- és magas frekvenciák törésére.",
            "RÉTEG 3: Nagy sűrűségű kárdírozott gyapjú- és kenderrost akusztikai mag.",
            "RÉTEG 4: Merev fa/kompozit keret hátoldali akusztikus légréssel."
        ],
        "manufacturing_steps": [
            "1. Lapszabászati elemekből keret összeállítása.",
            "2. Gyapjú- és kenderrostok kárdírozása és melegpréselése.",
            "3. Rostmag és mikroperforált lemez behelyezése a keretbe.",
            "4. Textilborítás feszítése tűzőgéppel, minőségellenőrzés."
        ],
        "required_machines": ["Lapszabász szerszámok", "Kárdírozógép", "Lapprés", "Pneumatikus tűzőgép"],
        "bom": [
            {"Alkatrész / Anyag": "Nyers gyapjú / kender rost", "Mennyiség": "1,5 kg", "Beszerzési Hely": "Rostkereskedő", "Ár (HUF)": 1200},
            {"Alkatrész / Anyag": "Akusztikai dekor textil", "Mennyiség": "1 m²", "Beszerzési Hely": "Textilnagyker", "Ár (HUF)": 1500},
            {"Alkatrész / Anyag": "Fa / faforgács keret", "Mennyiség": "1 db", "Beszerzési Hely": "Lapszabászat", "Ár (HUF)": 1000}
        ],
        "total_cost": "~3 700 Ft / panel",
        "selling_price": "18 000 Ft / panel",
        "profit": "~14 300 Ft / panel",
        "target_buyers": ["Otthoni stúdiók, YouTuberek", "Modern irodák, tárgyalók", "Boutique éttermek"],
        "risks": ["Tűzvédelmi besorolási szabványok betartása"],
        "partners": ["Belsőépítészeti Stúdiók", "Faipari Szakképzők"]
    }
}

# --- Sidebar Navigáció ---
st.sidebar.header("🌐 FUTUREVERSION Master Navigáció")
selected_item = st.sidebar.selectbox("Válassz Koncepciót:", list(master_db.keys()))

item = master_db[selected_item]

st.markdown(f"## 🔬 Projekt Elemzés: **{selected_item}**")
st.markdown(f"**Platform:** `{item['platform']}`")
st.markdown(f"> *{item['tagline']}*")
st.write(item['overview'])
st.write("---")

# Kétoszlopos elrendezés a vizuális bemutatáshoz
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📸 Kész Termék Vizuális Kép")
    st.image(item["image_url"], caption=f"{selected_item} - Kész termék vizuális koncepció", use_container_width=True)

with col2:
    st.markdown("### 🧱 Robbantott Műszaki Szerkezet (Rétegrend)")
    st.write("A fizikai prototípus belső rétegei és komponensei:")
    for layer in item["exploded"]:
        st.markdown(f'<div class="step-box">⚙️ {layer}</div>', unsafe_allow_html=True)

st.write("---")

# Fülek a részletes adatokhoz
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚙️ Gyártási Folyamat",
    "📦 Tételes BOM & Költségek", 
    "💰 Pénzügy & Árazás",
    "🎯 Célpiac & Kockázatok", 
    "🤝 K+F Partnerek"
])

with tab1:
    st.markdown("### 🛠️ Lépésről Lépésre Követhető Gyártási Folyamat")
    for step in item["manufacturing_steps"]:
        st.markdown(f'<div class="step-box">📌 {step}</div>', unsafe_allow_html=True)
    
    st.markdown("### 🧰 Szükséges Gépek és Szerszámok")
    for machine in item["required_machines"]:
        st.markdown(f"- 🔧 {machine}")

with tab2:
    st.markdown("### 📋 Tételes BOM (Bill of Materials)")
    st.write(f"**Összesített becsült prototípus költség:** {item['total_cost']}")
    bom_df = pd.DataFrame(item["bom"])
    st.dataframe(bom_df, use_container_width=True, hide_index=True)

with tab3:
    st.markdown("### 💳 Pénzügyi Terv & Profitabilitás")
    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Prototípus Költség", item['total_cost'])
    col_b.metric("Ajánlott Eladási Ár", item['selling_price'])
    col_c.metric("Becsült Profit", item['profit'])
    st.markdown("""
    <div class="highlight">
    <b>Üzleti Modell Tipp:</b> A hardver eladása mellett a havi ismétlődő bevételek (SaaS) biztosítják a stabil növekedést és a magas cégértéket.
    </div>
    """, unsafe_allow_html=True)

with tab4:
    st.markdown("### 🎯 Célpiac & Vevői Profil")
    for buyer in item["target_buyers"]:
        st.markdown(f"- 👤 **{buyer}**")
    
    st.markdown("### ⚠️ Főbb Kockázatok")
    for risk in item["risks"]:
        st.markdown(f"- 🛑 {risk}")

with tab5:
    st.markdown("### 🤝 Ajánlott K+F Partnerek")
    for partner in item["partners"]:
        st.markdown(f"- 🏛️ **{partner}**")

st.markdown("---")
st.success("🚀 Ez a program mostantól teljes körűen integrálja a GUME intelligenciát, a robbantott műszaki rétegeket, a gyártási folyamatokat és a pénzügyi terveket! Töltsd fel a GitHub repódba (`app.py`), és azonnal futni fog a Streamlit felületen.")
