from __future__ import annotations

import html

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.core.scoring import urgency_colors, urgency_label
from src.ingestion.pipeline import load_issues


st.set_page_config(page_title="CivicPulse", page_icon="🏙️", layout="wide")


def load_dashboard_data() -> pd.DataFrame:
    frame = load_issues(st.session_state.get("semantic_query") or None)
    if frame.empty:
        return frame
    frame["post_date"] = pd.to_datetime(frame["post_date"])
    frame["traction_date"] = pd.to_datetime(frame["traction_date"])
    return frame


def render_leaflet_map(frame: pd.DataFrame) -> None:
    markers = []
    for issue in frame.to_dict("records"):
        color, background = urgency_colors(float(issue["impact_score"]))
        markers.append(
            {
                "lat": issue["latitude"],
                "lng": issue["longitude"],
                "title": html.escape(issue["title"]),
                "area": html.escape(issue["area"]),
                "zone": html.escape(issue["zone"]),
                "score": issue["impact_score"],
                "color": color,
                "background": background,
            }
        )

    marker_js = "\n".join(
        f"""
        L.circleMarker([{marker["lat"]}, {marker["lng"]}], {{
            radius: 10,
            color: "{marker["color"]}",
            fillColor: "{marker["color"]}",
            fillOpacity: 0.82,
            weight: 2
        }}).bindPopup(`
            <strong>{marker["title"]}</strong><br>
            {marker["area"]} · {marker["zone"]}<br>
            Impact Score: <strong>{marker["score"]}</strong>
        `).addTo(map);
        """
        for marker in markers
    )

    components.html(
        f"""
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
        <div id="map" style="height: 430px; width: 100%; border: 1px solid #D7DEE8;"></div>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        <script>
            const map = L.map('map').setView([17.405, 78.47], 11);
            L.tileLayer('https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap'
            }}).addTo(map);
            {marker_js}
        </script>
        """,
        height=450,
    )


def score_badge(score: float) -> str:
    color, background = urgency_colors(score)
    return (
        f"<span style='background:{background};color:{color};"
        "padding:4px 8px;border-radius:6px;font-weight:700;'>"
        f"{score:.2f} · {urgency_label(score)}</span>"
    )


st.title("CivicPulse")
st.caption("AI-driven civic issue prioritization for Hyderabad GHMC zones")

st.text_input(
    "Vector Search",
    key="semantic_query",
    placeholder="Search by issue, area, category, or urgency signal",
)

df = load_dashboard_data()

if df.empty:
    st.warning("No civic issues found in the vector database.")
    st.stop()

active = len(df)
critical = int((df["impact_score"] >= 8.0).sum())
zones_affected = int(df["zone"].nunique())
resolved = 0

metric_cols = st.columns(4)
metric_cols[0].metric("Active", active)
metric_cols[1].metric("Critical", critical)
metric_cols[2].metric("Zones Affected", zones_affected)
metric_cols[3].metric("Resolved", resolved)

filter_cols = st.columns([1.1, 1.1, 1.2, 1])
category = filter_cols[0].selectbox("Category", ["All", *sorted(df["category"].unique())])
zone = filter_cols[1].selectbox("GHMC Zone", ["All", *sorted(df["zone"].unique())])
sort_by = filter_cols[2].selectbox(
    "Sort By",
    ["Impact Score", "Post Date", "Peak Traction Date"],
)
direction = filter_cols[3].selectbox("Direction", ["Descending", "Ascending"])

filtered = df.copy()
if category != "All":
    filtered = filtered[filtered["category"] == category]
if zone != "All":
    filtered = filtered[filtered["zone"] == zone]

sort_column = {
    "Impact Score": "impact_score",
    "Post Date": "post_date",
    "Peak Traction Date": "traction_date",
}[sort_by]
filtered = filtered.sort_values(sort_column, ascending=direction == "Ascending")

map_col, trend_col = st.columns([1.35, 1])
with map_col:
    st.subheader("Hyderabad Hotspots")
    render_leaflet_map(filtered)

with trend_col:
    st.subheader("Zone Trend View")
    trend = (
        filtered.groupby(["zone", "category"], as_index=False)
        .size()
        .rename(columns={"size": "reports"})
    )
    st.bar_chart(trend, x="zone", y="reports", color="category")

st.subheader("Prioritized Issue Queue")

display = filtered[
    [
        "id",
        "title",
        "area",
        "zone",
        "category",
        "impact_score",
        "post_date",
        "traction_date",
        "engagement_count",
    ]
].copy()
display["post_date"] = display["post_date"].dt.strftime("%Y-%m-%d")
display["traction_date"] = display["traction_date"].dt.strftime("%Y-%m-%d")
display["impact"] = display["impact_score"].apply(lambda value: score_badge(float(value)))

st.write(
    display[
        [
            "id",
            "title",
            "area",
            "zone",
            "category",
            "impact",
            "post_date",
            "traction_date",
            "engagement_count",
        ]
    ].to_html(escape=False, index=False),
    unsafe_allow_html=True,
)
