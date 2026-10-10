
from __future__ import annotations

"""GUME v6.6 - Global Intelligence Engine

A modular Streamlit research system combining:
- market data (Yahoo Finance / yfinance)
- optional World Bank public indicators (no API key)
- optional FRED indicators (API key required by FRED)
- optional Open-Meteo weather observations/forecast
- CSV upload for any additional macro, agriculture, trade, geopolitical,
  demographic, technology or company dataset
- provenance, freshness, missingness and confidence scoring
- transparent regime, risk, stress, Monte Carlo and domain-fusion layers

This is a research / decision-support engine, not investment advice.
External connectors are optional: failed connectors never silently become
"real" data; they are explicitly marked unavailable or proxy-backed.
"""

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from io import StringIO
import math
import os
import warnings
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

try:
    import yfinance as yf
except Exception:  # pragma: no cover
    yf = None


APP_VERSION = "6.6"
UTC_NOW = lambda: datetime.now(timezone.utc)


@dataclass
class DataMeta:
    name: str
    source: str
    source_type: str = "external"
    unit: str = "unknown"
    geography: str = "global"
    segment: str = "macro"
    frequency: str = "unknown"
    quality: float = 0.5
    release_lag_days: float = 0.0
    retrieved_at: str = ""
    status: str = "ok"
    notes: str = ""


@dataclass
class ConnectorResult:
    name: str
    frame: pd.DataFrame
    meta: DataMeta
    error: str = ""


class GlobalDataHub:
    """Central provenance-aware data fabric."""

    def __init__(self) -> None:
        self.frames: Dict[str, pd.DataFrame] = {}
        self.meta: Dict[str, DataMeta] = {}

    def add_frame(self, name: str, frame: pd.DataFrame, meta: DataMeta) -> None:
        if frame is None or frame.empty:
            return
        x = frame.copy()
        if not isinstance(x.index, pd.DatetimeIndex):
            x.index = pd.to_datetime(x.index, errors="coerce", utc=True)
        x = x[~x.index.isna()].sort_index()
        x = x.replace([np.inf, -np.inf], np.nan)
        if x.empty:
            return
        self.frames[name] = x
        self.meta[name] = meta

    def quality_report(self) -> pd.DataFrame:
        rows: List[Dict[str, Any]] = []
        now = UTC_NOW()
        for name, frame in self.frames.items():
            meta = self.meta[name]
            missing = float(frame.isna().mean().mean()) if not frame.empty else 1.0
            latest = frame.dropna(how="all").index.max() if not frame.empty else pd.NaT
            age_days = np.nan
            if pd.notna(latest):
                latest_ts = pd.Timestamp(latest)
                if latest_ts.tzinfo is None:
                    latest_ts = latest_ts.tz_localize("UTC")
                age_days = max(0.0, (pd.Timestamp(now) - latest_ts).total_seconds() / 86400.0)
            freshness = freshness_score(age_days, meta.frequency)
            q = float(np.clip(meta.quality, 0, 1))
            score = q * (1 - missing) * freshness
            rows.append({
                "dataset": name,
                "source": meta.source,
                "status": meta.status,
                "rows": len(frame),
                "latest": str(latest) if pd.notna(latest) else "n/a",
                "age_days": age_days,
                "missing_ratio": missing,
                "freshness": freshness,
                "quality_score": score,
                "geography": meta.geography,
                "segment": meta.segment,
                "notes": meta.notes,
            })
        return pd.DataFrame(rows).sort_values("quality_score", ascending=False) if rows else pd.DataFrame()

    def catalog(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(m) for m in self.meta.values()]) if self.meta else pd.DataFrame()


def freshness_score(age_days: float, frequency: str) -> float:
    if not np.isfinite(age_days):
        return 0.0
    freq = str(frequency).lower()
    half_life = {"daily": 7, "weekly": 21, "monthly": 60, "quarterly": 150, "annual": 450}.get(freq, 60)
    return float(np.exp(-age_days / max(half_life, 1)))


def clip01(x: float) -> float:
    return float(np.clip(x, 0.0, 1.0))


def score_from_z(x: float, scale: float = 1.0) -> float:
    if not np.isfinite(x):
        return 0.5
    return clip01(0.5 + 0.25 * np.tanh(float(x) / max(scale, 1e-9)))


def normalize_tickers(text: str) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(x.strip().upper() for x in str(text).replace(";", ",").split(",") if x.strip()))


# ----------------------------- Market connector -----------------------------

if st is not None:
    _cache = st.cache_data
else:  # pragma: no cover
    def _cache(*args, **kwargs):
        def deco(fn):
            return fn
        return deco


@_cache(ttl=900, show_spinner=False)
def download_market_prices(tickers: Tuple[str, ...], period: str) -> pd.DataFrame:
    if yf is None:
        return pd.DataFrame()
    raw = yf.download(
        list(tickers), period=period, auto_adjust=True, progress=False,
        threads=True, group_by="column", multi_level_index=True,
    )
    if raw is None or raw.empty:
        return pd.DataFrame()
    if isinstance(raw.columns, pd.MultiIndex):
        fields = [str(x) for x in raw.columns.get_level_values(0)]
        field = "Close" if "Close" in fields else ("Adj Close" if "Adj Close" in fields else fields[0])
        px = raw[field].copy()
    else:
        field = "Close" if "Close" in raw.columns else str(raw.columns[0])
        px = raw[[field]].copy()
        px.columns = [tickers[0]]
    if isinstance(px, pd.Series):
        px = px.to_frame(name=tickers[0])
    px.columns = [str(c).upper() for c in px.columns]
    px.index = pd.to_datetime(px.index, errors="coerce")
    px = px[~px.index.isna()].sort_index()
    return px.replace([np.inf, -np.inf], np.nan).ffill(limit=3).dropna(how="all")


# ----------------------------- HTTP helpers ---------------------------------

