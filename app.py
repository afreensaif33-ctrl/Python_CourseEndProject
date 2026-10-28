import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Rural Essential-Service Accessibility Analyzer", page_icon="🏡", layout="wide")

REQUIRED_COLUMNS = [
    "district", "village", "service_type", "facility_name",
    "distance_km", "travel_time_min", "available", "population", "period"
]
SERVICE_TYPES = ["Healthcare", "Banking", "Transport", "Education", "Other"]

st.title("🏡 Rural Essential-Service Accessibility Analyzer")
st.caption("Analyze service availability, identify underserved villages, compare service categories, and generate practical recommendations.")

with st.sidebar:
    st.header("Analysis settings")
    max_distance = st.slider("Maximum acceptable distance (km)", 1.0, 30.0, 5.0, 0.5)
    max_travel_time = st.slider("Maximum acceptable travel time (minutes)", 10, 120, 30, 5)
    st.markdown("---")
    st.write("**Expected data columns**")
    st.code(", ".join(REQUIRED_COLUMNS), language="text")
    st.caption("Use the included sample CSV to test the dashboard. Sample values are illustrative, not official statistics.")

@st.cache_data
def load_demo_data():
    path = Path(__file__).parent / "data" / "sample_rural_services.csv"
    return pd.read_csv(path)

def clean_data(df):
    """Normalize column names and validate/clean values used by the analysis."""
    data = df.copy()
    data.columns = [str(c).strip().lower().replace(" ", "_") for c in data.columns]
    missing = [c for c in REQUIRED_COLUMNS if c not in data.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))

    data = data[REQUIRED_COLUMNS].copy()
    for col in ["district", "village", "service_type", "facility_name", "period"]:
        data[col] = data[col].astype("string").str.strip()
        data[col] = data[col].replace("", pd.NA)

    for col in ["distance_km", "travel_time_min", "population"]:
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data["available"] = (
        data["available"].astype("string").str.strip().str.lower()
        .map({"yes": True, "y": True, "true": True, "1": True,
              "available": True, "no": False, "n": False, "false": False,
              "0": False, "unavailable": False})
    )

    data = data.dropna(subset=["district", "village", "service_type", "available"])
    data["distance_km"] = data["distance_km"].clip(lower=0)
    data["travel_time_min"] = data["travel_time_min"].clip(lower=0)
    data["population"] = data["population"].clip(lower=0)
    data["service_type"] = data["service_type"].str.title()
    data["period"] = data["period"].fillna("Unspecified")
    data["facility_name"] = data["facility_name"].fillna("Not specified")
    return data

def add_access_flags(data, distance_limit, time_limit):
    result = data.copy()
    result["within_distance"] = result["distance_km"].le(distance_limit)
    result["within_travel_time"] = result["travel_time_min"].le(time_limit)
    result["accessible"] = (
        result["available"] &
        result["within_distance"].fillna(False) &
        result["within_travel_time"].fillna(False)
    )
    result["access_status"] = result["accessible"].map({True: "Accessible", False: "Needs attention"})
    return result

def build_village_summary(data):
    summary = (data.groupby(["district", "village"], dropna=False)
        .agg(
            population=("population", "max"),
            services_recorded=("service_type", "nunique"),
            available_services=("accessible", "sum"),
            mean_distance_km=("distance_km", "mean"),
            mean_travel_time_min=("travel_time_min", "mean"),
            service_records=("service_type", "size")
        ).reset_index())
    summary["availability_pct"] = (
        summary["available_services"] / summary["service_records"].replace(0, pd.NA) * 100
    ).fillna(0).round(1)
    summary["priority"] = summary.apply(
        lambda r: "High" if r["availability_pct"] < 40 else ("Medium" if r["availability_pct"] < 70 else "Low"),
        axis=1
    )
    return summary.sort_values(["availability_pct", "mean_travel_time_min"], ascending=[True, False])

