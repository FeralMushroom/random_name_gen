import streamlit as st
from generator import generate_phrase

st.set_page_config(
    page_title="Generator Losowych Fraz",
    page_icon="🎲",
    layout="centered",
)

st.markdown("""
<style>
    .phrase-box {
        background: #f8f9fa;
        border-left: 4px solid #1a73e8;
        padding: 10px 16px;
        margin: 6px 0;
        border-radius: 4px;
        font-size: 1.1rem;
        color: #1a1a1a;
    }
    .stButton > button {
        width: 100%;
        background-color: #1a73e8;
        color: white;
        border: none;
        padding: 0.6rem;
        font-size: 1rem;
        border-radius: 6px;
    }
    .stButton > button:hover {
        background-color: #1557b0;
    }
</style>
""", unsafe_allow_html=True)

st.title("🎲 Generator Losowych Fraz")
st.caption("Losowe zestawienia polskich słów")

col1, col2 = st.columns([2, 1])

with col1:
    mode = st.selectbox(
        "Tryb",
        options=["adj+n+gen", "adj+n", "n+gen"],
        format_func=lambda x: {
            "adj+n+gen": "Przymiotnik + Rzeczownik + Dopełniacz",
            "adj+n":     "Przymiotnik + Rzeczownik",
            "n+gen":     "Rzeczownik + Dopełniacz",
        }[x],
    )

with col2:
    count = st.number_input("Liczba fraz", min_value=1, max_value=50, value=5)

safe = st.toggle("Tryb bezpieczny", value=True)

if st.button("✨ Generuj"):
    phrases = [generate_phrase(mode=mode, safe=safe) for _ in range(count)]
    st.session_state["phrases"] = phrases

if "phrases" in st.session_state:
    phrases = st.session_state["phrases"]
    for phrase in phrases:
        st.markdown(f'<div class="phrase-box">{phrase}</div>', unsafe_allow_html=True)

    st.text_area(
        "Skopiuj wszystkie",
        value="\n".join(phrases),
        height=min(150, 30 * len(phrases)),
        label_visibility="collapsed",
    )