def http_json(url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Any:
    """Bounded-retry HTTP JSON fetch. Retries only transient failures."""
    if requests is None:
        raise RuntimeError("A requests csomag nem érhető el.")
    last_error = None
    for attempt in range(3):
        try:
            r = requests.get(url, params=params or {}, timeout=timeout,
                             headers={"User-Agent": "GUME/6.6"})
            if r.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                last_error = RuntimeError(f"HTTP {r.status_code}")
                import time
                time.sleep(0.5 * (2 ** attempt))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last_error = exc
            if attempt < 2 and (isinstance(exc, requests.Timeout) or isinstance(exc, requests.ConnectionError)):
                import time
                time.sleep(0.5 * (2 ** attempt))
                continue
            raise
    raise RuntimeError(f"HTTP kérés sikertelen: {last_error}")


# ----------------------------- World Bank -----------------------------------

def fetch_world_bank_indicator(country: str, indicator: str, name: str) -> ConnectorResult:
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    try:
        payload = http_json(url, {"format": "json", "per_page": 1000})
        if not isinstance(payload, list) or len(payload) < 2:
            raise RuntimeError("A World Bank válasza nem tartalmaz adatot.")
        rows = payload[1]
        vals = []
        for row in rows:
            if row.get("value") is None or row.get("date") is None:
                continue
            vals.append((pd.Timestamp(f"{row['date']}-12-31", tz="UTC"), float(row["value"])))
        frame = pd.DataFrame(vals, columns=["date", name]).set_index("date").sort_index()
        meta = DataMeta(name=name, source="World Bank", source_type="API", frequency="annual", quality=0.95,
                        geography=country.upper(), segment="economy", retrieved_at=UTC_NOW().isoformat(),
                        notes=f"indicator={indicator}")
        return ConnectorResult(name, frame, meta)
    except Exception as exc:
        meta = DataMeta(name=name, source="World Bank", source_type="API", frequency="annual", quality=0.0,
                        geography=country.upper(), segment="economy", retrieved_at=UTC_NOW().isoformat(),
                        status="error", notes=f"indicator={indicator}")
        return ConnectorResult(name, pd.DataFrame(), meta, str(exc))


# ----------------------------- FRED -----------------------------------------

def fetch_fred_series(series_id: str, api_key: str, name: str) -> ConnectorResult:
    if not api_key:
        meta = DataMeta(name=name, source="FRED", source_type="API", frequency="monthly", quality=0.0,
                        retrieved_at=UTC_NOW().isoformat(), status="not_configured", notes="FRED_API_KEY nincs megadva.")
        return ConnectorResult(name, pd.DataFrame(), meta, "FRED API key hiányzik")
    url = "https://api.stlouisfed.org/fred/series/observations"
    try:
        payload = http_json(url, {"series_id": series_id, "api_key": api_key, "file_type": "json", "sort_order": "asc"})
        rows = []
        for row in payload.get("observations", []):
            try:
                value = float(row["value"])
            except Exception:
                continue
            rows.append((pd.Timestamp(row["date"], tz="UTC"), value))
        frame = pd.DataFrame(rows, columns=["date", name]).set_index("date").sort_index()
        meta = DataMeta(name=name, source="FRED", source_type="API", frequency="monthly", quality=0.95,
                        retrieved_at=UTC_NOW().isoformat(), status="ok", notes=f"series={series_id}")
        return ConnectorResult(name, frame, meta)
    except Exception as exc:
        meta = DataMeta(name=name, source="FRED", source_type="API", frequency="monthly", quality=0.0,
                        retrieved_at=UTC_NOW().isoformat(), status="error", notes=f"series={series_id}")
        return ConnectorResult(name, pd.DataFrame(), meta, str(exc))


# ----------------------------- Open-Meteo ------------------------------------

def fetch_open_meteo(latitude: float, longitude: float, name: str = "Weather") -> ConnectorResult:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude, "longitude": longitude,
        "daily": "temperature_2m_mean,precipitation_sum,wind_speed_10m_max",
        "past_days": 30, "forecast_days": 7, "timezone": "UTC",
    }
    try:
        payload = http_json(url, params)
        daily = payload.get("daily", {})
        dates = daily.get("time", [])
        if not dates:
            raise RuntimeError("Nincs meteorológiai adat.")
        frame = pd.DataFrame({
            "temperature_mean": daily.get("temperature_2m_mean", []),
            "precipitation_sum": daily.get("precipitation_sum", []),
            "wind_max": daily.get("wind_speed_10m_max", []),
        }, index=pd.to_datetime(dates, utc=True))
        meta = DataMeta(name=name, source="Open-Meteo", source_type="API", frequency="daily", quality=0.90,
                        geography=f"{latitude:.4f},{longitude:.4f}", segment="weather",
                        retrieved_at=UTC_NOW().isoformat(), notes="30 nap múlt + 7 nap előrejelzés")
        return ConnectorResult(name, frame, meta)
    except Exception as exc:
        meta = DataMeta(name=name, source="Open-Meteo", source_type="API", frequency="daily", quality=0.0,
                        geography=f"{latitude:.4f},{longitude:.4f}", segment="weather",
                        retrieved_at=UTC_NOW().isoformat(), status="error")
        return ConnectorResult(name, pd.DataFrame(), meta, str(exc))


# ----------------------------- CSV connector --------------------------------

def parse_uploaded_csv(data: bytes, name: str, source: str = "User CSV") -> ConnectorResult:
    try:
        frame = pd.read_csv(StringIO(data.decode("utf-8-sig")))
        if frame.empty:
            raise RuntimeError("Az CSV üres.")
        date_col = next((c for c in frame.columns if str(c).lower() in {"date", "datetime", "time", "timestamp"}), frame.columns[0])
        frame[date_col] = pd.to_datetime(frame[date_col], errors="coerce", utc=True)
        frame = frame.dropna(subset=[date_col]).set_index(date_col).sort_index()
        for c in frame.columns:
            frame[c] = pd.to_numeric(frame[c], errors="coerce")
        frame = frame.dropna(axis=1, how="all")
        meta = DataMeta(name=name, source=source, source_type="CSV", frequency="unknown", quality=0.75,
                        retrieved_at=UTC_NOW().isoformat(), status="ok", notes="Felhasználói adat; szemantikai validáció szükséges.")
        return ConnectorResult(name, frame, meta)
    except Exception as exc:
        meta = DataMeta(name=name, source=source, source_type="CSV", quality=0.0,
                        retrieved_at=UTC_NOW().isoformat(), status="error")
        return ConnectorResult(name, pd.DataFrame(), meta, str(exc))