def make_recommendations(village_summary, service_summary, distance_limit, time_limit):
    recommendations = []
    high_priority = village_summary[village_summary["priority"] == "High"]
    if not high_priority.empty:
        names = ", ".join(high_priority["village"].astype(str).head(5).tolist())
        recommendations.append(
            f"Prioritize a field assessment in {names}. These villages have less than 40% accessible service records in the current dataset."
        )
    far = village_summary[village_summary["mean_distance_km"] > distance_limit]
    if not far.empty:
        recommendations.append(
            f"Review transport links or mobile/periodic service delivery for {len(far)} villages whose average service distance exceeds {distance_limit:g} km."
        )
    slow = village_summary[village_summary["mean_travel_time_min"] > time_limit]
    if not slow.empty:
        recommendations.append(
            f"Investigate road conditions, routes, and public transport for {len(slow)} villages with average travel time above {time_limit} minutes."
        )
    if not service_summary.empty:
        weakest = service_summary.sort_values("accessibility_pct").iloc[0]
        recommendations.append(
            f"Service category needing the most attention: {weakest['service_type']} ({weakest['accessibility_pct']:.1f}% accessible records). Consider targeted facility placement, outreach, or service-day scheduling."
        )
    if not recommendations:
        recommendations.append("No major gaps were detected using the selected thresholds. Validate the records with local officials and community representatives before making decisions.")
    recommendations.append("Treat these findings as a screening tool, not proof that a facility is operational or that every resident can use it. Confirm facility hours, capacity, affordability, disability access, and seasonal road conditions.")
    return recommendations

uploaded = st.file_uploader("Upload your rural services CSV (optional)", type=["csv"])
if uploaded:
    try:
        raw = pd.read_csv(uploaded)
        source_label = uploaded.name
    except Exception as exc:
        st.error(f"Could not read this CSV: {exc}")
        st.stop()
else:
    raw = load_demo_data()
    source_label = "Built-in illustrative sample data"

try:
    cleaned = clean_data(raw)
except ValueError as exc:
    st.error(str(exc))
    st.info("Your CSV must contain all required columns listed in the sidebar. See README.md for the data dictionary.")
    st.stop()

if cleaned.empty:
    st.error("No usable records remain after cleaning. Check village, district, service type, and available values.")
    st.stop()

data = add_access_flags(cleaned, max_distance, max_travel_time)

with st.expander("Data quality report", expanded=False):
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows uploaded", len(raw))
    c2.metric("Rows retained", len(cleaned))
    c3.metric("Rows removed", len(raw) - len(cleaned))
    st.write("Cleaned data preview")
    st.dataframe(data, use_container_width=True)

districts = sorted(data["district"].dropna().unique().tolist())
services = sorted(data["service_type"].dropna().unique().tolist())
periods = sorted(data["period"].dropna().unique().tolist())
f1, f2, f3 = st.columns(3)
with f1:
    chosen_districts = st.multiselect("District", districts, default=districts)
with f2:
    chosen_services = st.multiselect("Service category", services, default=services)
with f3:
    chosen_periods = st.multiselect("Period", periods, default=periods)

filtered = data[
    data["district"].isin(chosen_districts) &
    data["service_type"].isin(chosen_services) &
    data["period"].isin(chosen_periods)
].copy()

if filtered.empty:
    st.warning("No records match these filters. Select at least one district, service category, and period.")
    st.stop()

accessible_pct = filtered["accessible"].mean() * 100
availability_pct = filtered["available"].mean() * 100
village_count = filtered["village"].nunique()
high_distance_count = filtered.loc[filtered["distance_km"] > max_distance, "village"].nunique()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Villages covered", f"{village_count:,}")
k2.metric("Accessible service records", f"{accessible_pct:.1f}%")
k3.metric("Facilities marked available", f"{availability_pct:.1f}%")
k4.metric("Villages with long-distance records", f"{high_distance_count:,}")

