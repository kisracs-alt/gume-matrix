# gume_v5_1.py
# GUME v5.1 — Global Planetary-Scale Matrix Engine + 4D Block Universe
# Szükséges: pip install streamlit yfinance pandas numpy hmmlearn

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from datetime import datetime

from hmmlearn.hmm import GaussianHMM

# ================================================================
# KONSTANSOK
# ================================================================
N_MC_PATHS = 5000          # Monte-Carlo útvonalszám
N_MC_DAYS = 30             # Monte-Carlo horizont (nap)
MC_SECTORS = ["Globális Index", "AI & Tech", "Energia"]  # MC-ben modellezett szektorok

WF_TRAIN_WINDOW = 500      # Walk-forward: első tanítóablak hossza (nap)
WF_REFIT_EVERY = 20        # Walk-forward: újraillesztés gyakorisága
WF_MIN_DATA = WF_TRAIN_WINDOW + WF_REFIT_EVERY  # minimálisan szükséges adat

SECTOR_TICKERS = {
    "AI & Tech":        ["NVDA", "MSFT", "GOOGL"],
    "Ipar":             ["CAT", "HON", "GE"],
    "Mezőgazdaság":     ["ADM", "CTVA", "DE"],
    "Energia":          ["XOM", "CVX", "BP"],
    "Cloud/IT":         ["AMZN", "CRM", "NOW"],
}
INDEX_TICKER = "^STOXX50E"  # Globális/Európai proxy index

ASSET_ORDER = list(SECTOR_TICKERS.keys()) + ["Globális Index"]


# ================================================================
# 4D BLOCK UNIVERSE ENGINE
# ================================================================
class GUME4DBlockUniverseGlobalEngine:

    def __init__(self, market_data):
        if market_data is None or len(market_data) < 30:
            raise ValueError("A market_data legalább 30 napos legyen.")
        self.market_data = market_data

    def compute_boltzmann_entropy(self, returns):
        flat = returns.values.flatten()
        flat = flat[np.isfinite(flat)]
        if len(flat) == 0:
            return 0.0
        hist, _ = np.histogram(flat, bins=30, density=True)
        p = hist / hist.sum()
        p = p[p > 0]
        return float(-np.sum(p * np.log(p)))

    def compute_network_centrality(self, correlation_matrix):
        corr = correlation_matrix.fillna(0).values
        corr = (corr + corr.T) / 2.0
        evals, evecs = np.linalg.eigh(corr)
        pv = np.abs(evecs[:, -1])
        weights = pv / pv.sum() if pv.sum() > 0 else np.ones(len(corr)) / len(corr)
        return pd.Series(weights, index=correlation_matrix.columns)

    def scan_block_universe_tomorrow(self):
        returns = self.market_data.pct_change().dropna()
        if len(returns) < 20:
            raise ValueError("Túl kevés érvényes hozamadat a letapogatáshoz.")

        correlation_matrix = returns.corr()

        vols = returns.std() * np.sqrt(252)
        evals, _ = np.linalg.eigh((correlation_matrix.values + correlation_matrix.values.T) / 2)
        denom = max(len(correlation_matrix), 1)
        systemic_risk = max(evals[-1], 0) / denom
        system_stress = float((vols.mean() * 100) * (1.0 + systemic_risk))

        beta = min(system_stress / 100.0, 0.95)
        lorentz_gamma = float(1.0 / np.sqrt(max(1.0 - beta**2, 1e-6)))

        entropy = self.compute_boltzmann_entropy(returns)
        centrality = self.compute_network_centrality(correlation_matrix)

        if system_stress < 40:
            metric_interval_type = "Időszerű (Timelike — Determinisztikus Trend)"
        elif system_stress < 70:
            metric_interval_type = "Fény-szerű határzóna (Nulllike — Transzió)"
        else:
            metric_interval_type = "Térszerű (Spacelike — Kaotikus Sokk)"

        if lorentz_gamma < 1.2:
            trajectory = ("Stabil, enyhén emelkedő 4D kristály-koordináta "
                          "(Nincs szingularitás)")
        elif lorentz_gamma < 2.0:
            trajectory = ("Görbült világvonal, mérsékelt téri torzulás "
                          "(Geodéta-instabilitás kezdeti fázisa)")
        else:
            trajectory = ("Erősen görbült világvonal, szingularitás-közeli "
                          "koordináta (Rendkívüli farokveszély)")

        blur = float(np.clip((system_stress / 100.0) * 0.6
                             + min(entropy / 5.0, 1.0) * 0.4, 0.0, 1.0))

        return {
            "metric_status": metric_interval_type,
            "system_stress_index": round(system_stress, 2),
            "lorentz_gamma_factor": round(lorentz_gamma, 4),
            "boltzmann_entropy": round(entropy, 4),
            "gravitational_center": centrality.idxmax(),
            "gravitational_center_weight": round(centrality.max(), 4),
            "worldline_trajectory": trajectory,
            "coherence_blur_probability": round(blur, 3),
            "centrality": centrality,
            "correlation_matrix": correlation_matrix,
        }


