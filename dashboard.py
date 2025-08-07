import streamlit as st
import pandas as pd
import plotly.express as px
import re

# ID da planilha Google Sheets
SPREADSHEET_ID = "1D4xID5FDYYNvpctagqpfIDagt74CeU2K"
SHEET_NAMES = [
    "01_2025", "02_2025", "03_2025", "04_2025", "05_2025",
    "06_2025", "07_2025", "08_2025", "09_2025", "10_2025",
    "11_2025", "12_2025", "Gastos"
]

@st.cache_data(show_spinner=False)
def load_google_sheets_data(sheet_names):
    all_data = []
    for sheet in sheet_names:
        url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet}"
        try:
            df = pd.read_csv(url, header=0, decimal=",")
            df.columns = [str(col).strip().capitalize() for col in df.columns]
            df["source_sheet"] = sheet
            all_data.append(df)
        except Exception as e:
            st.warning(f"Erro ao carregar aba '{sheet}': {e}")
            continue

    if not all_data:
        st.error("Nenhum dado foi carregado das planilhas.")
        st.stop()

    df = pd.concat(all_data, ignore_index=True)

    required_cols = ["Title", "Amount", "Transaction", "Category", "Date"]
    expected_cols = ["Title", "Amount", "Transaction", "Category", "Date", "Parcelas"]
    df = df[[col for col in df.columns if col in expected_cols or col == "source_sheet"]]
    for col in required_cols:
        if col not in df.columns:
            st.error(f"Coluna obrigatória ausente: {col}")
            st.stop()

    if "Parcelas" not in df.columns:
        df["Parcelas"] = "1/1"
    df["Amount"] = pd.to_numeric(df["Amount"], errors="coerce").fillna(0)
    return df

def adjust_installment_dates(df):
    adjusted_rows = []
    for _, row in df.iterrows():
        parcelas = str(row.get("Parcelas", "1/1"))
        try:
            current, total = map(int, parcelas.split("/"))
        except:
            current, total = 1, 1

        new_row = row.copy()
        try:
            raw_date = str(row["Date"]).strip().replace("=", "").replace('"', "")
            base_date = row["Date"]
            if pd.isna(base_date):
                continue  # ou trate como necessário


            new_row["Date"] = base_date + pd.DateOffset(months=(current - 1))
        except:
            new_row["Date"] = pd.NaT

        adjusted_rows.append(new_row)

    adjusted_df = pd.DataFrame(adjusted_rows)
    adjusted_df["Date"] = pd.to_datetime(adjusted_df["Date"], errors="coerce")
    adjusted_df["Month"] = adjusted_df["Date"].dt.to_period("M").astype(str)

    return adjusted_df

# Carregar dados
st.title("📊 Dashboard Financeiro - Google Sheets")
df_raw = load_google_sheets_data(SHEET_NAMES)
df = adjust_installment_dates(df_raw)

# Filtros
st.sidebar.header("Filtros")
months = sorted(df["Month"].dropna().unique())
selected_months = st.sidebar.multiselect("Selecione os meses", months, default=months)

categories = sorted(df["Category"].dropna().unique())
selected_categories = st.sidebar.multiselect("Selecione categorias", categories, default=categories)

transaction_types = sorted(df["Transaction"].dropna().unique())
selected_types = st.sidebar.multiselect("Selecione tipo", transaction_types, default=transaction_types)

# Aplicar filtros
df_filtered = df[
    (df["Month"].isin(selected_months)) &
    (df["Category"].isin(selected_categories)) &
    (df["Transaction"].isin(selected_types))
]

# KPIs
df_investments = df_filtered[(df_filtered["Transaction"] == "Expense") & (df_filtered["Category"] == "Savings")]
df_expenses_no_savings = df_filtered[(df_filtered["Transaction"] == "Expense") & (df_filtered["Category"] != "Savings")]

total_expenses = df_expenses_no_savings["Amount"].sum()
total_income = df_filtered[df_filtered["Transaction"] == "Income"]["Amount"].sum()
total_investments = df_investments["Amount"].sum()
balance = total_income - (total_expenses + total_investments)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Despesas", f"R$ {total_expenses:,.2f}")
col2.metric("Receitas", f"R$ {total_income:,.2f}")
col3.metric("Investimentos", f"R$ {total_investments:,.2f}")
col4.metric("Saldo", f"R$ {balance:,.2f}")

# Gráfico Receita vs Despesa
st.subheader("📈 Receita vs Despesa")
if not df_filtered.empty:
    monthly_summary = df_filtered.groupby(["Month", "Transaction"])["Amount"].sum().reset_index()
    fig_line = px.line(monthly_summary, x="Month", y="Amount", color="Transaction", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

# Evolução por categoria
st.subheader("📊 Evolução das Despesas por Categoria")
if not df_expenses_no_savings.empty:
    evolution_by_cat = df_expenses_no_savings.groupby(["Month", "Category"])["Amount"].sum().reset_index()
    fig_cat = px.line(evolution_by_cat, x="Month", y="Amount", color="Category", markers=True)
    st.plotly_chart(fig_cat, use_container_width=True)

# Top 5 Categorias
st.subheader("Top 5 Categorias de Gastos")
if not df_expenses_no_savings.empty:
    top_cats = df_expenses_no_savings.groupby("Category")["Amount"].sum().nlargest(5).index.tolist()
    df_top5 = df_expenses_no_savings[df_expenses_no_savings["Category"].isin(top_cats)]
    df_top5_summary = df_top5.groupby(["Month", "Category"])["Amount"].sum().reset_index()
    fig_top5 = px.bar(df_top5_summary, x="Month", y="Amount", color="Category", text_auto=True)
    st.plotly_chart(fig_top5, use_container_width=True)

# Pizza Receita vs Despesa
st.subheader("🥧 Receita vs Despesa")
summary = {"Receita": total_income, "Despesa": total_expenses}
fig_pie = px.pie(names=list(summary.keys()), values=list(summary.values()))
st.plotly_chart(fig_pie, use_container_width=True)

# Investimentos
st.subheader("📈 Investimentos")
if not df_investments.empty:
    invest_month = df_investments.groupby("Month")["Amount"].sum().reset_index()
    fig_invest = px.line(invest_month, x="Month", y="Amount", markers=True)
    st.plotly_chart(fig_invest, use_container_width=True)

# Download CSV
st.download_button(
    "📅 Baixar dados filtrados (CSV)",
    df_filtered.to_csv(index=False).encode("utf-8"),
    "dados_filtrados.csv",
    "text/csv",
)

# Tabela final
st.subheader("📄 Detalhes das Transações")
st.dataframe(df_filtered.sort_values(by="Date", ascending=False))






