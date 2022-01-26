#from term_sentiment import get_average_rating, get_entities
# import numpy as np
# import pandas as pd
 
import streamlit as st


import base64

# from livescore_data import voetbal_data, DIVISIES
from paginas import *
# import difflib
# 
# 
# 
# import altair as alt
# import gpdvega

LOGO_IMAGE = "Datacation_Logo_Wit.png"






STYLES = ["""
            <style>
            header {visibility: hidden;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """, """
            <style>
            .footer_img {
                max-width: 15%;
                height: auto;
                
            } 
            .footer {
            position: fixed;
            left: 5;
            bottom: 0;
            width: 100%;

            color: white;
            margin-bottom: 45px;
            }
            </style>
            """]

FOOTER = f"""
            <div class="footer">
            <p> </p>
            <img src="data:image/png;base64,{base64.b64encode(open(LOGO_IMAGE, "rb").read()).decode()}" class=footer_img alt="Dedicated to data!";"
            </div>
        """
        


def run_UI():
    st.set_page_config(
        page_title="🖥💪💥Voetbal Sentiment Analyse",
        page_icon="⚽",
        initial_sidebar_state="expanded")
    st.sidebar.title('Voetbal Sentiment Analyse')

    for style in STYLES:
        st.markdown(style, unsafe_allow_html=True) 
    st.sidebar.markdown(FOOTER, unsafe_allow_html=True)
  # print(st.session_state.divisie, st.session_state.data_type)
    df = pd.read_csv('data/livescore_eredivisie.csv')
    keuzes = ["Algemeen", "Wedstrijden", "Provincies", "Wordcloud"]
    keuze = st.sidebar.selectbox('Maak een selectie', keuzes)
    st.sidebar.write("""
    Deze tool analyseert de sentimenten van voetbal wedstrijden. Hierbij is het mogelijk om teams/spelers/locaties de sentimenten in te zien. 
    Op basis van deze informatie in combinatie met voetbal statistieken kan de tool een aanbeveling doen van te bekijken wedstrijd.
    """)
    # st.sidebar.button("Geef Aanbeveling")
    
    #st.sidebar.image("Datacation_Logo_Wit.png", use_column_width=True)

    if keuze == 'Algemeen':
        st.title("Algemeen")
        algemeen_page(df)
    elif keuze == "Wedstrijden":
        st.title("Wedstrijden")
        wedstrijden_page(df)
    elif keuze == "Provincies":
        st.title("Provincies")
        locaties_page(df)
    else:
        st.title("Cloud")
        cloud_page(df)
        


if __name__ == '__main__':
    st.set_option('deprecation.showPyplotGlobalUse', False)
    if st._is_running_with_streamlit:
        run_UI()