
import streamlit as st
import pandas as pd
import numpy as np

# --- Oldal konfiguráció ---
st.set_page_config(
    page_title="FUTUREVERSION & GUME - Prototípus & Piaci Intelligencia Motor",
    page_icon="⚙️",
    layout="wide"
)

# --- Stílusok ---
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .sub-title { font-size: 1.1rem; color: #4B5563; margin-bottom: 20px; }
    .card { background-color: #F8FAFC; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #2563EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .bom-table { width: 100%; border-collapse: collapse; }
    .highlight { background-color: #EFF6FF; padding: 15px; border-radius: 8px; border: 1px solid #BFDBFE; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚙️ FUTUREVERSION Garázs Labor & Piaci Intelligencia Motor</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Robbantott műszaki tervek, tételes BOM, célcsoport-elemzés és konkurens-analízis a GUME top prototípusaihoz</div>', unsafe_allow_html=True)
st.write("---")

# --- Prototípus Adatbázis ---
prototypes = {
    "1. Farm Water Intelligence (IoT & Ag-SaaS)": {
        "tagline": "Intelligens öntözés-vezérlő szenzorhálózat + GUME meteorológiai predikció",
        "overview": "Nem egyszerű talajnedvességmérő. Az eszköz a helyi talajadatokat a GUME globális időjárási és párolgási adataival kombinálva kiszámolja, hogy mikor és mennyi vizet kell kijuttatni.",
        "exploded": [
            "1. Külső UV-álló időjárásálló ház (ASA filament, 3D nyomtatva - Bambu A1)",
            "2. Napelemes tápegység + LiFePO4 akkumulátor modul",
            "3. ESP32-WROOM-32E mikrokontroller & LoRa/Wi-Fi modul",
            "4. Kapacitív talajnedvesség- és hőmérséklet-szenzor szúrótüske",
            "5. Opcionális motoros szelep vezérlő relé kimenet"
        ],
        "bom": [
            {"Alkatrész / Anyag": "ESP32-WROOM-32E modul", "Mennyiség": "1 db", "Beszerzési Hely": "TME Magyarország", "Becsült Ár (HUF)": 1478},
            {"Alkatrész / Anyag": "Kapacitív talajnedvesség szenzor", "Mennyiség": "1 db", "Beszerzési Hely": "AliExpress / hazai elektronika", "Becsült Ár (HUF)": 1200},
            {"Alkatrész / Anyag": "ASA Filament (ház nyomtatáshoz)", "Mennyiség": "200 g", "Beszerzési Hely": "3DJake Magyarország", "Becsült Ár (HUF)": 2000},
            {"Alkatrész / Anyag": "Kis napelem panel + akku", "Mennyiség": "1 szett", "Beszerzési Hely": "Elektronikai szaküzlet", "Becsült Ár (HUF)": 3500},
            {"Alkatrész / Anyag": "Apró alkatrészek, kábelek, PCB", "Mennyiség": "1 csomag", "Beszerzési Hely": "Helyi bolt / TME", "Becsült Ár (HUF)": 1500}
        ],
        "total_cost": "~9 678 Ft",
        "target_buyers": [
            "Közép- és nagy méretű kertészetek, faiskolák",
            "Prémium gyümölcsösök és szőlészetek",
            "Városi parkfenntartó önkormányzatok"
        ],
        "competitors": [
            {"Konkurens": "Rain Bird / Hunter (hagyományos időzítők)", "Eszközkészlet": "Fizikai időalapú szelepek, nincs AI döntés", "Gyengeségük": "Elpazarolják a vizet eső előtt is."},
            {"Konkurens": "CropX / Netafim (ipari rendszerek)", "Eszközkészlet": "Drága, nagyméretű szenzorhálózatok ($1000+)", "Gyengeségük": "Kisgazdaságok számára megfizethetetlenül drágák."}
        ]
    },
    "2. OilNest (Olaj- és Folyadékfelvevő Rost)": {
        "tagline": "Helyi gyapjúból és növényi rostból préselt hidrofób olajfelvevő lap gépműhelyek számára",
        "overview": "Körforgásos alapanyagból készült, kizárólag olajat és szénhidrogén alapú folyadékokat magába szívó, de a vizet taszító ipari párna/lap.",
        "exploded": [
            "1. Perforált védő külső háló (bioműanyag vagy tartós háló)",
            "2. Magas olajfelvevő képességű tisztított gyapjú / kender rostmag",
            "3. Hidrofób (vízlepergető) felületi biológiai impregnáló réteg",
            "4. Peremezett, összefogott zárás"
        ],
        "bom": [
            {"Alkatrész / Anyag": "Tisztított gyapjú / kender hulladék", "Mennyiség": "300 g", "Beszerzési Hely": "Helyi gyapjútermelők / textilmaradék", "Becsült Ár (HUF)": 400},
            {"Alkatrész / Anyag": "Hidrofób impregnáló bio-szer", "Mennyiség": "50 ml", "Beszerzési Hely": "Vegyipari forgalmazó", "Becsült Ár (HUF)": 300},
            {"Alkatrész / Anyag": "Külső tartóháló", "Mennyiség": "1 m²", "Beszerzési Hely": "Textilnagykereskedés", "Becsült Ár (HUF)": 250}
        ],
        "total_cost": "~950 Ft / db",
        "target_buyers": [
            "Autószerelő műhelyek, gépjármű-szervizek",
            "Mezőgazdasági telepek (traktor karbantartás)",
            "Ipari gyárak hidraulikus részlegei, kikötők"
        ],
        "competitors": [
            {"Konkurens": "3M Oil Absorbent Pads (műanyagszál alapú)", "Eszközkészlet": "Polipropilén alapú, fosszilis eredetű felitatók", "Gyengeségük": "Nem megújuló anyagból vannak, környezetszennyező a hulladékkezelésük."}
        ]
    },
    "3. Energy Loss Scanner (Hőveszteség Audit Szett)": {
        "tagline": "Hordozható multi-szenzoros audit eszköz kisüzemek, raktárak és épületek energia-megtakarításához",
        "overview": "Egyesíti a hőkamerát, a pára-, CO₂- és hőmérséklet-szenzorokat, hogy pontosan megmondja az épület tulajdonosának, hol szökik a pénze.",
        "exploded": [
            "1. Ergonomikus kézi pisztolyváz (3D nyomtatott - Bambu A1)",
            "2. MLX90640 hőkamera szenzor modul",
            "3. DHT22 pára- és hőmérséklet-szenzor",
            "4. ESP32 mikrokontroller + OLED / TFT színes kijelző",
            "5. Újratölthető Li-Ion akkumulátor egység"
        ],
        "bom": [
            {"Alkatrész / Anyag": "MLX90640 Hőkamera modul", "Mennyiség": "1 db", "Beszerzési Hely": "Elektronikai webshop / TME", "Becsült Ár (HUF)": 12500},
            {"Alkatrész / Anyag": "ESP32 mikrokontroller + TFT kijelző", "Mennyiség": "1 szett", "Beszerzési HUF": "TME / 3DJake", "Becsült Ár (HUF)": 4500},
            {"Alkatrész / Anyag": "PETG Filament a vázhoz", "Mennyiség": "150 g", "Beszerzési Hely": "3DJake Magyarország", "Becsült Ár (HUF)": 1200},
            {"Alkatrész / Anyag": "Akkumulátor és töltő áramkör", "Mennyiség": "1 szett", "Beszerzési Hely": "Elektronikai alkatrészbolt", "Becsült Ár (HUF)": 1800}
        ],
        "total_cost": "~20 000 Ft",
        "target_buyers": [
            "Épületenergetikai auditorok, kivitelezők",
            "Kisüzemek, logisztikai raktárak, autószervizek tulajdonosai",
            "Társasházi közös képviselők"
        ],
        "competitors": [
            {"Konkurens": "Flir / Testo professzionális hőkamerák", "Eszközkészlet": "Önálló hőkamerák ($400 - $1500)", "Gyengeségük": "Drágák, és csak hőt mutatnak, nem számolnak energiamegtakarítási megtérülést."}
        ]
    },
    "4. AcousticWool (Designer Akusztikai Panel)": {
        "tagline": "Prémium megjelenésű, gyapjúalapú hangelnyelő panel otthoni stúdiókhoz és irodákhoz",
        "overview": "Nem olcsó szivacs, hanem magas sűrűségű természetes rost és mikroperforált réteg kombinációja, amely dizájnelemként is megállja a helyét.",
        "exploded": [
            "1. Dekoratív, akusztikusan áteresztő külső textil borítás",
            "2. Mikroperforált elülső hangtörő réteg",
            "3. Nagy sűrűségű kárdírozott gyapjú/kender akusztikai mag",
            "4. Légrés a hátoldalon a mélyebb frekvenciák elnyeléséhez",
            "5. Merev hátfal és fali rögzítő konzol"
        ],
        "bom": [
            {"Alkatrész / Anyag": "Nyers gyapjú / kender rost", "Mennyiség": "1,5 kg", "Beszerzési Hely": "Helyi rostkereskedő", "Becsült Ár (HUF)": 1200},
            {"Alkatrész / Anyag": "Dekoratív akusztikai textil", "Mennyiség": "1 m²", "Beszerzési Hely": "Textilnagykereskedés", "Becsült Ár (HUF)": 1500},
            {"Alkatrész / Anyag": "Fa / faforgács keret", "Mennyiség": "1 db", "Beszerzési Hely": "Asztalosműhely / lapszabászat", "Becsült Ár (HUF)": 1000}
        ],
        "total_cost": "~3 700 Ft / panel",
        "target_buyers": [
            "Otthoni hangstúdiók, podcast készítők, YouTuberek",
            "Modern irodák, tárgyalók, coworking irodák",
            "Boutique éttermek, kávézók (visszhang csökkentésére)"
        ],
        "competitors": [
            {"Konkurens": "Auralex / szivacsalapú akusztikai elemek", "Eszközkészlet": "Poliuretán hab piramisok", "Gyengeségük": "Porladnak idővel, csúnyák, tűzveszélyesek, és csak a magas hangokat szűrik."}
        ]
    }
}

# --- Felület Navigáció ---
selected_proj = st.sidebar.selectbox("Válassz Prototípust az Elemzéshez:", list(prototypes.keys()))
p_data = prototypes[selected_proj]

st.markdown(f"## 🔬 Projekt Elemzés: **{selected_proj}**")
st.markdown(f"> *{p_data['tagline']}*")
st.write(p_data['overview'])
st.write("---")

# Fülek a részletes adatokhoz
tab1, tab2, tab3, tab4 = st.tabs([
    "🛠️ Robbantott Szerkezet", 
    "📦 Tételes BOM & Költségek", 
    "🎯 Célpiac & Első Vevők", 
    "⚔️ Konkurencia Elemzés"
])

with tab1:
    st.markdown("### 🧱 Robbantott Műszaki Szerkezet (Rétegrend)")
    st.write("A prototípus fizikai felépítése alulról felfelé / kívülről befelé:")
    for layer in p_data["exploded"]:
        st.markdown(f"- ✅ {layer}")
    
    st.markdown("""
    <div class="highlight">
    <b>Garázs Gyártási Tipp:</b> Az első prototípusok 3D nyomtatott házzal (Bambu A1, PETG vagy ASA anyagból) és kézi összeszereléssel készülnek. A végleges sorozatgyártásnál átállhatunk fröccsöntésre.
    </div>
    """, unsafe_allow_html=True)

with tab2:
    st.markdown("### 📋 Tételes BOM (Bill of Materials) - Prototípus Szint")
    st.write(f"**Összesített becsült prototípus anyagköltség:** {p_data['total_cost']}")
    
    bom_df = pd.DataFrame(p_data["bom"])
    st.dataframe(bom_df, use_container_width=True, hide_index=True)
    
    st.markdown("""
    *Megjegyzés: Az árak nettó beszerzési árak magyarországi és európai beszállítóktól (pl. TME, 3DJake, AliExpress) kis tételes (1 db-os prototípus) megrendelés esetén.*
    """)

with tab3:
    st.markdown("### 🎯 Ki veszi meg? (Célpiac & Vevői Profil)")
    st.write("A GUME által azonosított elsődleges fizető vevők és szegmensek:")
    for buyer in p_data["target_buyers"]:
        st.markdown(f"- 👤 **{buyer}**")

    st.markdown("""
    <div class="highlight">
    <b>Értékajánlat (Value Proposition):</b> Nem magát az eszközt adjuk el, hanem a problémából fakadó megtakarítást (pl. megspórolt víz, elkerült termésveszteség, olcsóbb energiafelhasználás).
    </div>
    """, unsafe_allow_html=True)

with tab4:
    st.markdown("### ⚔️ Piaci Konkurencia & Versenytársak Eszközei")
    for comp in p_data["competitors"]:
        st.markdown(f"""
        <div class="card">
            <h4>🏢 Konkurens: <b>{comp['Konkurens']}</b></h4>
            <p><b>Használt eszközök / technológia:</b> {comp['Eszközkészlet']}</p>
            <p><b>Fő gyengeségük / Rés a piacon:</b> <span style="color: #DC2626;">{comp['Gyengeségük']}</span></p>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")
st.success("🚀 Ez a modul azonnal használható a GitHub repóba feltöltve a Streamlit felületén! Válassz másik projektet a bal oldali sávból a részletek megtekintéséhez.")
