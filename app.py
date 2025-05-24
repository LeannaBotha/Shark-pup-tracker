import streamlit as st
import pandas as pd
import os
from datetime import datetime

# File to store data
DATA_FILE = "shark_pups.csv"

st.title("🦈 Shark Pup Tracker")
st.write("Log and review data from your shark pups.")

# Input form
with st.form("pup_form"):
    date = st.date_input("Date", value=datetime.today())
    pup_id = st.text_input("Pup ID")
    weight = st.number_input("Weight (g)", min_value=0.0, step=0.1)
    length = st.number_input("Length (cm)", min_value=0.0, step=0.1)
    notes = st.text_area("Notes", height=100)
    submitted = st.form_submit_button("Add Entry")

    if submitted:
        new_row = {
            "Date": date.strftime("%Y-%m-%d"),
            "Pup ID": pup_id,
            "Weight (g)": weight,
            "Length (cm)": length,
            "Notes": notes,
        }

        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        else:
            df = pd.DataFrame([new_row])

        df.to_csv(DATA_FILE, index=False)
        st.success(f"Saved entry for Pup ID: {pup_id}")

# Show current records
if os.path.exists(DATA_FILE):
    st.subheader("📊 All Recorded Shark Pups")
    df = pd.read_csv(DATA_FILE)
    st.dataframe(df)
else:
    st.info("No data recorded yet.")

