import streamlit as st
import pandas as pd
import numpy as np
import datetime as dt
import plotly.express as px
import requests

def plot_auslastung():
    st.title('EP-Auslastung')

    jahr_ausgang = dt.date.today().year
    liste_jahr = [jahr_ausgang, jahr_ausgang +1]    
    jahr = st.selectbox(label='Jahr', options=liste_jahr)

    datum = pd.to_datetime(st.date_input(label='Datum', min_value=f'{jahr}-01-01', max_value=f'{jahr}-12-31'))

    @st.cache_data
    def lade_alle_ferien(jahr, art):
        liste_land = ['DE', 'FR', 'CH', 'AT']

        def api_ferien(jahr, land, art):
            url = f'https://openholidaysapi.org/{art}Holidays'
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
            try:
                df['gebiet'] = [x[0]['shortName'] if isinstance(x, list) and len(x) > 0 else land for x in df['subdivisions']]
            except:
                df['gebiet'] = land
            df['land'] = land
            df = df[['startDate', 'endDate', 'type', 'nationwide', 'ferien', 'land', 'gebiet']]
            df[['startDate', 'endDate']] = df[['startDate', 'endDate']].apply(pd.to_datetime)
            df['art'] = art

            return df
        
        df_ferien = pd.DataFrame(columns=['startDate', 'endDate', 'type', 'nationwide', 'ferien', 'land', 'gebiet', 'art'])

        for land in liste_land:
            df_api = api_ferien(jahr, land, art)
            df_ferien = pd.concat([df_ferien, df_api])

        return df_ferien

    def merge_alle_ferien():
        df_ferien = lade_alle_ferien(jahr, 'School')
        df_feiertage = lade_alle_ferien(jahr, 'Public')

        df = pd.concat([df_ferien, df_feiertage])
        df['ferien'] = np.where(df['art'] == 'School', 1, 0)
        df['feiertag'] = np.where(df['art'] == 'Public', 1, 0)

        dict_gebiete = {
            'DE': 16,
            'FR': 18,
            'CH': 26,
            'AT': 9
        }    
        
        df['feiertag'] = np.where(df['nationwide'] == True, df['land'].map(dict_gebiete), df['feiertag'])

        return df

    df_feiertage_gesamt = merge_alle_ferien()

    def lade_ferien(df_ferien, datum):
        df = df_ferien.copy()
        df = df.loc[(df['startDate'] <= datum) & (df['endDate'] >= datum)]
        df = df[['land', 'gebiet', 'ferien', 'feiertag']]

        df = df.groupby('land')[['ferien', 'feiertag']].sum().reset_index()

        return df

    df_ferien_anzeige = lade_ferien(df_feiertage_gesamt, datum)

    if len(df_ferien_anzeige) == 0:
        st.success('Super, dies ist ein großartiger Tag für den EP. Die Welt gehört uns!', icon=':material/celebration:')
        return

    column_config_ep = {
        'land': st.column_config.Column(
            label='Land'
        ),
        'ferien': st.column_config.NumberColumn(
            label='Ferien (Gebiete)'
        ),
        'feiertag': st.column_config.NumberColumn(
            label='Feiertage (Gebiete)',
            help='Ggf. kann eine 1 auch das gesamte Land widerspiegeln'
        ),
    }

    st.dataframe(df_ferien_anzeige, hide_index=False, column_config=column_config_ep)

plot_auslastung()
