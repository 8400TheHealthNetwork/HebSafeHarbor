from typing import Dict, List

import pandas as pd
import streamlit as st

from utils import render_entities


def show_entities(text: str, items: pd.DataFrame):
    spans = [{"start": item["startPosition"], "end": item["endPosition"], "label": item["entityType"]} for _, item in
             items.iterrows()]
    doc_dict = {"text": text, "ents": spans}
    render_entities(doc_dict=doc_dict)


def visualize_response(source_text: str, response: Dict):
    resopnse_items = response.get("items", [])
    if not resopnse_items:
        return
    items_df = pd.DataFrame.from_records(resopnse_items)


    print(items_df)
    identification_df = items_df[["textStartPosition", "textEndPosition", "textEntityType"]]
    identification_df.columns = ["startPosition", "endPosition", "entityType"]
    show_entities(source_text, identification_df)

    anonymized_df = items_df[["maskStartPosition", "maskEndPosition", "textEntityType"]]
    anonymized_df.columns = ["startPosition", "endPosition", "entityType"]
    show_entities(response["text"], anonymized_df)

    st.table(items_df)