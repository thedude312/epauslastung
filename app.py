import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import plotly.express as px
import requests

with st.sidebar:
    jahr_ausgang = dt.date.today().year
    liste_jahr = [jahr_ausgang, jahr_ausgang +1]    
    jahr = st.selectbox(label='Jahr', options=liste_jahr)

    datum = pd.to_datetime(st.date_input(label='Datum', min_value=f'{jahr}-01-01', max_value=f'{jahr}-12-31'))

@st.cache_data
def lade_alle_ferien(jahr):
    liste_land = ['DE', 'FR', 'CH', 'AT']

    def api_ferien(jahr, land):
        url = 'https://openholidaysapi.org/SchoolHolidays'
        params = {
            'countryIsoCode': land,
            'languageIsoCode': 'DE',
            'validFrom': f'{jahr}-01-01',
            'validTo': f'{jahr}-12-31'
        }

        response = requests.get(url, params=params, headers={'accept': 'text/json'})
        data = response.json()

        df = pd.json_normalize(data)
    
        df['ferien'] = [x[0]['text'] if isinstance(x, list) and len(x) > 0 else None for x in df['name']]
        df['gebiet'] = [x[0]['shortName'] if isinstance(x, list) and len(x) > 0 else None for x in df['subdivisions']]
        df['land'] = land
        df = df[['startDate', 'endDate', 'type', 'nationwide', 'ferien', 'land', 'gebiet']]
        df[['startDate', 'endDate']] = df[['startDate', 'endDate']].apply(pd.to_datetime)

        return df
    
    df_ferien = pd.DataFrame(columns=['startDate', 'endDate', 'type', 'nationwide', 'ferien', 'land', 'gebiet'])

    for land in liste_land:
        df_api = api_ferien(jahr, land)
        df_ferien = pd.concat([df_ferien, df_api])

    return df_ferien

df_ferien = lade_alle_ferien(jahr)

def lade_ferien(df_ferien, datum):
    df = df_ferien.copy()
    df['ferien'] = 1
    df = df.loc[(df['startDate'] <= datum) & (df['endDate'] >= datum)]
    df = df[['land', 'gebiet', 'ferien']]

    return df

df_ferien_anzeige = lade_ferien(df_ferien, datum)

st.dataframe(df_ferien_anzeige)