# ================================================================
# FŐMOTOR — GUME v5.1
# ================================================================
class GlobalPlanetaryMatrixEngine:

    def __init__(self, lookback="10y"):
        self.lookback = lookback
        self.sectors = list(SECTOR_TICKERS.keys())
        self.assets = ASSET_ORDER
        self.market_data = None
        self.correlation_matrix = None

    def fetch_global_telemetry(self):
        all_tickers = []
        for tickers in SECTOR_TICKERS.values():
            all_tickers.extend(tickers)
        all_tickers.append(INDEX_TICKER)

        raw = yf.download(all_tickers, period=self.lookback,
                          interval="1d", progress=False, auto_adjust=True)
        close = raw["Close"]

        if isinstance(close, pd.Series):
            close = close.to_frame(name=INDEX_TICKER)

        sector_frames = {}
        for sector, tickers in SECTOR_TICKERS.items():
            avail = [t for t in tickers if t in close.columns]
            if avail:
                sector_frames[sector] = close[avail].mean(axis=1)
        if INDEX_TICKER in close.columns:
            sector_frames["Globális Index"] = close[INDEX_TICKER]

        md = pd.DataFrame(sector_frames).sort_index().ffill().dropna()
        if len(md) < 100:
            raise ValueError(f"Csak {len(md)} nap érvényes adat — legalább 100 kell.")
        self.market_data = md
        self.correlation_matrix = md.pct_change().dropna().corr()
        return md

    def get_returns(self):
        return self.market_data.pct_change().dropna()

    def compute_network_centrality(self):
        corr = self.correlation_matrix.fillna(0).values
        corr = (corr + corr.T) / 2.0
        evals, evecs = np.linalg.eigh(corr)
        pv = np.abs(evecs[:, -1])
        w = pv / pv.sum() if pv.sum() > 0 else np.ones(len(corr)) / len(corr)
        return dict(zip(self.correlation_matrix.columns, w))

    def calculate_global_stress_index(self):
        returns = self.get_returns()
        vols = returns.std() * np.sqrt(252)
        corr = (self.correlation_matrix.values + self.correlation_matrix.values.T) / 2
        evals, _ = np.linalg.eigh(corr)
        systemic = max(evals[-1], 0) / max(len(corr), 1)
        stress = float(vols.mean() * 100 * (1.0 + systemic))
        return stress, (vols * 100).to_dict()

    def calculate_boltzmann_entropy(self):
        flat = self.get_returns().values.flatten()
        flat = flat[np.isfinite(flat)]
        if len(flat) == 0:
            return 0.0
        hist, _ = np.histogram(flat, bins=30, density=True)
        p = hist / hist.sum()
        p = p[p > 0]
        return float(-np.sum(p * np.log(p)))

    def detect_regime_hmm(self):
        returns = self.get_returns()
        col = "Globális Index" if "Globális Index" in returns.columns else returns.columns[0]
        X = returns[col].dropna().values.reshape(-1, 1)
        if len(X) < 250:
            return None
        try:
            model = GaussianHMM(n_components=3, covariance_type="full",
                                n_iter=200, random_state=42)
            model.fit(X)
            hidden = model.predict(X)
        except Exception:
            return None

        stats = []
        for i in range(3):
            mask = hidden == i
            stats.append({
                "state": i,
                "mean": float(X[mask].mean()) if mask.any() else 0.0,
                "vol": float(X[mask].std()) if mask.sum() > 1 else 1.0,
                "count": int(mask.sum()),
            })
        order = sorted(stats, key=lambda s: s["vol"])
        label_map = {
            order[0]["state"]: "Nyugodt/Optimista",
            order[1]["state"]: "Átmeneti/Keveredett",
            order[2]["state"]: "Válság/Stressz",
        }
        labels = pd.Series([label_map[h] for h in hidden],
                           index=returns[col].dropna().index)

        T = np.zeros((3, 3))
        states_order = [order[0]["state"], order[1]["state"], order[2]["state"]]
        for a_i, a in enumerate(states_order):
            idx_a = np.where(hidden[:-1] == a)[0]
            for b_i, b in enumerate(states_order):
                T[a_i, b_i] = np.mean(hidden[idx_a + 1] == b) if len(idx_a) else 0.0
        T = T / T.sum(axis=1, keepdims=True).clip(min=1e-9)
        next_probs = T[states_order.index(hidden[-1])]

        return {
            "regime_series": labels,
            "label_map": label_map,
            "regime_stats": {label_map[s["state"]]: s for s in stats},
            "transition_matrix": T,
            "next_probs": next_probs,
            "posteriors": model.predict_proba(X),
            "current_regime": labels.iloc[-1],
        }

    def walk_forward_regime_signals(self):
        returns = self.get_returns()
        col = "Globális Index" if "Globális Index" in returns.columns else returns.columns[0]
        r = returns[col].dropna()
        if len(r) < WF_MIN_DATA:
            return None

        signals = pd.Series(index=r.index, dtype=float)

        for start in range(WF_TRAIN_WINDOW, len(r), WF_REFIT_EVERY):
            train = r.iloc[:start].values.reshape(-1, 1)
            try:
                m = GaussianHMM(n_components=3, covariance_type="full",
                                n_iter=100, random_state=42)
                m.fit(train)
                hidden = m.predict(train)
            except Exception:
                continue

            vols = [train[hidden == i].std() if (hidden == i).sum() > 1 else 1.0
                    for i in range(3)]
            order = np.argsort(vols)
            lbl = {order[0]: "Nyugodt/Optimista", order[1]: "Átmeneti/Keveredett",
                   order[2]: "Válság/Stressz"}

            last_state = hidden[-1]
            signals.iloc[start:start + WF_REFIT_EVERY] = (
                1.0 if lbl[last_state] == "Nyugodt/Optimista"
                else 0.5 if lbl[last_state] == "Átmeneti/Keveredett"
                else 0.0
            )

        return signals.dropna()

    def backtest_regime_strategy(self, signals):
        returns = self.get_returns()
        col = "Globális Index" if "Globális Index" in returns.columns else returns.columns[0]
        r = returns[col]
        strat_ret = r.loc[signals.index] * (signals - 0.5) * 2.0
        strat_ret = strat_ret.fillna(0)

        def perf(x):
            eq = (1 + x).cumprod()
            total = eq.iloc[-1] - 1
            sharpe = x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0
            dd = (eq / eq.cummax() - 1).min()
            return total, sharpe, dd

        bh_total, bh_sharpe, bh_dd = perf(r.loc[signals.index])
        st_total, st_sharpe, st_dd = perf(strat_ret)
        return {
            "buy_hold": {"total_return": bh_total, "sharpe": bh_sharpe, "max_dd": bh_dd},
            "strategy": {"total_return": st_total, "sharpe": st_sharpe, "max_dd": st_dd},
            "equity_curves": pd.DataFrame({
                "Buy & Hold": (1 + r.loc[signals.index]).cumprod(),
                "Rezsim-stratégia": (1 + strat_ret).cumprod(),
            }, index=signals.index),
        }

    def build_black_litterman(self, risk_aversion=2.5, tau=0.05):
        returns = self.get_returns()
        cov = returns.cov().values * 252
        n = len(self.assets)

        centr = self.compute_network_centrality()
        w_mkt = np.array([centr.get(a, 1 / n) for a in self.assets])
        w_mkt = w_mkt / w_mkt.sum()

        pi = risk_aversion * cov @ w_mkt

        omega = tau * cov
        inv = np.linalg.pinv(omega)
        P = np.eye(n)
        Q = pi
        omega = tau * P @ cov @ P.T
        A = np.linalg.pinv(tau * cov)
        B = P.T @ np.linalg.pinv(omega) @ P
        mu_bl = np.linalg.pinv(A + B) @ (A @ pi + P.T @ np.linalg.pinv(omega) @ Q)
        cov_bl = cov + np.linalg.pinv(A + B)

        w_eq = np.linalg.pinv(risk_aversion * cov_bl) @ mu_bl
        w_eq = np.clip(w_eq, -0.5, 0.5)
        if np.abs(w_eq).sum() == 0:
            w_eq = w_mkt
        w_eq = w_eq / np.sum(np.abs(w_eq))

        return {"mu_bl": mu_bl, "cov_bl": cov_bl, "weights": w_eq,
                "market_weights": w_mkt}

    def run_monte_carlo(self, n_paths=N_MC_PATHS, n_days=N_MC_DAYS):
        returns = self.get_returns()[MC_SECTORS]
        mu = returns.mean().values
        cov = returns.cov().values * 252
        rng = np.random.default_rng(42)

        df = 5
        L = np.linalg.cholesky(cov + np.eye(len(mu)) * 1e-8)
        norm_shocks = rng.standard_normal((n_paths, n_days, len(mu)))
        chi2 = rng.chisquare(df, (n_paths, n_days, 1))
        t_shocks = norm_shocks / np.sqrt(chi2 / df)
        t_shocks *= np.sqrt((df - 2) / df)

        paths = np.zeros((n_paths, n_days + 1, len(mu)))
        paths[:, 0, :] = 100.0
        for d in range(1, n_days + 1):
            paths[:, d, :] = paths[:, d - 1, :] * np.exp(
                (mu - 0.5 * np.diag(cov)) / 252 + (t_shocks[:, d - 1, :] @ L.T) / np.sqrt(252)
            )

        return paths

    def run_full_scan(self):
        report = {}

        md = self.fetch_global_telemetry()

        # 1. 4D Blokkuniverzum letapogatás
        engine4d = GUME4DBlockUniverseGlobalEngine(md)
        report["block_universe"] = engine4d.scan_block_universe_tomorrow()

        # 2. Stressz + volatilitások
        stress, vols = self.calculate_global_stress_index()
        report["stress_index"] = stress
        report["vols"] = vols

        # 3. Entrópia
        report["entropy"] = self.calculate_boltzmann_entropy()

        # 4. Centralitás
        report["centrality_weights"] = self.compute_network_centrality()

        # 5. Korrelációs mátrix
        report["correlation_matrix"] = self.correlation_matrix

        # 6. HMM rezsim-detektálás
        report["hmm"] = self.detect_regime_hmm()

        # 7. Walk-forward jelzések + backtest
        wf = self.walk_forward_regime_signals()
        report["walk_forward"] = wf
        if wf is not None:
            report["backtest"] = self.backtest_regime_strategy(wf)

        # 8. Black-Litterman
        report["black_litterman"] = self.build_black_litterman()

        # 9. Monte-Carlo
        report["mc_paths"] = self.run_monte_carlo()

        # 10. Nyers adat
        report["market_data"] = md

        return report


