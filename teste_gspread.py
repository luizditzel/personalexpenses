import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Autenticação
try:
    credentials = service_account.Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/drive.metadata.readonly"]
    )
    st.success("✅ Autenticação com sucesso")
except Exception as e:
    st.error(f"❌ Erro na autenticação: {e}")
    st.stop()

# Criar cliente da API Google Drive
try:
    service = build("drive", "v3", credentials=credentials)
    results = service.files().list(pageSize=10, fields="files(id, name)").execute()
    files = results.get("files", [])

    if not files:
        st.warning("⚠️ Nenhum arquivo acessível foi encontrado.")
    else:
        st.success("📁 Arquivos acessíveis pela conta de serviço:")
        for file in files:
            st.write(f"📄 {file['name']} (ID: {file['id']})")
except Exception as e:
    st.error(f"❌ Erro ao acessar Google Drive: {e}")
