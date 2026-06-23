import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="ECB Churn Index", layout="wide")
st.title("European Banking Churn Analysis")

# Load dataset (bypass Surnames for GDPR compliance)
df = pd.read_csv("dataset.csv").drop(columns=["Surname"])

# Sidebar filter panel
geo = st.sidebar.multiselect("Geography", df["Geography"].unique())

# Filter dataset
filtered_df = df[df["Geography"].isin(geo)] if geo else df

# Render churn bar chart
fig = px.bar(filtered_df, x="NumOfProducts", y="Exited", title="Churn rate vs Products")
st.plotly_chart(fig, use_container_width=True)