# ================================================================
# STREAMLIT UI
# ================================================================
st.set_page_config(page_title="GUME v5.1", page_icon="🌍", layout="wide")
st.title("🌍 GUME v5.1 — Global Planetary-Scale Matrix Engine")
st.caption("4D Blokkuniverzum • Walk-Forward HMM • Black-Litterman • Student-t Monte-Carlo")

with st.sidebar:
    st.header("⚙️ Paraméterek")
    lookback = st.selectbox("Vizsgált időszak", ["5y", "10y", "15y", "20y"], index=1)
    risk_aversion = st.slider("Kockázatkerülés (δ)", 1.0, 10.0, 2.5, 0.5)
    run_btn = st.button("🚀 Globális Szimuláció Futtatása", use_container_width=True)

if run_btn:
    with st.spinner("🌍 Globális telemetria letöltése és 4D letapogatás..."):
        try:
            engine = GlobalPlanetaryMatrixEngine(lookback=lookback)
            report = engine.run_full_scan()
            st.session_state["gume_report"] = report
        except Exception as e:
            st.error(f"Hiba a szimuláció közben: {e}")

report = st.session_state.get("gume_report", None)

if report:
    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["🌌 4D Blokkuniverzum", "📊 Piaci State", "🔮 HMM Rezsim",
         "💰 Portfólió", "📈 Monte-Carlo"])

    with tab1:
        st.header("🌌 4D Blokkuniverzum Világvonal-Szimuláció")
        bu = report["block_universe"]

        c1, c2, c3 = st.columns(3)
        c1.metric("Rendszer-Stressz Index", bu["system_stress_index"])
        c2.metric("Lorentz Gamma", bu["lorentz_gamma_factor"])
        c3.metric("Boltzmann-Entrópia", bu["boltzmann_entropy"])

        c1, c2, c3 = st.columns(3)
        c1.metric("Metrika Állapot", bu["metric_status"])
        c2.metric("Gravitációs Középpont", bu["gravitational_center"],
                  delta=f"{bu['gravitational_center_weight']:.1%}")
        c3.metric("Elmosódási Valószínűség", f"{bu['coherence_blur_probability']:.1%}")

        st.info(f"**Világvonal-trajektória:** {bu['worldline_trajectory']}")

        st.subheader("🕸️ Hálózati Gravitációs Súlyok")
        centr = bu["centrality"]
        st.bar_chart(centr)

        st.subheader("🔗 Szektorális Korrelációs Mátrix (4D)")
        st.dataframe(bu["correlation_matrix"].style
                     .background_gradient(cmap="RdYlGn_r", vmin=-1, vmax=1)
                     .format("{:.2f}"))

    with tab2:
        st.header("📊 Piaci Stressz és Volatilitás")
        c1, c2, c3 = st.columns(3)
        c1.metric("Globális Stressz Index", f"{report['stress_index']:.2f}")
        c2.metric("Boltzmann-Entrópia", f"{report['entropy']:.4f}")
        c3.metric("Vezető Szektor (Centralitás)",
                  max(report["centrality_weights"], key=report["centrality_weights"].get))

        st.subheader("Éves Volatilitások (%)")
        st.bar_chart(pd.Series(report["vols"]))

        st.subheader("🔗 Korrelációs Mátrix")
        st.dataframe(report["correlation_matrix"].style
                     .background_gradient(cmap="RdYlGn_r", vmin=-1, vmax=1)
                     .format("{:.2f}"))

        with st.expander("📁 Nyers piaci adatok (utolsó 60 nap)"):
            st.dataframe(report["market_data"].tail(60))

    with tab3:
        st.header("🔮 HMM Rezsimelemzés")
        hmm = report["hmm"]
        if hmm is None:
            st.warning("Nincs elég adat a HMM illesztéshez.")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Aktuális Rezsim", hmm["current_regime"])
            next_idx = int(np.argmax(hmm["next_probs"]))
            regime_names = list(hmm["regime_stats"].keys())
            c2.metric("Holnapi Legvalószínűbb Rezsim", regime_names[next_idx],
                      delta=f"{hmm['next_probs'][next_idx]:.1%}")

            st.subheader("Rezsim-Statisztikák")
            st.dataframe(pd.DataFrame(hmm["regime_stats"]).T)

            st.subheader("Rezsim-Sorozat (utolsó 250 nap)")
            regime_num = hmm["regime_series"].map(
                {"Nyugodt/Optimista": 0, "Átmeneti/Keveredett": 1, "Válság/Stressz": 2})
            st.area_chart(regime_num.tail(250), height=250)

            st.subheader("Markov Transziós Mátrix")
            T = pd.DataFrame(hmm["transition_matrix"],
                             index=regime_names, columns=regime_names)
            st.dataframe(T.style.background_gradient(cmap="Blues", vmin=0, vmax=1)
                         .format("{:.2f}"))

            st.markdown("---")
            st.subheader("🚶 Walk-Forward Jelzések (Out-of-Sample)")
            wf_chart = pd.DataFrame({
                "Jel (0-1)": report["walk_forward"],
            })
            st.line_chart(wf_chart)

            if "backtest" in report:
                bt = report["backtest"]
                st.subheader("📉 Backtest Eredmények")
                c1, c2, c3 = st.columns(3)
                c1.metric("Stratégia Hozam", f"{bt['strategy']['total_return']:.1%}")
                c2.metric("Buy & Hold Hozam", f"{bt['buy_hold']['total_return']:.1%}")
                c3.metric("Stratégia Sharpe", f"{bt['strategy']['sharpe']:.2f}")
                c1, c2, c3 = st.columns(3)
                c1.metric("B&H Sharpe", f"{bt['buy_hold']['sharpe']:.2f}")
                c2.metric("Stratégia Max DD", f"{bt['strategy']['max_dd']:.1%}")
                c3.metric("B&H Max DD", f"{bt['buy_hold']['max_dd']:.1%}")

                st.subheader("Tőkegörbék (Out-of-Sample)")
                st.line_chart(bt["equity_curves"])

    with tab4:
        st.header("💰 Black-Litterman Optimális Portfólió")
        bl = report["black_litterman"]

        st.subheader("Optimális Súlyok")
        w_series = pd.Series(bl["weights"], index=ASSET_ORDER)
        st.bar_chart(w_series)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Piaci (Centralitás) Súlyok")
            st.bar_chart(pd.Series(bl["market_weights"], index=ASSET_ORDER))
        with c2:
            st.subheader("BL Implikált Hozamok (μ)")
            st.bar_chart(pd.Series(bl["mu_bl"], index=ASSET_ORDER))

        st.subheader("BL Kovariancia-mátrix (évesített)")
        st.dataframe(pd.DataFrame(bl["cov_bl"], index=ASSET_ORDER, columns=ASSET_ORDER)
                     .style.background_gradient(cmap="Blues").format("{:.4f}"))

    with tab5:
        st.header("📈 Student-t Monte-Carlo Szimuláció (30 nap)")
        paths = report["mc_paths"]

        for i, sector in enumerate(MC_SECTORS):
            st.subheader(f"{sector} — {N_MC_PATHS} útvonal")
            p = paths[:, :, i]

            pct = np.percentile(p, [5, 25, 50, 75, 95], axis=0)
            pct_df = pd.DataFrame({
                "P5": pct[0], "P25": pct[1], "Medián": pct[2],
                "P75": pct[3], "P95": pct[4],
            })
            st.line_chart(pct_df)

            final = p[:, -1]
            c1, c2, c3 = st.columns(3)
            c1.metric("Medián Végérték", f"{np.median(final):.1f}")
            c2.metric("P5 (Veszélyzóna)", f"{np.percentile(final, 5):.1f}")
            c3.metric("P(Veszteség >10%)",
                      f"{np.mean(final < 90):.1%}")

        st.caption("Student-t eloszlás (df=5) — vastag farkak modellezve.")

else:
    st.info("👈 Állítsd be a paramétereket és indítsd a szimulációt a sidebarban!")
    st.markdown("""
    ### 🌍 GUME v5.1 — Mit tud ez a motor?

    | Modul | Funkció |
    |---|---|
    | **🌌 4D Blokkuniverzum** | Metrika-intervallum osztályozás, Lorentz-faktor, entrópia |
    | **📊 Piaci State** | Globális stressz-index, volatilitások, korrelációk |
    | **🔮 HMM Rezsim** | 3-állapotú rezsimelemzés volatilitás-alapú stabil címkézéssel |
    | **🚶 Walk-Forward** | Valódi out-of-sample jelzések — nincs look-ahead bias |
    | **📉 Backtest** | Stratégia vs. Buy & Hold összehasonlítás Sharpe/DD metrikákkal |
    | **💰 Black-Litterman** | Centrality-alapú piaci súlyok + implikatív hozamok |
    | **📈 Monte-Carlo** | 5000 útvonal, Student-t vastag farkak, percentil-sávok |

    **Kezdd itt:** válaszd ki az időszakot és nyomd meg a 🚀 gombot!
    """)

st.markdown("---")
st.caption(f"🌍 GUME v5.1 — Futás időpontja: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")