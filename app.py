import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from io import BytesIO

def haal_keuring_data(kentekens):
    url = "https://opendata.rdw.nl/resource/vkij-7mwc.json"
    records = []
    for kenteken in kentekens:
        params = {"$select": "kenteken, vervaldatum_keuring_dt", "$where": f"kenteken='{kenteken}'"}
        try:
            response = requests.get(url, params=params)
            if response.ok and response.json():
                data = response.json()[0]
            else:
                data = {"kenteken": kenteken, "vervaldatum_keuring_dt": None}
        except:
            data = {"kenteken": kenteken, "vervaldatum_keuring_dt": None}
        records.append(data)

    df = pd.DataFrame(records)
    df["vervaldatum_keuring_dt"] = pd.to_datetime(df["vervaldatum_keuring_dt"], errors='coerce')
    df["dagen_tot_verval"] = (df["vervaldatum_keuring_dt"] - pd.Timestamp.today()).dt.days.round()

    # Zet duidelijke tekst voor ontbrekende datums
    df["vervaldatum_keuring_dt"] = df["vervaldatum_keuring_dt"].dt.date
    df["vervaldatum_keuring_dt"] = df["vervaldatum_keuring_dt"].fillna("geen vervaldatum")
    df["dagen_tot_verval"] = df["dagen_tot_verval"].fillna("N.V.T.").astype(str)

    return df

def schrijf_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter", datetime_format="yyyy-mm-dd")
    df.to_excel(writer, index=False, sheet_name="Keuringen")
    workbook = writer.book
    worksheet = writer.sheets["Keuringen"]
    col = df.columns.get_loc("dagen_tot_verval")

    # Opmaak
    oranje = workbook.add_format({"bg_color": "#FFA500"})
    groen = workbook.add_format({"bg_color": "#C6EFCE"})
    grijs = workbook.add_format({"bg_color": "#D9D9D9"})

    # Grijs = "N.V.T."
    worksheet.conditional_format(1, col, len(df), col, {
        "type": "text", "criteria": "containing", "value": "N.V.T.", "format": grijs
    })

    # Oranje < 30
    worksheet.conditional_format(1, col, len(df), col, {
        "type": "cell", "criteria": "<", "value": 30, "format": oranje
    })

    # Groen >= 30
    worksheet.conditional_format(1, col, len(df), col, {
        "type": "cell", "criteria": ">=", "value": 30, "format": groen
    })

    writer.close()
    output.seek(0)
    return output

# Streamlit UI
st.title("RDW Keuringsdatum Checker")
st.markdown("Plak een lijst met kentekens (één per regel):")

input_text = st.text_area("Kentekens")
if st.button("Genereer Excel"):
    kentekens = [k.strip().replace("-", "").upper() for k in input_text.splitlines() if k.strip()]
    if kentekens:
        df = haal_keuring_data(kentekens)
        excel_data = schrijf_excel(df)
        st.download_button("Download RDW-Keuringen.xlsx", excel_data, file_name="RDW-Keuringen-vervaldatums.xlsx")
    else:
        st.warning("Voer eerst geldige kentekens in.")
