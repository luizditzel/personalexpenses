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

def load_data_consolidated(file_path="Monthly_Check_2025.xlsm"):
    try:
        excel_file = pd.ExcelFile(file_path, engine="openpyxl")
    except FileNotFoundError:
        st.error("❌ Arquivo não encontrado. Certifique-se que o arquivo está no mesmo repositório.")
        st.stop()

    # Selecionar abas com padrão mês (01-2025 ou 01_2025)
    month_sheets = [sheet for sheet in excel_file.sheet_names if re.match(r"^\d{2}[-_]\d{4}$", sheet)]

    if not month_sheets:
        st.error("❌ Nenhuma aba com formato válido encontrada. Esperado: 01-2025 ou 01_2025.")
        st.stop()

    all_data = []
    for sheet in month_sheets:
        df_temp = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")
        if df_temp.empty:
            continue  # Ignorar abas vazias
        all_data.append(df_temp)

    if not all_data:
        st.error("❌ Não foi possível carregar dados. As abas podem estar vazias ou com estrutura inválida.")
        st.stop()

    # Concatenar todas as abas
    df = pd.concat(all_data, ignore_index=True)

    # Normalizar colunas se existirem
    if hasattr(df, "columns"):
        df.columns = [str(col).strip().capitalize() for col in df.columns]
    else:
        st.error("❌ Estrutura do arquivo inválida. Verifique se as abas possuem cabeçalhos.")
        st.stop()

    return df

def adjust_installment_dates(df):
    # Garantir que existe coluna Parcelas
    if "Parcela" not in df.columns:
        return df

    adjusted_rows = []
    for _, row in df.iterrows():
        parcelas = str(row.get("Parcelas", "1/1"))
        try:
            current, total = map(int, parcelas.split("/"))
        except:
            current, total = 1, 1

        # Ajustar data para refletir a parcela correta
        new_row = row.copy()
        new_row["Date"] = row["Date"] + pd.DateOffset(months=(current - 1))
        new_row["Month"] = new_row["Date"].to_period("M").astype(str)
        adjusted_rows.append(new_row)

    return pd.DataFrame(adjusted_rows)

df_raw = load_data_consolidated()
df = adjust_installment_dates(df_raw)
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
# Separar Savings das outras despesas
df_investments = df_filtered[(df_filtered["Transaction"] == "Expense") & (df_filtered["Category"] == "Savings")]
df_expenses_no_savings = df_filtered[(df_filtered["Transaction"] == "Expense") & (df_filtered["Category"] != "Savings")]

# KPIs ajustados
total_expenses = df_expenses_no_savings["Amount"].sum()
total_income = df_filtered[df_filtered["Transaction"] == "Income"]["Amount"].sum()
total_investments = df_investments["Amount"].sum()
balance = total_income - (total_expenses + total_investments)


st.title("📊 Dashboard Financeiro")
st.markdown("Visualização interativa de receitas e despesas")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Despesas", f"R$ {total_expenses:,.2f}")
col2.metric("Total Receitas", f"R$ {total_income:,.2f}")
col3.metric("Investimentos", f"R$ {total_investments:,.2f}")
col4.metric("Saldo", f"R$ {balance:,.2f}")

# =====================
# GRÁFICOS
# =====================

# 1) Evolução mensal Receita vs Despesa
st.subheader("📈 Evolução Mensal (Receita vs Despesa)")
monthly_summary = df_filtered.groupby(["Month", "Transaction"])["Amount"].sum().reset_index()
fig_line = px.line(monthly_summary, x="Month", y="Amount", color="Transaction",
                   title="Receita e Despesa por Mês", markers=True)
st.plotly_chart(fig_line, use_container_width=True)

# 2) Evolução das Despesas por Categoria
st.subheader("📊 Evolução das Despesas por Categoria")
if not df_expenses_no_savings.empty:
    evolution_by_cat = df_expenses_no_savings.groupby(["Month", "Category"])["Amount"].sum().reset_index()
    fig_cat_evolution = px.line(evolution_by_cat, x="Month", y="Amount", color="Category",
                                 title="Evolução das Despesas por Categoria", markers=True)
    st.plotly_chart(fig_cat_evolution, use_container_width=True)
else:
    st.info("Nenhuma despesa encontrada no período selecionado.")
    
# 3) Top 5 Categorias ao longo dos meses
st.subheader("🔥 Top 5 Categorias de Gastos ao Longo dos Meses")
if not df_expenses_no_savings.empty:
    top_categories = (
        df_expenses_no_savings.groupby("Category")["Amount"].sum()
        .sort_values(ascending=False)
        .head(5)
        .index.tolist()
    )
    df_top5 = df_expenses_no_savings[df_expenses_no_savings["Category"].isin(top_categories)]
    df_top5_summary = df_top5.groupby(["Month", "Category"])["Amount"].sum().reset_index()
    fig_top5 = px.bar(
        df_top5_summary,
        x="Month",
        y="Amount",
        color="Category",
        title="Top 5 Categorias de Gastos por Mês",
        text_auto=True
    )
    st.plotly_chart(fig_top5, use_container_width=True)
else:
    st.info("Não há despesas para calcular as Top 5 categorias.")

# 4) Gastos por Categoria (Selecionar Mês)
st.subheader("📊 Gastos por Categoria (Selecionar Mês)")
month_for_bar = st.selectbox("Selecione um mês para analisar categorias", months)
df_month = df_expenses_no_savings[df_expenses_no_savings["Month"] == month_for_bar]
if not df_month.empty:
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
else:
    st.info(f"Não há despesas registradas para {month_for_bar}.")


# 5) Pizza - Receita vs Despesa (sem Savings)
st.subheader("🥧 Receita vs Despesa")
summary = {"Receita": total_income, "Despesa": total_expenses}
fig_pie = px.pie(names=list(summary.keys()), values=list(summary.values()), title="Receita vs Despesa (Exclui Investimentos)")
st.plotly_chart(fig_pie, use_container_width=True)

# 6) Evolução dos Investimentos
st.subheader("📈 Evolução dos Investimentos")
if not df_investments.empty:
    investments_by_month = df_investments.groupby("Month")["Amount"].sum().reset_index()
    fig_invest = px.line(investments_by_month, x="Month", y="Amount", title="Investimentos por Mês", markers=True)
    st.plotly_chart(fig_invest, use_container_width=True)
else:
    st.info("Nenhum investimento registrado no período selecionado.")

# =====================
# TABELA FILTRADA
# =====================
st.subheader("📄 Detalhes das Transações Filtradas")
st.dataframe(df_filtered.sort_values(by="Date", ascending=False))





