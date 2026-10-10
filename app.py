import streamlit as st
import pandas as pd
import numpy as np

# --- Oldal konfiguráció ---
st.set_page_config(
    page_title="FUTUREVERSION & GUME - Prototípus & Gyártási Labor",
    page_icon="⚙️",
    layout="wide"
)

# --- Stílusok ---
st.markdown("""
    <style>
    .main-title { font-size: 2.2rem; font-weight: bold; color: #1E3A8A; margin-bottom: 0px; }
    .sub-title { font-size: 1.1rem; color: #4B5563; margin-bottom: 20px; }
    .card { background-color: #F8FAFC; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #2563EB; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .step-box { background-color: #EFF6FF; padding: 12px 15px; border-radius: 6px; border: 1px solid #BFDBFE; margin-bottom: 8px; }
    .highlight { background-color: #FEF3C7; padding: 15px; border-radius: 8px; border: 1px solid #FCD34D; margin-top: 10px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">⚙️ FUTUREVERSION Garázs Labor & Gyártási Útmutató</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Robbantott műszaki tervek, lépésről lépésre követhető gyártási folyamatok, BOM és piaci elemzés</div>', unsafe_allow_html=True)
st.write("---")

# --- Prototípus Adatbázis Gyártási Folyamatokkal és Műszaki Adatokkal ---
prototypes = {
    "1. Farm Water Intelligence (IoT & Ag-SaaS)": {
        "tagline": "Intelligens öntözés-vezérlő szenzorhálózat + GUME meteorológiai predikció",
        "overview": "Nem egyszerű talajnedvességmérő. Az eszköz a helyi talajadatokat a GUME globális időjárási és párolgási adataival kombinálva kiszámolja, hogy mikor és mennyi vizet kell kijuttatni.",
        "image_url": "https://images.unsplash.com/photo-1586771107445-d3ca888129ff?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Külső UV-álló időjárásálló ház (ASA filament, 3D nyomtatva - Bambu A1)",
            "RÉTEG 2: Napelemes tápegység + LiFePO4 akkumulátor modul",
            "RÉTEG 3: ESP32-WROOM-32E mikrokontroller & LoRa/Wi-Fi adómodul",
            "RÉTEG 4: Kapacitív talajnedvesség- és hőmérséklet-szenzor szúrótüske",
            "RÉTEG 5: Opcionális motoros szelep vezérlő relé kimenet"
        ],
        "manufacturing_steps": [
            "1. Ház megtervezése CAD-ben és nyomtatása Bambu A1 3D nyomtatón (ASA filament, idojárásálló).",
            "2. ESP32 modul és a szenzorok kábelezése, forrasztása a prototípus panelre.",
            "3. Vízálló műgyanta kiöntés biztosítása az elektronikai csatlakozásoknál.",
            "4. GUME IoT firmware (Edge kliens) flashelése a mikrokontrollerre.",
            "5. Kalibrálás laboratóriumi körülmények között ismert nedvességtartalmú talajban."
        ],
        "required_machines": [
            "Bambu Lab A1 3D nyomtató",
            "Forrasztóállomás és multiméter",
            "Műgyanta kiöntő szett",
            "Programozó kábelek / tesztpad"
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
        "image_url": "https://images.unsplash.com/photo-1581092335397-9583fe92d232?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Perforált védő külső háló (bioműanyag vagy tartós háló)",
            "RÉTEG 2: Magas olajfelvevő képességű tisztított gyapjú / kender rostmag",
            "RÉTEG 3: Hidrofób (vízlepergető) felületi biológiai impregnáló réteg",
            "RÉTEG 4: Peremezett, összefogott zárás"
        ],
        "manufacturing_steps": [
            "1. Gyapjú és textilhulladék tisztítása és mechanikai aprítása.",
            "2. Rostok szálorientálása és egyenletes terítése formába.",
            "3. Hidrofób biológiai impregnáló szer permetezése a rostokra.",
            "4. Melegpréselés lappréssel a kívánt sűrűség és vastagság eléréséhez.",
            "5. Méretre vágás, peremezés és csomagolás."
        ],
        "required_machines": [
            "Rostaprító gép",
            "Kézi vagy pneumatikus lapprés",
            "Permetező / impregnáló egység",
            "Vágószerszámok"
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
        "image_url": "https://images.unsplash.com/photo-1581092160607-ee22621dd758?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Ergonomikus kézi pisztolyváz (3D nyomtatott - Bambu A1)",
            "RÉTEG 2: MLX90640 hőkamera szenzor modul",
            "RÉTEG 3: DHT22 pára- és hőmérséklet-szenzor",
            "RÉTEG 4: ESP32 mikrokontroller + OLED / TFT színes kijelző",
            "RÉTEG 5: Újratölthető Li-Ion akkumulátor egység"
        ],
        "manufacturing_steps": [
            "1. Ergonomikus pisztolyváz nyomtatása Bambu A1 3D nyomtatón (PETG filament).",
            "2. MLX90640 hőkamera és kijelző csatlakoztatása az ESP32 alaplaphoz.",
            "3. Akkumulátor töltő áramkör bekötése és beépítése a vázba.",
            "4. Hőmérséklet- és energiakalkulációs szoftver / firmware telepítése.",
            "5. Kalibrálási teszt fekete test forrás ellenőrzésével."
        ],
        "required_machines": [
            "Bambu Lab A1 3D nyomtató",
            "Forrasztóállomás",
            "Csavarhúzó szett és tesztpad"
        ],
        "bom": [
            {"Alkatrész / Anyag": "MLX90640 Hőkamera modul", "Mennyiség": "1 db", "Beszerzési Hely": "Elektronikai webshop / TME", "Becsült Ár (HUF)": 12500},
            {"Alkatrész / Anyag": "ESP32 mikrokontroller + TFT kijelző", "Mennyiség": "1 szett", "Beszerzési Hely": "TME / 3DJake", "Becsült Ár (HUF)": 4500},
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
        "image_url": "https://images.unsplash.com/photo-1598488035139-bdbb2231ce04?q=80&w=800&auto=format&fit=crop",
        "exploded": [
            "RÉTEG 1: Dekoratív, akusztikusan áteresztő külső textil borítás",
            "RÉTEG 2: Mikroperforált elülső hangtörő réteg",
            "RÉTEG 3: Nagy sűrűségű kárdírozott gyapjú/kender akusztikai mag",
            "RÉTEG 4: Légrés a hátoldalon a mélyebb frekvenciák elnyeléséhez",
            "RÉTEG 5: Merev hátfal és fali rögzítő konzol"
        ],
        "manufacturing_steps": [
            "1. Gyapjú és kender rostok kárdírozása (szálorientálás).",
            "2. Keret összeállítása lapszabászati elemekből.",
            "3. Rostmag elhelyezése a keretben melegpréseléssel.",
            "4. Mikroperforált lemez és dekoratív textil feszítése a keretre.",
            "5. Minőségellenőrzés és hátoldali rögzítők felszerelése."
        ],
        "required_machines": [
            "Lapszabász eszközök / asztalos szerszámok",
            "Kárdírozógép",
            "Lapprés",
            "Tűzőgép / textilrögzítő"
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

# Kétoszlopos elrendezés a vizuális bemutatáshoz
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 📸 Kész Termék / Prototípus Vizuális Kép")
    st.image(p_data["image_url"], caption=f"{selected_proj} - Illusztrált kész termék nézet", use_container_width=True)

with col2:
    st.markdown("### 🧱 Robbantott Műszaki Szerkezet (Rétegrend)")
    st.write("A fizikai prototípus rétegei és komponensei felülről lefelé / külső burkolattól a magig:")
    for layer in p_data["exploded"]:
        st.markdown(f'<div class="step-box">⚙️ {layer}</div>', unsafe_allow_html=True)

st.write("---")

# Fülek a részletes adatokhoz (belelépve a gyártási folyamatba is)
tab1, tab2, tab3, tab4 = st.tabs([
    "⚙️ Gyártási Folyamat & Technológia",
    "📦 Tételes BOM & Költségek", 
    "🎯 Célpiac & Első Vevők", 
    "⚔️ Konkurencia Elemzés"
])

with tab1:
    st.markdown("### 🛠️ Lépésről Lépésre Követhető Gyártási Folyamat")
    st.write("A garázs-műhelyben történő összeszerelés és előállítás fázisai:")
    for step in p_data["manufacturing_steps"]:
        st.markdown(f'<div class="step-box">📌 {step}</div>', unsafe_allow_html=True)
    
    st.markdown("### 🧰 Szükséges Gépek és Szerszámok")
    for machine in p_data["required_machines"]:
        st.markdown(f"- 🔧 {machine}")

with tab2:
    st.markdown("### 📋 Tételes BOM (Bill of Materials) - Prototípus Szint")
    st.write(f"**Összesített becsült prototípus anyagköltség:** {p_data['total_cost']}")
    
    bom_df = pd.DataFrame(p_data["bom"])
    st.dataframe(bom_df, use_container_width=True, hide_index=True)
    
    st.markdown("""
    <div class="highlight">
    <b>Beszerzési Tipp:</b> Az elektronikai alkatrészekhez a <b>TME Magyarország</b>, a 3D nyomtatáshoz a <b>3DJake</b> ajánlott, míg a rost- és alapanyagok helyi termelőktől vagy fatelepektől szerezhetők be legolcsóbban.
    </div>
    """, unsafe_allow_html=True)

with tab3:
    st.markdown("### 🎯 Ki veszi meg? (Célpiac & Vevői Profil)")
    st.write("A GUME által azonosított elsődleges fizető vevők és szegmensek:")
    for buyer in p_data["target_buyers"]:
        st.markdown(f"- 👤 **{buyer}**")

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
st.success("✨ Másold be ezt az új, teljesen kibővített kódot a GitHub repódban lévő `app.py`-ba! Ekkor már a termékfotó és a robbantott rétegábra mellett egy külön füvön (Gyártási Folyamat & Technológia) a pontos gyártási lépések és a szükséges gépek is listázva lesznek.")
