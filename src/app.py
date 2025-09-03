import os, json
import pandas as pd
import streamlit as st
import altair as alt

st.set_page_config(page_title="Smart Fan SoV Dashboard", layout="wide")

st.title("Smart Fan Share-of-Voice (SoV) Dashboard")

# ----------------- Load -----------------
def load_json(path):
    return json.load(open(path)) if os.path.exists(path) else None

def load_csv(path):
    return pd.read_csv(path) if os.path.exists(path) else pd.DataFrame()

summary = load_json("out/summary.json")
scored = load_csv("out/scored.csv")
brand_summary = load_csv("out/brand_summary.csv")

if summary is None or scored.empty:
    st.error(" No analysis results found. Run `python src/analyze.py` first.")
    st.stop()

brands = summary["brands"]

# ----------------- Raw Items -----------------
st.subheader("Raw Data Preview")
st.dataframe(scored.head(20))

# ----------------- Mentions -----------------
st.subheader("1️. Mentions (Raw Mention Share)")
df_rms = pd.DataFrame(summary["rms"]["share"].items(), columns=["brand", "share"])
col1, col2 = st.columns(2)
with col1:
    st.altair_chart(
        alt.Chart(df_rms).mark_bar().encode(
            x="brand",
            y=alt.Y("share:Q", axis=alt.Axis(format='%')),
            tooltip=["brand", alt.Tooltip("share:Q", format=".1%")]
        ),
        use_container_width=True
    )
with col2:
    st.altair_chart(
        alt.Chart(df_rms).mark_arc(innerRadius=50).encode(
            theta="share",
            color="brand",
            tooltip=["brand", alt.Tooltip("share:Q", format=".1%")]
        ),
        use_container_width=True
    )

# ----------------- Engagement -----------------
st.subheader("2️. Engagement vs Weighted SoV")
df_wsov = pd.DataFrame(summary["wsov"]["share"].items(), columns=["brand", "share"])
df_eng = scored.groupby("dominant_brand")["engagement"].sum().reset_index()
df_eng.columns = ["brand", "total_engagement"]

col1, col2 = st.columns(2)
with col1:
    st.markdown("**Weighted SoV (wSoV)**")
    st.altair_chart(
        alt.Chart(df_wsov).mark_bar().encode(
            x="brand",
            y=alt.Y("share:Q", axis=alt.Axis(format='%')),
            tooltip=["brand", alt.Tooltip("share:Q", format=".1%")]
        ),
        use_container_width=True
    )
with col2:
    st.markdown("**Total Engagement per Brand**")
    st.altair_chart(
        alt.Chart(df_eng).mark_bar().encode(
            x="brand",
            y="total_engagement",
            tooltip=["brand", "total_engagement"]
        ),
        use_container_width=True
    )

# ----------------- Sentiment -----------------
st.subheader("3️. Sentiment Breakdown per Brand")
sent = summary["sentiment_breakdown"]
rows = []
for b, vals in sent.items():
    for lab, c in vals.items():
        rows.append({"brand": b, "sentiment": lab, "count": c})
df_sent = pd.DataFrame(rows)
chart = alt.Chart(df_sent).mark_bar().encode(
    x="brand:N",
    y="count:Q",
    color="sentiment:N",
    tooltip=["brand", "sentiment", "count"]
)
st.altair_chart(chart, use_container_width=True)

# ----------------- SoPV -----------------
st.subheader("4️. Share of Positive Voice (SoPV)")
df_sopv = pd.DataFrame(summary["sopv"]["share"].items(), columns=["brand", "share"])
st.altair_chart(
    alt.Chart(df_sopv).mark_bar().encode(
        x="brand",
        y=alt.Y("share:Q", axis=alt.Axis(format='%')),
        tooltip=["brand", alt.Tooltip("share:Q", format=".1%")]
    ),
    use_container_width=True
)

# ----------------- Timeline -----------------
if "published_at" in scored.columns:
    st.subheader("5️. Timeline of Mentions")
    scored["published_at"] = pd.to_datetime(scored["published_at"], errors="coerce")
    df_time = (
        scored.dropna(subset=["published_at"])
        .groupby([pd.Grouper(key="published_at", freq="M"), "dominant_brand"])
        .size().reset_index(name="count")
    )
    if not df_time.empty:
        st.altair_chart(
            alt.Chart(df_time).mark_line(point=True).encode(
                x="published_at:T",
                y="count:Q",
                color="dominant_brand:N",
                tooltip=["published_at", "dominant_brand", "count"]
            ),
            use_container_width=True
        )

# ----------------- Heatmap -----------------
st.subheader("6️. Brand × Platform Presence")
df_heat = scored.groupby(["platform", "dominant_brand"]).size().reset_index(name="count")
heat = alt.Chart(df_heat).mark_rect().encode(
    x="platform:N",
    y="dominant_brand:N",
    color="count:Q",
    tooltip=["platform", "dominant_brand", "count"]
)
st.altair_chart(heat, use_container_width=True)

# ----------------- Top Publishers -----------------
st.subheader("7️. Top Publishers")
st.dataframe(pd.DataFrame(summary["top_publishers"]))

# ----------------- Executive Summary -----------------
st.subheader("Executive Summary")
st.write(f"""
**Dataset Size:** {summary['total_items']} items analyzed  
**Brands Covered:** {', '.join(summary['brands'])}  

- **Mentions (RMS):** Shows how often each brand is visible in search results.  
- **Engagement & wSoV:** Captures how strongly audiences interact with each brand’s content, weighted by sentiment.  
- **Sentiment Breakdown:** Classifies brand mentions as positive, neutral, or negative.  
- **SoPV:** Focuses only on positive sentiment share.  
- **Timeline:** Displays how brand visibility evolves over time.  
- **Heatmap:** Highlights which platforms (YouTube, Google) dominate for each brand.  
- **Top Publishers:** Identifies the key sites/channels driving visibility.  

This dashboard provides a single-view snapshot of **Atomberg vs competitors in Smart Fan Share-of-Voice**, allowing decision-makers to understand brand strength, engagement quality, sentiment tone, and market position at a glance.
""")
