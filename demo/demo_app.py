import json
import os
import requests
import streamlit as st

st.set_page_config(layout="wide", page_title="Hebrew Safe Harbor", initial_sidebar_state="collapsed")

from visualizer import visualize_response

DEFAULT_TEXT = "גדעון לבנה הגיע היום לבית החולים שערי צדק עם תלונות על כאבים בחזה"
URL = os.getenv("HSH_SERVER", "http://localhost:8000")

def run():
    st.title("Hebrew Safe Harbor demo application")
    # TODO check if server is ready + create url

    with st.form("analyze text"):
        text = st.text_area("Enter text to analyze", DEFAULT_TEXT)
        req_data = {
            "docs": [
                {
                    "id": "doc_1",
                    "text": text
                }
            ]
        }

        submitted = st.form_submit_button("Analyze")

        if submitted:
            print(URL)
            if text is not None and len(text) > 0:
                response = requests.post(f"{URL}/query", json=req_data)
                content = json.loads(response.content)

                with st.expander("JSON response"):
                    response_content = json.dumps(content, indent=4, ensure_ascii=False)
                    st.code(response_content, language="json")

                docs = content.get("docs", [])
                if len(docs) == 1:
                    doc = docs[0]
                    visualize_response(text, doc)
                else:
                    if response.status_code == 20:  # response consists of more than one doc
                        st.error("Expected a single text to process and visualize, but received more than one")
                    else:
                        response = requests.post(f"{URL}/ready", json=req_data)
                        if response.status_code == 503:
                            st.error("Server is not ready - Try again soon or check server")
                        else:
                            st.error(response.text)


if __name__ == "__main__":
    run()
