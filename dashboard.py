import streamlit as st
import pandas as pd
import plotly.express as px

# =====================
# CARREGAR OS DADOS
# =====================
@st.cache_data
def load_data():
    df = pd.read_excel("Book1.xlsx")
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)  # Ex: 2025-01
    return df

df = load_data()

# =====================
# SIDEBAR - FILTROS GLOBAIS
# =====================
st.sidebar.header("Filtros")
months = sorted(df["Month"].unique())
selected_months = st.sidebar.multiselect("Selecione os meses", months, default=months)

categories = sorted(df["Category"].unique())
selected_categories = st.sidebar.multiselect("Selecione categorias", categories, default=categories)

transaction_types = sorted(df["Transaction"].unique())
selected_types = st.sidebar.multiselect("Selecione tipo", transaction_types, default=transaction_types)

# Aplicar filtros globais
df_filtered = df[
    (df["Month"].isin(selected_months)) &
    (df["Category"].isin(selected_categories)) &
    (df["Transaction"].isin(selected_types))
]

# =====================
# KPIs
# =====================
total_expenses = df_filtered[df_filtered["Transaction"] == "Expense"]["Amount"].sum()
total_income = df_filtered[df_filtered["Transaction"] == "Income"]["Amount"].sum()
balance = total_income - total_expenses

st.title("📊 Dashboard Financeiro")
st.markdown("Visualização interativa de receitas e despesas")

col1, col2, col3 = st.columns(3)
col1.metric("Total Despesas", f"R$ {total_expenses:,.2f}")
col2.metric("Total Receitas", f"R$ {total_income:,.2f}")
col3.metric("Saldo
