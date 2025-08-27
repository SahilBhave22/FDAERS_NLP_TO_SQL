import os, json
import streamlit as st
from agent import build_agent  # your LangGraph builder

st.set_page_config(page_title="FAERS NLP → SQL (Query Only)", page_icon="💊", layout="wide")

# --- Secrets ---
# - openai_api_key (optional; can also use env var)
# - schema_catalog_path OR schema_catalog (inline JSON string)
OPENAI_KEY = st.secrets.get("openai_api_key")
if OPENAI_KEY:
    os.environ["OPENAI_API_KEY"] = OPENAI_KEY

@st.cache_resource
def load_catalog():
    if "schema_catalog" in st.secrets:
        try:
            return json.loads(st.secrets["schema_catalog"])
        except Exception as e:
            st.error("Could not parse schema_catalog in secrets.")
            raise
    path = st.secrets.get("schema_catalog_path", "schema_catalog.json")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Failed to read schema catalog at {path}.")
        raise

@st.cache_resource
def get_agent():
    catalog = load_catalog()
    return build_agent(catalog), catalog

st.title("💊 FAERS NLP → SQL")
st.caption("Type a FAERS question → get validated SQL. No database execution.")

with st.sidebar:
    st.header("Schema Catalog")
    try:
        cat_str = json.dumps(load_catalog(), indent=2)
        st.code(cat_str[:900] + ("..." if len(cat_str) > 900 else ""))
    except Exception:
        st.write("Catalog not loaded.")

q = st.text_area(
    "Ask a FAERS question",
    placeholder="Top 10 adverse events in males for Keytruda since 2021 reported by health professionals",
    height=140,
)

go = st.button("Generate SQL", type="primary")

sql_box = st.empty()
err_box = st.empty()

if go:
    if not q.strip():
        st.error("Please enter a question.")
        st.stop()

    app, catalog = get_agent()
    state = {"question": q, "sql": None, "error": None, "attempts": 0, "summary": None}
    final_state = app.invoke(state)

    sql = (final_state.get("sql") or "").strip()
    error = final_state.get("error")

    if sql:
        sql_box.code(sql, language="sql")
    else:
        err_box.error("No SQL was generated. Check your model/key and catalog.")

    if error:
        err_box.error(f"Validator: {error}")
