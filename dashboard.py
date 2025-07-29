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
col3.metric("Saldo", f"R$ {balance:,.2f}")

# =====================
# GRÁFICOS
# =====================

# Evolução mensal
st.subheader("📈 Evolução Mensal (Receita vs Despesa)")
monthly_summary = df_filtered.groupby(["Month", "Transaction"])["Amount"].sum().reset_index()
fig_line = px.line(monthly_summary, x="Month", y="Amount", color="Transaction",
                   title="Receita e Despesa por Mês", markers=True)
st.plotly_chart(fig_line, use_container_width=True)

# =====================
# NOVO: Gráfico por categoria com seletor de mês
# =====================
st.subheader("📊 Gastos por Categoria (Selecionar Mês)")
month_for_bar = st.selectbox("Selecione um mês para analisar categorias", months)

df_month = df_filtered[(df_filtered["Month"] == month_for_bar) & (df_filtered["Transaction"] == "Expense")]
expenses_by_cat_month = df_month.groupby("Category")["Amount"].sum().reset_index().sort_values("Amount", ascending=False)

fig_bar_month = px.bar(
    expenses_by_cat_month,
    x="Amount",
    y="Category",
    orientation="h",
    title=f"Gastos por Categoria em {month_for_bar}",
    text_auto=True
)
st.plotly_chart(fig_bar_month, use_container_width=True)

# =====================
# Pizza - Receita vs Despesa
# =====================
st.subheader("🥧 Receita vs Despesa")
summary = {"Receita": total_income, "Despesa": total_expenses}
fig_pie = px.pie(names=list(summary.keys()), values=list(summary.values()), title="Receita vs Despesa")
st.plotly_chart(fig_pie, use_container_width=True)

# =====================
# TABELA FILTRADA
# =====================
st.subheader("📄 Detalhes das Transações Filtradas")
st.dataframe(df_filtered.sort_values(by="Date", ascending=False))
