import streamlit as st
from spacy.displacy import EntityRenderer

HTML_WRAPPER = """<div style="dir: auto; overflow-x: auto; border: 1px solid #e6e9ef; border-radius: 0.25rem; padding: 1rem; margin-bottom: 2.5rem">{}</div>"""

entity_colors = {
    "CREDIT_CARD": "#FFF8C3",
    "CRYPTO": "#CBC3FF",
    "DATE_TIME": "#00cdcd",
    "DOMAIN_NAME": "#bc8f8f",
    "EMAIL_ADDRESS": "#4682b4",
    "IBAN_CODE": "#808080",
    "IP_ADDRESS": "#ffe4b5",
    "NRP": "#6666ff",
    "LOCATION": "#ee76ff",
    "PERSON": "#cdff76",
    "PHONE_NUMBER": "#daa520",
    "MEDICAL_LICENSE": "#66cd00",
    "US_BANK_NUMBER": "#f0e68c",
    "US_DRIVER_LICENSE": "#ffaeb9",
    "US_ITIN": "#FFC3C3",
    "US_PASSPORT": "#dcdcdc",
    "US_SSN": "#B49DDC",
    "UK_NHS": "#C59DDC",
    "NIF": "#ff4500",
    "FIN/NRIC": "#7fff00",
    "AU_ABN": "#ff8c00",
    "AU_ACN": "#424242",
    "AU_TFN": "#ff1493",
    "AU_MEDICARE": "#228b22",
    "PERS": "#1e90ff",

    "CARDINAL": "#8bddff",
    "DATE": "#ffabcd",
    "EVENT": "#68228b",
    "FAC": "#ff69b4",
    "GPE": "#7fffd4",
    "LANGUAGE": "#8b8b00",
    "LAW": "#d8bfd8",
    "LOC": "#FDC9A6",
    "MONEY": "#8b7355",
    "NORP": "#fafa88",
    "ORDINAL": "#00bfff",
    "ORG": "#ff00ff",
    "PERCENT": "#008000",
    "XXX": "#dc143c",
    "PRODUCT": "#deb887",
    "QUANTITY": "#add8e6",
    "TIME": "#da70d6",
    "WORK_OF_ART": "#00cc8c",

    "FOOD": "#ff6c6c",
    "EXTERNAL_EVENT": "#666680",
    "CARE_ENVIRONMENT": "#123456",
    "HEALTHCARE_PROFESSIONAL": "#ffd700",
    "ADMINISTRATIVE_EVENT": "#bfccff",
    "NAME": "#4169e1",
    "ADDRESS": "#cdcd00",
    "YYY": "#db7093",
    "PHONE_OR_FAX": "#ff7f50",
    "ID": "#8b0000",
    "EMAIL": "#76ee00",
    "URL": "#ffff00",
    "ZZZ": "#4d4d4d"
}

other_colors = {
    "FOLLOWING_NEGATIONS": "#FFAA00",
    "PRECEDING_NEGATIONS": "#AAFF00",
    "PSUDEO_NEGATIONS": "#FF00AA",
    "TERMINATION": "#CCCCFF",
    "SEC": "#fbe2e5",
    "SEGMENTER": "#bedbbb",
    "LINEBREAK_CLASSIFIER": "#ddf3f5",
    "ONE_LINE_SECTION": "#ddf3f5",
    "MERGING": "#ccf6c8",
    "NOT_MERGING": "#c3aed6"
}

colors = {**entity_colors, **other_colors}


def render_entities(doc_dict, options=None):
    _html = {}
    tpl_ent = """
    <mark class="entity" style="background: {bg}; padding: 0.45em 0.45em; margin: 0 0.25em; line-height: 1; border-radius: 1.00em; border-style: solid; border-color: {bg}; opacity: 0.5;">
        {text}
        <span style="font-size: 0.8em; font-weight: bold; line-height: 1; border-radius: 0.35em; text-transform: uppercase; vertical-align: middle; margin-left: 0.5rem">{label}</span>
    </mark>
    """
    if options is None:
        options = {"colors": colors}
    renderer = EntityRenderer(options=options)
    doc_dict.update({"settings": {"direction": "rtl"}})
    _html["parsed"] = renderer.render([doc_dict]).strip()
    html = _html["parsed"]
    # Newlines seem to mess with the rendering
    html = html.replace("⏎", "<br>")
    html = html.replace("\n", " ")

    st.write(HTML_WRAPPER.format(html), unsafe_allow_html=True)
