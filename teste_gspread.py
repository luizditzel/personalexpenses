import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("🔐 Teste de Acesso ao Google Sheets")

scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

# Autenticação via secrets.toml
try:
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(credentials)
    st.success("✅ Autenticação bem-sucedida com a conta de serviço.")
except Exception as e:
    st.error(f"❌ Falha na autenticação: {e}")
    st.stop()

# Tentar abrir a planilha
SPREADSHEET_ID = "1D4xID5FDYYNvpctagqpfIDagt74CeU2K"
try:
    sheet = client.open_by_key(SPREADSHEET_ID)
    st.success("📄 Planilha acessada com sucesso!")
    st.write("Abas disponíveis:", [ws.title for ws in sheet.worksheets()])
except Exception as e:
    st.error(f"❌ Falha ao acessar a planilha: {e}")
