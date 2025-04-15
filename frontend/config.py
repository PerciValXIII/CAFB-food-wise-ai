import streamlit as st

# These keys must match the keys in your .streamlit/secrets.toml file.
BEARER_TOKEN = st.secrets["general"]["BEARER_TOKEN"]
API_URL = st.secrets["general"]["API_URL"]
PPT_GEN_URL = st.secrets["general"]["PPT_GEN_URL"]
PDF_GEN_URL = st.secrets["general"]["PDF_GEN_URL"]
UPLOAD_FILE_URL = st.secrets["general"]["UPLOAD_FILE_URL"]