# ----------------------------- Quant layer ----------------------------------

def log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return np.log(prices / prices.shift(1)).replace([np.inf, -np.inf], np.nan).dropna(how="all")


def annual_return(r: pd.Series, ann: int) -> float:
    """Geometric annualized return from log returns, with sample-length guard."""
    x = r.dropna()
    if len(x) < 2 or ann <= 0:
        return np.nan
    return float(np.expm1(x.mean() * ann))


def annual_vol(r: pd.Series, ann: int) -> float:
    x = r.dropna()
    return float(x.std(ddof=1) * np.sqrt(ann)) if len(x) > 1 else np.nan


def downside_vol(r: pd.Series, ann: int, target: float = 0.0) -> float:
    """Annualized downside deviation relative to a per-period target (default zero)."""
    x = (r.dropna() - target).clip(upper=0.0)
    if len(x) < 2 or ann <= 0:
        return np.nan
    return float(np.sqrt(np.mean(np.square(x))) * np.sqrt(ann))


def sharpe(r: pd.Series, ann: int) -> float:
    v = annual_vol(r, ann)
    return float(r.mean() * ann / v) if np.isfinite(v) and v > 0 else np.nan


def sortino(r: pd.Series, ann: int, target: float = 0.0) -> float:
    x = r.dropna()
    v = downside_vol(x, ann, target=target)
    excess = (x.mean() - target) * ann if len(x) else np.nan
    return float(excess / v) if np.isfinite(v) and v > 0 else np.nan


def max_drawdown(r: pd.Series) -> float:
    x = np.exp(r.fillna(0).cumsum())
    return float((x / x.cummax() - 1).min()) if len(x) else np.nan


def var_cvar(r: pd.Series, level: float = 0.95) -> Tuple[float, float]:
    x = r.dropna()
    if len(x) < 10:
        return np.nan, np.nan
    q = float(np.quantile(x, 1 - level))
    tail = x[x <= q]
    return q, float(tail.mean()) if len(tail) else q


