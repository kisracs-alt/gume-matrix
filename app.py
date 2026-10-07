import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# --- Oldal konfiguráció ---
st.set_page_config(
    page_title="GUME v5.1 - Makrogazdasági és Stratégiai Elemző Mátrix",
    page_icon="🌐",
    layout="wide"
)

# --- Stílusok / Címsor ---
st.markdown("""
    <style>
    .main-title { font-size: 2.5rem; font-weight: bold; color: #1E3A8A; }
    .sub-title { font-size: 1.2rem; color: #4B5563; }
    .card { background-color: #F3F4F6; padding: 20px; border-radius: 10px; margin-bottom: 20px; border-left: 5px solid #2563EB; }
    .insight-box { background-color: #EFF6FF; padding: 15px; border-radius: 8px; border: 1px solid #BFDBFE; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">🌐 GUME v5.1 – Globális Stratégiai & Piaci Elemző Mátrix</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Intelligens döntéstámogató és jövőbeli forgatókönyv-generátor rendszer</div>', unsafe_allow_html=True)
st.write("---")

# --- Oldalsáv / Paraméterek ---
st.sidebar.header("⚙️ Szimulációs Paraméterek")

asset_input = st.sidebar.text_input(
    "Vizsgált Eszközök (Ticker / Tőzsdjel, vesszővel elválasztva)", 
    value="SPY, QQQ, GLD, BTC-USD, EURUSD=X"
)
tickers = [t.strip().upper() for t in asset_input.split(",") if t.strip()]

period_option = st.sidebar.selectbox("Vizsgált Időszak", ["1y", "2y", "5y", "10y"], index=0)
risk_tolerance = st.sidebar.slider("Kockázatkezelési Küszöb (Max Megengedett Volatilitás %)", 5, 40, 15)

st.sidebar.markdown("---")
run_button = st.sidebar.button("🚀 Globális Elemzés és Forgatókönyv Futtatása", type="primary")

# --- Fővezérlő logika ---
if run_button:
    if not tickers:
        st.error("Kérlek adj meg legalább egy érvényes tőzsdei eszközt!")
    else:
        with st.spinner("Adatok letöltése, ökonometriai számítások és jövőbeli forgatókönyv-elemzés futtatása..."):
            try:
                # Adatletöltés Yahoo Finance-ről
                data = yf.download(tickers, period=period_option, progress=False)
                
                if isinstance(data.columns, pd.MultiIndex):
                    prices = data['Close']
                else:
                    prices = data[['Close']] if 'Close' in data else data

                prices = prices.dropna(how='all')
                
                if prices.empty:
                    st.error("Nem található adat a megadott eszközökhöz. Ellenőrizd a tickereket!")
                else:
                    # Számítások
                    returns = prices.pct_change().dropna()
                    annualized_return = returns.mean() * 252
                    annualized_volatility = returns.std() * np.sqrt(252)
                    sharpe_ratio = annualized_return / (annualized_volatility + 1e-6)
                    corr_matrix = returns.corr()

                    # --- Eredmények Megjelenítése ---
                    st.markdown("### 📊 1. Kvantitatív Teljesítménymátrix & Mutatók")
                    
                    metrics_df = pd.DataFrame({
                        "Évesített Hozzam (%)": (annualized_return * 100).round(2),
                        "Évesített Volatilitás (%)": (annualized_volatility * 100).round(2),
                        "Sharpe Mutató": sharpe_ratio.round(2)
                    })
                    st.dataframe(metrics_df, use_container_width=True)

                    # --- Korrelációs mátrix ---
                    st.markdown("### 🔗 2. Eszközök közötti Korrelációs Háló")
                    st.dataframe(corr_matrix.style.background_gradient(cmap="coolwarm", vmin=-1, vmax=1).format("{:.2f}"), use_container_width=True)

                    # --- RÉSZLETES SZÖVEGES ELEMZÉS ÉS JÖVŐBELI KITEKINTÉS ---
                    st.markdown("---")
                    st.markdown("### 📝 3. Mélyreható Makrogazdasági és Stratégiai Elemzés")

                    # Általános piaci hangulat megállapítása
                    avg_vol = annualized_volatility.mean() * 100
                    market_sentiment = "magas volatilitású, védekező" if avg_vol > 20 else "stabil, növekedésorientált"

                    st.markdown(f"""
                    <div class="card">
                        <h4>🌍 Makrogazdasági Környezet Értékelése</h4>
                        <p>A GUME v5.1 motor által elemezett adatok alapján a globális piaci környezet jelenleg <b>{market_sentiment}</b> fázisban van. Az átlagos eszközvolatilitás <b>{avg_vol:.1f}%</b> körül alakul, ami jelzi a piaci szereplők kockázatvállalási hajlandóságát és az inflációs/kamatláb-környezet okozta bizonytalanságot.</p>
                    </div>
                    """, unsafe_allow_html=True)

                    # Egyedi eszközök értékelése szövegesen
                    st.markdown("#### 🔍 Eszközspecifikus Teljesítményértékelések")
                    for t in tickers:
                        if t in annualized_return:
                            h = annualized_return[t] * 100
                            v = annualized_volatility[t] * 100
                            s = sharpe_ratio[t]
                            
                            status_text = "Kiemelkedő növekedési potenciál" if h > 10 else ("Stabil, de alacsonyabb hozamú" if h > 0 else "Negatív korrekciós fázis")
                            risk_eval = "Magas kockázatú, óvatosságot igényel" if v > risk_tolerance else "Megfelelő kockázatkezelési sávban mozog"

                            st.markdown(f"""
                            * **{t}**: 
                              * *Teljesítmény:* Az eszköz évesített hozama **{h:.2f}%**, volatilitása pedig **{v:.2f}%** mellett alakul (Sharpe: **{s:.2f}**).
                              * *Értékelés:* **{status_text}**. Elemzési szempontból ez a(z) {t} eszköz jelenleg a **{risk_eval}** kategóriába sorolható a portfólión belül.
                            """)

                    # --- JÖVŐBELI FORGATÓKÖNYVEK ÉS KILÁTÁSOK ---
                    st.markdown("---")
                    st.markdown("### 🔮 4. Jövőbeli Forgatókönyvek és Kilátások a Közeljövőre")

                    st.markdown(f"""
                    <div class="insight-box">
                        <h4>📈 1. Forgatókönyv: Alapeset (Makrogazdasági Konszolidáció)</h4>
                        <p>Amennyiben a jegybanki kamatpályák stabilizálódnak, és nem történik rendszerszintű likviditási sokk, a kockázatosabb eszközök (pl. technológiai részvények, növekedési assetek) fokozatos felívelésre számíthatnak. A volatilitás mérséklődése a stabilabb Sharpe-mutatóval rendelkező elemek felé tereli a tőkét.</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="insight-box">
                        <h4>⚠️ 2. Forgatókönyv: Kockázati / Feszültségi Szcenárió</h4>
                        <p>Geopolitikai feszültségek vagy váratlan inflációs újragyorsulás esetén az eszközök közötti korrelációk felgyorsulhatnak (1-es korreláció felé tartva), ami megnehezíti a tradicionális diverzifikációt. Ebben az esetben a defenzív eszközök (pl. arany, likvid tartalékok) felértékelődése várható.</p>
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown("---")
                    st.markdown("### 🛡️ 5. Stratégiai Akcióterv és Ajánlások")
                    st.markdown(f"""
                    * **Portfólió Súlyozás:** A megadott <b>{risk_tolerance}%</b>-os kockázati küszöb alapján javasolt az alacsonyabb Sharpe-mutatóval rendelkező elemek súlyának csökkentése.
                    * **Likviditáskezelés:** Tartson fenn legalább 10-15%-os likvid tartalékot a váratlan piaci korrekciók alóli belépési pontok kihasználására.
                    * **Rebalanszírozás:** Negyedévente vizsgálja felül a korrelációs mátrixot; ha két eszköz korrelációja 0.8 fölé emelkedik, a diverzifikációs hatás elvész, így szerkezeti átrendezés válik szükségessé.
                    """)

            except Exception as e:
                st.error(f"Hiba történt az elemzés futtatása közben: {e}")
else:
    st.info("👈 Add meg a kívánt eszközöket a bal oldali sávban, majd kattints a **Globális Elemzés és Forgatókönyv Futtatása** gombra a részletes jelentés elkészítéséhez!")
