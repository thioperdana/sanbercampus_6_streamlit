import streamlit as st
import pandas as pd
from google import genai
import io

st.set_page_config(
    page_title="Chat dengan Gemini",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("Chat dengan Gemini")

with st.sidebar:
    st.title("Tentang Aplikasi")
    st.write("""
    Aplikasi ini menggunakan model Gemini-Flash-Lite-Latest dari Google GenAI.
    Anda dapat memasukkan teks atau mengunggah file untuk mendapatkan respon dari model.
    """)
    st.write("## Pengaturan")
    st.write("Pengaturan tambahan dapat ditambahkan di sini.")
    model = st.selectbox(
        "Pilih Model",
        ("gemini-flash-latest", "gemma-3-4b-it", "gemini-2.5-pro")
    )
    gemini_key = st.text_input(
        "Masukkan API Key Gemini Anda",
        type="password",
        value=st.secrets["GEMINI_API_KEY"]
    )

    if st.button("Hapus Riwayat Chat"):
        st.session_state["messages"] = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input(
    "Katakan sesuatu...",
    accept_file=True,
    file_type=["txt", "pdf", "csv", "docx"]
    ):
    
    st.chat_message("user").markdown(prompt.text)
    st.session_state["messages"].append({"role": "user", "content": prompt.text})

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        gemini_api_key = gemini_key
        client = genai.Client(api_key=gemini_api_key)

        if prompt.files:
            # Jika ada file yang diunggah adalah .txt
            # berkas = prompt.files[0].getvalue()

            # Jika ada file yang diunggah adalah .pdf
            berkas = io.BytesIO(prompt.files[0].getvalue())
            import PyPDF2
            pdf_reader = PyPDF2.PdfReader(berkas)
            berkas =f"""

            History percakapan:
            Gunakan percakapan di bawah sebagai konteks tambahan untuk menjawab
            {''.join([msg['content'] for msg in st.session_state['messages'] if msg['role']=='user'])}
            Jangan sebutkan history percakapan di jawaban Anda. 

            {prompt.text}

            Berikut adalah isi dari file yang diunggah:
            """
            for page in pdf_reader.pages:
                berkas += page.extract_text()+"\n"

            response = client.models.generate_content_stream(
                model=model,
                contents=berkas
            )
        else:
            berkas =f"""

            History percakapan:
            Gunakan percakapan di bawah sebagai konteks tambahan untuk menjawab
            {''.join([msg['content'] for msg in st.session_state['messages'] if msg['role']=='user'])}
            Jangan sebutkan history percakapan di jawaban Anda. Jangan ulangi pertanyaan.

            {prompt.text}
            """

            response = client.models.generate_content_stream(
                model=model,
                contents=berkas
            )

        for chunk in response:
            if chunk.text:
                full_response += chunk.text+"\n"
            
            message_placeholder.markdown(full_response + "▌")

        message_placeholder.markdown(full_response)
        st.session_state["messages"].append({"role": "assistant", "content": full_response})