def portfolio_returns(R: pd.DataFrame, weights: pd.Series) -> pd.Series:
    """Compute portfolio log-return approximation using aligned, valid weights.

    For small daily returns the weighted-log-return approximation is useful; it is
    not exactly the log of a rebalanced portfolio's simple return.
    """
    if R is None or R.empty:
        return pd.Series(dtype=float, name="portfolio")
    w = pd.to_numeric(weights.reindex(R.columns), errors="coerce").fillna(0.0)
    if (w < 0).any():
        raise ValueError("Negatív súly nem támogatott ebben az equal-weight referencia-motorban.")
    total = float(w.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("A portfóliósúlyok összege nem pozitív.")
    w = w / total
    # Missing assets are excluded per row, then remaining weights are renormalized.
    arr = R.to_numpy(dtype=float)
    out = np.full(len(R), np.nan)
    wv = w.to_numpy(dtype=float)
    for i, row in enumerate(arr):
        valid = np.isfinite(row) & (wv > 0)
        if valid.any():
            ww = wv[valid]
            ww = ww / ww.sum()
            out[i] = float(row[valid] @ ww)
    return pd.Series(out, index=R.index, name="portfolio").dropna()


def regime_engine(R: pd.DataFrame, ann: int) -> Dict[str, float | str]:
    m = R.mean(axis=1).dropna()
    if len(m) < 30:
        return {"name": "insufficient_data", "trend": np.nan, "vol_ratio": np.nan, "stress": np.nan}
    fast = m.tail(min(63, len(m))).mean() * ann
    slow = m.tail(min(252, len(m))).mean() * ann
    v21 = m.tail(min(21, len(m))).std(ddof=1) * np.sqrt(ann)
    v252 = m.std(ddof=1) * np.sqrt(ann)
    vr = v21 / v252 if v252 > 0 else 1.0
    stress = max(0.0, -m.tail(min(21, len(m))).mean() * ann) + max(0.0, vr - 1.0)
    name = "risk_on" if fast - slow > 0.05 and vr < 1.15 else ("risk_off" if fast - slow < -0.05 or vr > 1.45 else "neutral")
    return {"name": name, "trend": fast - slow, "vol_ratio": vr, "stress": stress}


def stress_matrix(R: pd.DataFrame, regime: str) -> pd.DataFrame:
    v = R.std().replace(0, np.nan)
    beta = (R.mean() / v).replace([np.inf, -np.inf], np.nan).fillna(0)
    rank = beta.rank(pct=True).fillna(0.5)
    specs = {"Base": 0.0, "Risk-on": 0.35, "Inflation / rate shock": -0.45, "Geopolitical stress": -0.60, "Systemic stress": -0.90}
    rows = []
    for label, shock in specs.items():
        q = shock * (0.65 + 0.35 * rank)
        if label == "Risk-on" and regime == "risk_off":
            q *= 0.7
        if label == "Systemic stress":
            q *= 1.2
        rows.append(q.rename(label))
    return pd.DataFrame(rows)


def monte_carlo_student_t(pr: pd.Series, paths: int, horizon: int, df: int = 5, seed: int = 42) -> Tuple[float, float]:
    x = pr.dropna()
    if len(x) < 30:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    mu, sig = float(x.mean()), float(x.std(ddof=1))
    z = rng.standard_t(df=df, size=(int(paths), int(horizon))) / math.sqrt(df / (df - 2))
    terminal = (mu + sig * z).sum(axis=1)
    q = float(np.quantile(terminal, 0.05))
    return q, float(terminal[terminal <= q].mean())


# ----------------------------- Domain fusion --------------------------------

GUME_DOMAINS: Dict[str, List[str]] = {
    "Markets": ["Equities", "Rates", "Credit", "Volatility", "Digital assets"],
    "Industry": ["Manufacturing", "Semiconductors", "Autos", "Construction", "Services"],
    "Agriculture": ["Grains", "Oilseeds", "Livestock", "Fertilizer", "Food security"],
    "Trade": ["Exports", "Imports", "Shipping", "Trade balance", "Supply chains"],
    "Finance": ["Liquidity", "Banks", "Funding", "Leverage", "Financial conditions"],
    "Economy": ["Growth", "Inflation", "Employment", "Productivity", "Demand"],
    "Policy": ["Fiscal", "Monetary", "Regulation", "Industrial policy", "Tax policy"],
    "Politics": ["Government stability", "Elections", "Institutions", "Policy uncertainty", "Social stability"],
    "Geopolitics": ["Conflict", "Sanctions", "Alliances", "Strategic competition", "Sovereign risk"],
    "Weather": ["Temperature", "Precipitation", "Drought", "Storms", "Weather volatility"],
    "Commodities": ["Energy", "Metals", "Precious metals", "Industrial inputs", "Commodity volatility"],
    "Geography": ["Regional concentration", "Chokepoints", "Infrastructure", "Resource geography", "Distance friction"],
    "FX": ["USD", "EUR", "JPY", "EM FX", "FX volatility"],
    "Climate": ["Warming", "Extreme events", "Water stress", "Transition", "Physical risk"],
    "Population": ["Population growth", "Aging", "Migration", "Urbanization", "Labor supply"],
    "Technology": ["Innovation", "Automation", "Robotics", "Compute", "R&D"],
    "AI": ["Model capability", "Compute demand", "Adoption", "AI investment", "AI risk"],
    "IT": ["Cloud", "Cybersecurity", "Software", "Data infrastructure", "Networks"],
    "Science": ["Research intensity", "Biotech", "Materials", "Energy science", "Scientific uncertainty"],
    "Quantum": ["Quantum compute", "Quantum sensing", "Quantum communication", "Error correction", "Commercial readiness"],
    "Society": ["Trust", "Inequality", "Mobility", "Polarization", "Social resilience"],
    "Psychology": ["Risk appetite", "Fear", "Greed", "Attention", "Behavioral stress"],
    "Culture": ["Consumption", "Media", "Values", "Creativity", "Cultural diffusion"],
    "Mathematics": ["Probability", "Statistics", "Optimization", "Networks", "Information"],
    "Spacetime": ["Temporal state", "Spatial state", "Velocity proxy", "Interaction intensity", "State distance"],
}


# These mappings deliberately use only indicators whose semantics are clear.
WORLD_BANK_MAP = {
    "gdp_growth": ("NY.GDP.MKTP.KD.ZG", "GDP growth"),
    "inflation": ("FP.CPI.TOTL.ZG", "Inflation"),
    "unemployment": ("SL.UEM.TOTL.ZS", "Unemployment"),
    "population": ("SP.POP.TOTL", "Population"),
}


def latest_value(hub: GlobalDataHub, key: str) -> float:
    frame = hub.frames.get(key)
    if frame is None or frame.empty:
        return np.nan
    s = frame.iloc[:, 0].dropna()
    return float(s.iloc[-1]) if len(s) else np.nan


def build_domain_scores(R: pd.DataFrame, reg: Dict[str, Any], hub: GlobalDataHub) -> pd.DataFrame:
    market_mean = R.mean(axis=1).dropna()
    mean_r = float(market_mean.tail(21).mean()) if len(market_mean) else 0.0
    vol = float(market_mean.std(ddof=1)) if len(market_mean) > 2 else 0.0
    if R.shape[1] > 1:
        corr = R.corr()
        mask = ~np.eye(corr.shape[0], dtype=bool)
        vals = corr.where(mask).stack().dropna()
        cross_corr = float(vals.mean()) if len(vals) else 0.0
    else:
        cross_corr = 0.0
    stress = float(reg.get("stress", np.nan)) if np.isfinite(reg.get("stress", np.nan)) else 0.0
    trend = float(reg.get("trend", np.nan)) if np.isfinite(reg.get("trend", np.nan)) else 0.0

    base = score_from_z(mean_r * 252, 1.0)
    risk = score_from_z(-stress, 1.0)
    diversification = clip01(1.0 - max(0.0, cross_corr))
    stability = clip01(1.0 - min(1.0, vol * 10.0))
    trend_score = score_from_z(trend, 0.5)

    # External macro evidence. Values are not forced into a single metric when
    # semantics are ambiguous; they only adjust explicitly mapped domains.
    wb_gdp = latest_value(hub, "WB:gdp_growth")
    wb_inf = latest_value(hub, "WB:inflation")
    wb_unemp = latest_value(hub, "WB:unemployment")
    macro_evidence = []
    if np.isfinite(wb_gdp):
        macro_evidence.append(score_from_z(wb_gdp, 3.0))
    if np.isfinite(wb_inf):
        macro_evidence.append(score_from_z(-wb_inf, 5.0))
    if np.isfinite(wb_unemp):
        macro_evidence.append(score_from_z(-wb_unemp, 5.0))
    macro_score = float(np.mean(macro_evidence)) if macro_evidence else np.nan

    weather_frame = hub.frames.get("Weather")
    weather_score = 0.5
    if weather_frame is not None and not weather_frame.empty:
        # A neutral weather score is intentionally retained: raw weather values
        # are not converted to "good/bad" without a crop/location baseline.
        weather_score = 0.5

    proxies = {
        "Markets": np.mean([base, stability, trend_score]),
        "Industry": np.mean([base, stability]),
        "Agriculture": np.mean([base, risk]),
        "Trade": np.mean([base, diversification]),
        "Finance": np.mean([base, stability, risk]),
        "Economy": macro_score if np.isfinite(macro_score) else np.mean([base, trend_score]),
        "Policy": np.mean([risk, 0.5]),
        "Politics": np.mean([risk, 0.5]),
        "Geopolitics": np.mean([risk, stability]),
        "Weather": weather_score,
        "Commodities": np.mean([base, risk]),
        "Geography": np.mean([diversification, 0.5]),
        "FX": np.mean([base, stability]),
        "Climate": 0.5,
        "Population": 0.5,
        "Technology": np.mean([base, trend_score]),
        "AI": np.mean([base, trend_score]),
        "IT": np.mean([base, stability]),
        "Science": np.mean([trend_score, 0.5]),
        "Quantum": 0.5,
        "Society": np.mean([risk, 0.5]),
        "Psychology": np.mean([base, risk]),
        "Culture": np.mean([base, 0.5]),
        "Mathematics": np.mean([diversification, stability]),
        "Spacetime": np.mean([trend_score, diversification, stability]),
    }

    directly_measured = {"Economy"} if macro_evidence else set()
    directly_measured.update({"Weather"} if weather_frame is not None and not weather_frame.empty else set())
    market_backed = {"Markets", "Finance", "FX", "Commodities"}
    rows = []
    for domain, segments in GUME_DOMAINS.items():
        score = clip01(float(proxies[domain]))
        if domain in directly_measured:
            conf = 0.78
            evidence = "external connector + market context"
        elif domain in market_backed:
            conf = 0.68
            evidence = "market-derived proxy"
        else:
            conf = 0.25
            evidence = "proxy / dedicated domain feed required"
        rows.append({
            "Domain": domain, "Score": score, "Confidence": conf,
            "Segments": len(segments), "Evidence": evidence,
        })
    return pd.DataFrame(rows).set_index("Domain")


def fusion_score(domain_df: pd.DataFrame) -> Dict[str, float]:
    w = domain_df["Confidence"].clip(lower=0.05)
    score = float(np.average(domain_df["Score"], weights=w))
    confidence = float(np.average(domain_df["Confidence"], weights=np.ones(len(domain_df))))
    breadth = float(domain_df["Score"].between(0.4, 0.6).mean())
    return {"score": score, "confidence": confidence, "neutral_breadth": breadth}


def stress_propagation(domain_df: pd.DataFrame, regime_name: str) -> pd.DataFrame:
    direction = -1 if regime_name == "risk_off" else (1 if regime_name == "risk_on" else 0)
    out = domain_df.copy()
    # Uncertainty is higher when evidence confidence is low.
    out["Stress sensitivity"] = (0.5 + (0.5 - out["Score"]).abs() + (1 - out["Confidence"]) * 0.25).clip(0, 1)
    out["Scenario score"] = (out["Score"] + direction * 0.08 * out["Stress sensitivity"]).clip(0, 1)
    out["Priority"] = pd.cut(out["Stress sensitivity"], [-np.inf, .45, .65, np.inf], labels=["Low", "Medium", "High"])
    return out.sort_values("Stress sensitivity", ascending=False)


def strategic_actions(regime_name: str, risk_tolerance: float, port_vol: float, global_score: float) -> List[str]:
    actions: List[str] = []
    if regime_name == "risk_off":
        actions += ["Kockázatcsökkentés és likviditás elsődleges; új kitettséget fokozatosan kezelj.",
                    "Vizsgáld a koncentrációt és a magas korrelációjú kitettségeket."]
    elif regime_name == "risk_on":
        actions += ["Pozícióépítés csak a kockázati mandátumon belül, fokozatosan.",
                    "Trendkitettség növelhető, de veszteséglimit és diverzifikáció maradjon."]
    else:
        actions.append("Átmeneti/semleges környezetben a diverzifikáció és a fokozatos allokáció a prioritás.")
    if np.isfinite(port_vol) and port_vol > risk_tolerance / 100:
        actions.append("A referencia-portfólió becsült volatilitása meghaladja a megadott toleranciát.")
    if global_score < 0.40:
        actions.append("A globális fúziós pontszám gyenge: stresszteszt és likviditási tartalék indokolt.")
    elif global_score > 0.60:
        actions.append("A globális fúziós pontszám támogató, de a domain-bizonyosságot külön kell ellenőrizni.")
    actions.append("A szcenáriók relatív érzékenységi tesztek; nem determinisztikus jövőbeli előrejelzések.")
    return actions


# ------------------------ Validation / model governance ----------------------

CONNECTOR_REGISTRY = pd.DataFrame([
    {"connector": "Yahoo Finance", "domain": "Markets", "auth": "Usually none", "cadence": "daily", "status": "implemented", "limitations": "Third-party feed; terms/coverage can change"},
    {"connector": "World Bank Indicators", "domain": "Economy / Population", "auth": "none", "cadence": "annual / mixed", "status": "implemented", "limitations": "Release lags; indicator definitions differ"},
    {"connector": "FRED", "domain": "Macro / Rates", "auth": "API key", "cadence": "series-dependent", "status": "implemented", "limitations": "US-heavy; each series has its own units/frequency"},
    {"connector": "Open-Meteo", "domain": "Weather", "auth": "Depends on product/usage", "cadence": "daily / forecast", "status": "implemented", "limitations": "Point forecasts are not global climate measurements"},
    {"connector": "CSV import", "domain": "User-defined", "auth": "user supplied", "cadence": "user-defined", "status": "implemented", "limitations": "User must validate semantics, units, geography and revisions"},
    {"connector": "FAOSTAT / UN Comtrade / EIA", "domain": "Agriculture / Trade / Energy", "auth": "varies", "cadence": "varies", "status": "planned adapter", "limitations": "Not claimed as connected in this build"},
])


def validate_frame(frame: pd.DataFrame) -> Dict[str, Any]:
    """Structural quality checks; does not infer semantic correctness."""
    if frame is None or not isinstance(frame, pd.DataFrame) or frame.empty:
        return {"ok": False, "rows": 0, "columns": 0, "missing_ratio": 1.0,
                "duplicate_timestamps": 0, "non_numeric_columns": [], "issues": ["empty_or_invalid_frame"]}
    x = frame.copy()
    idx = pd.to_datetime(x.index, errors="coerce", utc=True)
    duplicate_count = int(idx.duplicated().sum())
    numeric = x.apply(pd.to_numeric, errors="coerce")
    non_numeric = [str(c) for c in x.columns if numeric[c].notna().sum() == 0]
    finite = numeric.replace([np.inf, -np.inf], np.nan)
    missing = float(finite.isna().mean().mean()) if finite.size else 1.0
    issues = []
    if idx.isna().any(): issues.append("invalid_timestamps")
    if duplicate_count: issues.append("duplicate_timestamps")
    if non_numeric: issues.append("non_numeric_or_empty_columns")
    if missing > 0.25: issues.append("high_missingness")
    if not np.isfinite(finite.to_numpy(dtype=float, na_value=np.nan)).any(): issues.append("no_finite_numeric_values")
    return {"ok": not issues, "rows": int(len(x)), "columns": int(x.shape[1]),
            "missing_ratio": missing, "duplicate_timestamps": duplicate_count,
            "non_numeric_columns": non_numeric, "issues": issues}


def walk_forward_backtest(R: pd.DataFrame, lookback: int = 126,
                          rebalance_every: int = 21, ann: int = 252) -> pd.DataFrame:
    """Leakage-aware rolling inverse-vol baseline versus equal-weight benchmark.

    Weights are recalculated every `rebalance_every` observations using only
    data strictly before the rebalance date, then applied to each out-of-sample
    observation until the next rebalance. This is a diagnostic, not a predictive
    model or proof of investment edge.
    """
    if R is None or R.empty or lookback < 20 or rebalance_every < 1:
        return pd.DataFrame(columns=["date", "strategy_return", "benchmark_return", "drawdown"])
    x = R.sort_index().replace([np.inf, -np.inf], np.nan)
    strategy, benchmark, dates = [], [], []
    active_weights = None
    for t in range(lookback, len(x)):
        if active_weights is None or (t - lookback) % rebalance_every == 0:
            train = x.iloc[max(0, t-lookback):t]
            valid_cols = train.columns[train.count() >= 20]
            vol = train[valid_cols].std(ddof=1).replace(0, np.nan)
            inv = (1.0 / vol).replace([np.inf, -np.inf], np.nan).dropna()
            if inv.empty:
                active_weights = None
                continue
            active_weights = inv / inv.sum()
        row = x.iloc[t]
        valid = row.reindex(active_weights.index).dropna()
        if len(valid) == 0:
            continue
        w = active_weights.reindex(valid.index).fillna(0.0)
        if not np.isfinite(w.sum()) or w.sum() <= 0:
            continue
        w = w / w.sum()
        strategy.append(float((valid * w).sum()))
        benchmark.append(float(valid.mean()))
        dates.append(x.index[t])
    if not dates:
        return pd.DataFrame(columns=["date", "strategy_return", "benchmark_return", "drawdown"])
    out = pd.DataFrame({"strategy_return": strategy, "benchmark_return": benchmark}, index=pd.DatetimeIndex(dates))
    wealth = np.exp(out["strategy_return"].cumsum())
    out["drawdown"] = wealth / wealth.cummax() - 1.0
    out.index.name = "date"
    return out.reset_index()


def backtest_summary(bt: pd.DataFrame, ann: int = 252) -> Dict[str, float]:
    if bt is None or bt.empty or len(bt) < 2:
        return {"strategy_ann_return": np.nan, "benchmark_ann_return": np.nan,
                "strategy_ann_vol": np.nan, "strategy_max_drawdown": np.nan, "observations": 0}
    sr = pd.Series(bt["strategy_return"].to_numpy(dtype=float))
    br = pd.Series(bt["benchmark_return"].to_numpy(dtype=float))
    return {"strategy_ann_return": annual_return(sr, ann),
            "benchmark_ann_return": annual_return(br, ann),
            "strategy_ann_vol": annual_vol(sr, ann),
            "strategy_max_drawdown": float(bt["drawdown"].min()),
            "observations": int(len(bt))}


def model_governance(reg: Dict[str, Any], domain_df: pd.DataFrame, hub: GlobalDataHub,
                     prices: pd.DataFrame) -> pd.DataFrame:
    """Machine-readable run manifest and explicit caveats."""
    quality = hub.quality_report()
    low_conf = int((domain_df["Confidence"] < 0.5).sum()) if not domain_df.empty else 0
    latest = prices.index.max() if prices is not None and not prices.empty else pd.NaT
    return pd.DataFrame([
        {"check": "run_timestamp_utc", "value": UTC_NOW().isoformat(), "status": "info"},
        {"check": "market_latest_timestamp", "value": str(latest), "status": "info"},
        {"check": "market_columns", "value": int(prices.shape[1]) if prices is not None else 0, "status": "info"},
        {"check": "market_rows", "value": int(prices.shape[0]) if prices is not None else 0, "status": "info"},
        {"check": "regime", "value": reg.get("name", "unknown"), "status": "diagnostic_only"},
        {"check": "datasets_loaded", "value": int(len(quality)), "status": "info"},
        {"check": "low_confidence_domains", "value": low_conf, "status": "warning" if low_conf else "ok"},
        {"check": "causality_claim", "value": "none", "status": "guardrail"},
        {"check": "financial_advice", "value": "not provided", "status": "guardrail"},
        {"check": "walk_forward", "value": "available as diagnostic; not proof of predictive edge", "status": "guardrail"},
    ])


# ----------------------------- UI -------------------------------------------

def run_app() -> None:
    if st is None:
        raise RuntimeError("A Streamlit nincs telepítve.")
    st.set_page_config(page_title=f"GUME v{APP_VERSION} – Global Intelligence", page_icon="🌐", layout="wide")
    st.title(f"🌐 GUME v{APP_VERSION} – Global Intelligence Engine")
    st.caption("Piac + makro + időjárás + adatfabrika + kockázat + domain-fúzió. Kutatási/döntéstámogató rendszer, nem befektetési tanácsadás.")

    with st.sidebar:
        st.header("1. Piaci réteg")
        ticker_text = st.text_input("Tickerek", "SPY, QQQ, GLD, BTC-USD, EURUSD=X")
        period = st.selectbox("Piaci periódus", ["1y", "2y", "5y", "10y", "max"], index=2)
        ann = st.selectbox("Évesítés", [252, 365], index=0)
        risk_tol = st.slider("Kockázati tolerancia (% éves vol)", 5, 60, 15)
        lookback = st.slider("Rezsim lookback (nap)", 126, 756, 504, step=63)
        mc_paths = st.slider("Monte Carlo utak", 1000, 20000, 5000, step=1000)

        st.header("2. Külső adatkapcsolók")
        wb_country = st.text_input("World Bank országkód", "HUN").strip().upper()
        fred_key = st.text_input("FRED API key (opcionális)", type="password", value=os.getenv("FRED_API_KEY", ""))
        use_wb = st.checkbox("World Bank makro", value=True)
        use_fred = st.checkbox("FRED", value=False)
        use_weather = st.checkbox("Open-Meteo", value=True)
        lat = st.number_input("Időjárás szélesség", value=47.4979, format="%.4f")
        lon = st.number_input("Időjárás hosszúság", value=19.0402, format="%.4f")
        run = st.button("🚀 GUME futtatása", type="primary", use_container_width=True)

        st.header("3. További adat")
        uploaded = st.file_uploader("CSV (date + numerikus oszlopok)", type=["csv"])

    tickers = normalize_tickers(ticker_text)
    if not tickers:
        st.error("Adj meg legalább egy tickert.")
        return

    key = (tickers, period, ann, lookback, wb_country, bool(use_wb), bool(use_fred), bool(use_weather), float(lat), float(lon), bool(uploaded))
    if run or st.session_state.get("gume_key") != key:
        with st.spinner("GUME adat- és modellréteg fut..."):
            prices = download_market_prices(tickers, period)
        st.session_state.gume_key = key
        st.session_state.gume_prices = prices
    else:
        prices = st.session_state.get("gume_prices", pd.DataFrame())

    if prices.empty:
        st.error("Nem érkezett használható árfolyamadat. Ellenőrizd a tickerneveket és az internetkapcsolatot.")
        return

    R_all = log_returns(prices)
    R = R_all.tail(min(lookback, len(R_all)))
    valid_cols = [c for c in R.columns if R[c].count() >= 30]
    R = R[valid_cols]
    prices = prices[valid_cols]
    if R.empty:
        st.error("Nincs legalább 30 megfigyeléssel rendelkező eszköz.")
        return

    hub = GlobalDataHub()
    for c in prices.columns:
        quality = 1.0 if R[c].notna().mean() > 0.98 else 0.80
        hub.add_frame(c, prices[[c]], DataMeta(c, "Yahoo Finance", "market", "price", "global", "market", "daily", quality,
                                                retrieved_at=UTC_NOW().isoformat()))

    connector_errors: List[str] = []
    if use_wb:
        for short, (code, label) in WORLD_BANK_MAP.items():
            res = fetch_world_bank_indicator(wb_country, code, label)
            if res.frame.empty:
                connector_errors.append(f"World Bank / {label}: {res.error}")
            else:
                hub.add_frame(f"WB:{short}", res.frame, res.meta)

    if use_fred:
        fred_map = {"FRED:fedfunds": ("FEDFUNDS", "Fed funds rate"), "FRED:cpi": ("CPIAUCSL", "CPI"), "FRED:unrate": ("UNRATE", "Unemployment rate")}
        for name, (sid, label) in fred_map.items():
            res = fetch_fred_series(sid, fred_key, label)
            if res.frame.empty:
                connector_errors.append(f"{name}: {res.error}")
            else:
                hub.add_frame(name, res.frame, res.meta)

    if use_weather:
        res = fetch_open_meteo(float(lat), float(lon))
        if res.frame.empty:
            connector_errors.append(f"Open-Meteo: {res.error}")
        else:
            hub.add_frame("Weather", res.frame, res.meta)

    if uploaded is not None:
        res = parse_uploaded_csv(uploaded.getvalue(), "Uploaded CSV")
        if res.frame.empty:
            connector_errors.append(f"CSV: {res.error}")
        else:
            hub.add_frame("Uploaded CSV", res.frame, res.meta)

    weights = pd.Series(1 / len(R.columns), index=R.columns)
    pr = portfolio_returns(R, weights)
    port_vol = annual_vol(pr, ann)
    reg = regime_engine(R, ann)

    st.subheader("1. Piaci állapot")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rezsim", str(reg["name"]).upper())
    c2.metric("Trend", f"{reg['trend']:.2%}" if np.isfinite(reg["trend"]) else "n/a")
    c3.metric("Vol-ráta", f"{reg['vol_ratio']:.2f}" if np.isfinite(reg["vol_ratio"]) else "n/a")
    c4.metric("Stress", f"{reg['stress']:.3f}" if np.isfinite(reg["stress"]) else "n/a")
    st.info("A rezsim trend + rövid/hosszú volatilitás proxy. Nem HMM, nem oksági modell, és nem garantálja a jövőbeli rezsimet.")

    st.subheader("2. Kvantitatív kockázati mátrix")
    rows = []
    for col in R.columns:
        x = R[col].dropna()
        q, cv = var_cvar(x)
        rows.append({"Eszköz": col, "Éves hozam": annual_return(x, ann), "Éves vol": annual_vol(x, ann),
                     "Downside vol": downside_vol(x, ann), "Sharpe": sharpe(x, ann), "Sortino": sortino(x, ann),
                     "Max DD": max_drawdown(x), "VaR95 (1d log)": q, "CVaR95 (1d log)": cv})
    metrics = pd.DataFrame(rows).set_index("Eszköz")
    st.dataframe(metrics.style.format({"Éves hozam": "{:.2%}", "Éves vol": "{:.2%}", "Downside vol": "{:.2%}",
                                        "Sharpe": "{:.2f}", "Sortino": "{:.2f}", "Max DD": "{:.2%}",
                                        "VaR95 (1d log)": "{:.2%}", "CVaR95 (1d log)": "{:.2%}"}), use_container_width=True)

    st.subheader("3. Korreláció és referencia-portfólió")
    st.dataframe(R.corr().style.format("{:.2f}"), use_container_width=True)
    p_return = annual_return(pr, ann)
    p_sharpe = sharpe(pr, ann)
    p_dd = max_drawdown(pr)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ref. éves hozam", f"{p_return:.2%}")
    c2.metric("Ref. éves vol", f"{port_vol:.2%}")
    c3.metric("Ref. Sharpe", f"{p_sharpe:.2f}")
    c4.metric("Ref. max DD", f"{p_dd:.2%}")

    st.subheader("4. Monte Carlo")
    q, cv = monte_carlo_student_t(pr, mc_paths, 21)
    c1, c2, c3 = st.columns(3)
    c1.metric("Horizont", "21 nap")
    c2.metric("MC VaR 95% (log)", f"{q:.2%}" if np.isfinite(q) else "n/a")
    c3.metric("MC CVaR 95% (log)", f"{cv:.2%}" if np.isfinite(cv) else "n/a")
    st.caption("Student-t i.i.d. referencia-szimuláció; nem regime-conditioned, nem útfüggő makromodell.")

    st.subheader("5. Stressz-szcenárió")
    st.dataframe(stress_matrix(R, str(reg["name"])).style.format("{:.2%}"), use_container_width=True)
    st.caption("Relatív érzékenységi stressz; nem árfolyam- vagy makrogazdasági előrejelzés.")

    st.subheader("6. Walk-forward baseline diagnostic")
    bt = walk_forward_backtest(R, lookback=min(126, max(20, len(R) // 2)), rebalance_every=21, ann=ann)
    bts = backtest_summary(bt, ann)
    b1, b2, b3, b4 = st.columns(4)
    b1.metric("Baseline annualized return", f"{bts['strategy_ann_return']:.2%}" if np.isfinite(bts['strategy_ann_return']) else "n/a")
    b2.metric("Equal-weight benchmark", f"{bts['benchmark_ann_return']:.2%}" if np.isfinite(bts['benchmark_ann_return']) else "n/a")
    b3.metric("Baseline annualized vol", f"{bts['strategy_ann_vol']:.2%}" if np.isfinite(bts['strategy_ann_vol']) else "n/a")
    b4.metric("Out-of-sample observations", str(bts["observations"]))
    if not bt.empty:
        st.line_chart(bt.set_index("date")[["strategy_return", "benchmark_return"]].cumsum())
        st.dataframe(bt.tail(100), use_container_width=True)
        st.download_button("⬇️ Walk-forward CSV", bt.to_csv(index=False).encode("utf-8"), "gume_v6_6_walk_forward.csv", "text/csv")
    st.caption("A súlyok kizárólag az adott időpont előtti ablakból készülnek. A baseline egyszerű inverz-volatilitás; az eredmény diagnosztika, nem előrejelzés vagy befektetési ajánlás.")

    st.subheader("7. Global Data Fabric")
    quality = hub.quality_report()
    st.dataframe(quality.style.format({"age_days": "{:.1f}", "missing_ratio": "{:.2%}", "freshness": "{:.2%}", "quality_score": "{:.2%}"}), use_container_width=True)
    if connector_errors:
        with st.expander("Connector hibák / hiányok", expanded=False):
            for err in connector_errors:
                st.warning(err)

    domain_df = build_domain_scores(R, reg, hub)
    fusion = fusion_score(domain_df)
    st.divider()
    st.header("🌍 7. Global Intelligence Fusion")
    a, b, c = st.columns(3)
    a.metric("Global GUME Score", f"{fusion['score']:.1%}")
    b.metric("Fusion confidence", f"{fusion['confidence']:.1%}")
    c.metric("Neutral domain breadth", f"{fusion['neutral_breadth']:.1%}")

    st.dataframe(domain_df.style.format({"Score": "{:.1%}", "Confidence": "{:.1%}"}), use_container_width=True)
    prop = stress_propagation(domain_df, str(reg["name"]))
    st.subheader("9. Domain stress propagation")
    st.dataframe(prop.style.format({"Score": "{:.1%}", "Confidence": "{:.1%}", "Stress sensitivity": "{:.1%}", "Scenario score": "{:.1%}"}), use_container_width=True)

    st.subheader("10. Global decision layer")
    if fusion["score"] < 0.40:
        st.error("DEFENSIVE — gyenge / stresszes globális összkép.")
    elif fusion["score"] > 0.60:
        st.success("EXPANSIVE — támogató globális összkép.")
    else:
        st.warning("TRANSITION — vegyes / átmeneti környezet.")
    for action in strategic_actions(str(reg["name"]), risk_tol, port_vol, fusion["score"]):
        st.write("• " + action)

    st.subheader("11. Provenance / model governance")
    st.write("A rendszer nem nevezi valódi mérésnek a hiányzó domaineket. A piaci proxy, külső API-adat és felhasználói CSV külön státuszt kap.")
    st.dataframe(hub.catalog(), use_container_width=True)
    st.subheader("Connector registry")
    st.dataframe(CONNECTOR_REGISTRY, use_container_width=True)
    st.subheader("Run manifest / governance checks")
    governance = model_governance(reg, domain_df, hub, prices)
    st.dataframe(governance, use_container_width=True)

    report = metrics.copy()
    report["ref_weight"] = 1 / len(report)
    report_csv = report.to_csv().encode("utf-8")
    st.download_button("⬇️ Kvantitatív CSV", report_csv, "gume_v6_6_quant_report.csv", "text/csv")
    st.download_button("⬇️ Data Fabric CSV", quality.to_csv(index=False).encode("utf-8"), "gume_v6_6_data_fabric.csv", "text/csv")
    st.download_button("⬇️ Domain Intelligence CSV", domain_df.to_csv().encode("utf-8"), "gume_v6_6_domain_intelligence.csv", "text/csv")

    with st.expander("Források és módszertani korlátok"):
        st.markdown(
            "- Yahoo Finance/yfinance: piaci árfolyamok.\n"
            "- World Bank Indicators API: országos éves makroindikátorok.\n"
            "- FRED: opcionális, API-kulcsos makroadatok.\n"
            "- Open-Meteo: opcionális időjárási idősor.\n"
            "- CSV: bármely további adatforrás, amelynek szemantikáját a felhasználó ellenőrzi.\n"
            "- A Climate, Geopolitics, Politics, Agriculture, AI, Quantum stb. domainjei nem kapnak hamis pontosságot: dedicated feed nélkül proxy/low-confidence állapotban maradnak.\n"
            "- A rendszer nem használja a 4D/spacetime fogalmakat fizikai törvények bizonyítására; ezek csak strukturális domain-címkék."
        )


if __name__ == "__main__":
    run_app()