st.subheader("Service accessibility comparison")
service_summary = (filtered.groupby("service_type")
    .agg(total_records=("accessible", "size"),
         accessible_records=("accessible", "sum"),
         availability_pct=("available", lambda x: x.mean() * 100),
         accessibility_pct=("accessible", lambda x: x.mean() * 100),
         avg_distance_km=("distance_km", "mean"),
         avg_travel_time_min=("travel_time_min", "mean"))
    .reset_index())
service_summary[["availability_pct", "accessibility_pct", "avg_distance_km", "avg_travel_time_min"]] = service_summary[
    ["availability_pct", "accessibility_pct", "avg_distance_km", "avg_travel_time_min"]
].round(1)

left, right = st.columns(2)
with left:
    fig = px.bar(service_summary, x="service_type", y="accessibility_pct",
                 color="service_type", range_y=[0, 100],
                 labels={"service_type": "Service category", "accessibility_pct": "Accessible records (%)"},
                 title="Accessibility by service category")
    st.plotly_chart(fig, use_container_width=True)
with right:
    fig = px.bar(service_summary, x="service_type", y="avg_distance_km",
                 color="service_type",
                 labels={"service_type": "Service category", "avg_distance_km": "Average distance (km)"},
                 title="Average distance to service")
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Underserved villages")
village_summary = build_village_summary(filtered)
st.caption("Priority is based on the percentage of service records meeting the selected availability, distance, and travel-time thresholds.")
priority_order = pd.Categorical(village_summary["priority"], categories=["High", "Medium", "Low"], ordered=True)
village_summary = village_summary.assign(priority_order=priority_order).sort_values(
    ["priority_order", "availability_pct"], ascending=[True, True]
).drop(columns=["priority_order"])
st.dataframe(village_summary, use_container_width=True, hide_index=True)

fig = px.bar(village_summary.sort_values("availability_pct"), x="village", y="availability_pct",
             color="priority", hover_data=["district", "population", "mean_distance_km", "mean_travel_time_min"],
             range_y=[0, 100], title="Village-level accessible service records",
             labels={"village": "Village", "availability_pct": "Accessibility (%)", "priority": "Priority"})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Compare locations")
location_metric = st.selectbox("Compare districts by", ["Accessibility (%)", "Average distance (km)", "Average travel time (minutes)"])
metric_map = {
    "Accessibility (%)": ("accessible", "mean", 100),
    "Average distance (km)": ("distance_km", "mean", 1),
    "Average travel time (minutes)": ("travel_time_min", "mean", 1)
}
col, agg, multiplier = metric_map[location_metric]
district_summary = filtered.groupby("district")[col].agg(agg).reset_index(name="value")
if location_metric == "Accessibility (%)":
    district_summary["value"] *= multiplier
fig = px.bar(district_summary.sort_values("value"), x="district", y="value", color="district",
             title=f"District comparison: {location_metric}", labels={"value": location_metric, "district": "District"})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Practical recommendations")
for i, recommendation in enumerate(make_recommendations(village_summary, service_summary, max_distance, max_travel_time), 1):
    st.markdown(f"**{i}.** {recommendation}")

st.subheader("Download analysis outputs")
csv1 = service_summary.to_csv(index=False).encode("utf-8")
csv2 = village_summary.to_csv(index=False).encode("utf-8")
c1, c2, c3 = st.columns(3)
c1.download_button("Download cleaned records", data=filtered.to_csv(index=False).encode("utf-8"),
                   file_name="cleaned_rural_services.csv", mime="text/csv")
c2.download_button("Download service summary", data=csv1,
                   file_name="service_accessibility_summary.csv", mime="text/csv")
c3.download_button("Download village priorities", data=csv2,
                   file_name="underserved_villages.csv", mime="text/csv")

st.markdown("---")
st.caption(f"Data source: {source_label} · Thresholds are configurable. Results depend on data completeness and accuracy.")
