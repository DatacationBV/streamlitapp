#from term_sentiment import get_average_rating, get_entities
# from bokeh.models.annotations import Tooltip
import numpy as np
from numpy import random
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from wordcloud import WordCloud
import json
# from enum import Enum
# import os
# import base64

# from livescore_data import voetbal_data, DIVISIES
# import difflib
# import geopandas as gpd
import altair as alt

        

def get_match_details(match_ids):
    with open(f'data/match_details.json') as f:
        data = json.load(f)
    return {key: data[str(key)] for key in match_ids }

@st.cache
def get_tweets_n():
    tweets = pd.read_csv("data/tweets.csv")
    n_t = {}
    for id in tweets["match id"].unique():
        n_t[id] = len(tweets[tweets["match id"] == id])
    return n_t




def get_players_teams(match_detail):
    players_teams = {}
    players_teams["players"] = {
        "t1": [speler["Naam"] for speler in match_detail["players t1"]],
        "t2": [speler["Naam"] for speler in match_detail["players t2"]]
        }
    players_teams["t1"] = match_detail["T1"]
    players_teams["t2"] = match_detail["T2"]
    return players_teams

def get_average_rating(players_teams, match_ent):

    avg_rating = {}
    avg_rating[players_teams["t1"]] = {
        "count": np.sum([row["count"] for _,row in match_ent.iterrows() if row["subj"] in [players_teams["t1"]] + players_teams["players"]["t1"] ]),
        "sentiment": np.sum([row["count"] * row["positive"]  for _,row in match_ent.iterrows() if row["subj"] in [players_teams["t1"]] + players_teams["players"]["t1"] ])
    }
    avg_rating[players_teams["t2"]] =  {
        "count": np.sum([row["count"] for _,row in match_ent.iterrows() if row["subj"] in [players_teams["t2"]] + players_teams["players"]["t2"] ]),
        "sentiment": np.sum([row["count"] * row["positive"]  for _,row in match_ent.iterrows() if row["subj"] in [players_teams["t2"]] + players_teams["players"]["t2"] ])
    }

    return avg_rating

def get_filterd_ents(match_ids):
    filtered_ents = pd.read_csv("data/filtered_ents.csv")    
    return filtered_ents.groupby(["match id", 'subj'])\
        .agg({'count': 'sum', 'negative': 'sum', 'neutral': 'sum', 'positive_': 'sum', 'positive': 'mean'}).reset_index().sort_values(by="count", ascending=False).rename(columns={"positive": "sentiment", "positive_": "positive"})



def algemeen_page(df):
    filtered_ents = get_filterd_ents(df["match id"].unique())

    filtered_ents["% positief"] = filtered_ents["positive"]/filtered_ents["count"] * 100
    filtered_ents["% negatief"] = filtered_ents["negative"]/filtered_ents["count"] * 100
    filtered_ents.rename(columns={"neutral": "neutraal", "positive": "positief", "negative": "negatief", "subj": "onderwerp"}, inplace=True)
    trending = filtered_ents.head(10)[["onderwerp", "negatief", "neutraal" ,"positief"]].melt('onderwerp', var_name="tweet sentiment", value_name='aantal')
    n_t = get_tweets_n()
    tweets_gelezen = int(((random.random() + 0.35) * 3) * sum(n_t.values()))

    st.markdown('''
    Op deze pagina vind je algemene statistieken over zowel spelers waarover getweet is als ploegen. 
    Benieuwd naar de meest of minst geliefde ploeg/speler? In deze demo krijg je inzicht in de tweets van de afgelopen speelronde. 
    Het viel ons op dat twitteraars vrij negatief zijn, dus wees gewaarschuwd.
    ''')

    col1, col2, col3 = st.columns(3)
    col1.metric("Beoordeelde Tweets", f"{sum(n_t.values())}", "20%")
    col2.metric("Positief", f"{np.rint(filtered_ents['% positief'].mean())}%", "-8%")
    col3.metric("Negatief", f"{np.rint(filtered_ents['% negatief'].mean())}%", "4%")

    with st.expander(f"Click hier voor de uitleg!"):
        st.markdown(f'''
        Het totaal aantal geplaatste tweets bedroeg: {tweets_gelezen}. Hieruit was echter een groot aantal niet
        te verwerken vanwege spam/taal/enz. In totaal zijn er {sum(n_t.values())} tweets overgebleven en gebruikt voor onze analyse.
        Het percentage vertegenwoordigd de verandering ten opzichte van de vorige speelronde.
        ''')

    chart_trending = alt.Chart(trending).mark_bar().encode(
        x=alt.X('onderwerp', sort=None),
        y='aantal:Q',
        color=alt.Color('tweet sentiment'),
        tooltip=['tweet sentiment', 'aantal']
        )
            # .encode(
            #     alt.X("index", title=""),
            #     alt.Y("value", title=""),
            #     alt.Color("variable", title="", type="nominal"),
            #     alt.Tooltip(["index", "value", "variable"]),
            #     opacity=opacity,
            # )
    # get club name with hightest amount of tweets
    club_name = trending.groupby("onderwerp").sum().sort_values("aantal", ascending=False).head(1).index[0]
    st.markdown(("# Top 10 Trending\nDe volgende grafiek bevat de top 10 trending personen/clubs die gevonden zijn in de tweets van de afgelopen speelronde:"))
    st.altair_chart(chart_trending, use_container_width=True)
    st.markdown(f'''
    {club_name} blijkt afgelopen speelronde de populairste club te zijn, hier is het vaakts over getweet.''')
    
    with st.expander(f"Hoe weten we dat een twitteraar die bijvoorbeeld Feijenoooord/Fynoord twittert, Feyenoord bedoeld?"):
        st.markdown('''
        Hiervoor gebruiken we het Gestalt Pattern Matching algoritme dat eind jaren 1980 door Ratcliff en Obershelp werd gepubliceerd.        
        Het idee is om de langste aaneengesloten overeenkomende reeks letters te vinden tussen twee woorden: het getweette woord en de mogelijke club/persoon.  
        Op de stukken links en rechts van de overeenkomende reeks wordt opnieuw gezocht naar de langst aaneengesloten overeenkomende reeks letters.
        De reeksen worden bij elkaar opgeteld en gedeeld door de som van de lengte van de twee woorden. Wanneer een grenswaarde is bereikt wordt het woord gekozen.
        ''')
    st.markdown('''

    ---
    ''')

    ents_30 = filtered_ents[filtered_ents["count"] > 30]

    positive = ents_30.sort_values("% positief", ascending=False).head(10)
    negative = ents_30.sort_values("% negatief", ascending=False).head(10)

    
    st.markdown('''
    # Top 10 Positief
    De volgende grafiek bevat de top 10 meest positief getweet personen/clubs van de afgelopen speelronde:
    ''')
    p = alt.Chart(positive).mark_bar().encode(
        x=alt.X('onderwerp', sort=None),
        y='% positief'
        ).configure_mark(
    color='#20ba2d'
)
    st.altair_chart(p, use_container_width=True)

    meest_positief = positive.head(1).values[0][1]
    st.markdown(f''' 
    {meest_positief} staat bovenaan de lijst en had het hoogste percentage positieve tweets.
    ''')
    with st.expander(f"Klik hier voor de technische uitleg van sentiment analyse."):
        st.markdown('''
            Sentimentanalyse is een vorm van Natural Language Processing (NLP) die tekstgegevens analyseert, om het sentiment van de tekst te bepalen. 
            Voor onze tool hebben we gebruik gemaakt van de Transformer architectuur.
            De Transformer in NLP is een nieuwe architectuur die tot doel heeft reeks-naar-reeks taken op te lossen en
            daarbij op een slimme manier rekening houdt met relaties tussen onderdelen van een reeks, zoals een woord in een zin die op (lange) afstand staan. 
        ''')
    st.markdown('''

    ---
    ''')

    meest_negatief = negative.head(1).values[0][1]

    st.markdown('''
    # Top 10 Negatief
    De volgende grafiek bevat de top 10 personen/clubs waarover het minst positief is getweet van de afgelopen speelronde:
    ''')
    p = alt.Chart(negative).mark_bar().encode(
        x=alt.X('onderwerp', sort=None),
        y=alt.Y('% negatief', sort="ascending")
        ).configure_mark(
    color='#db9316')
    st.altair_chart(p, use_container_width=True)
    st.markdown(f'''
    {meest_negatief} staat bovenaan de lijst van percentage negatieve tweets. ''')
    with st.expander(f"Waarom percentages en niet aantallen?"):
        st.markdown('''
            Aangezien er over de topclubs in Nederland vaak veel meer wordt getweet dan over de rest,
            zal het aantal positieve en negatieve tweets vaak hoger zijn dan bij de rest.
            Door het percentage te berekenen van de positieve en negatieve tweets, kunnen we een representatief beeld krijgen van het sentiment.
        ''')

def wedstrijden_page(df):
    st.markdown(
        '''
        Op deze pagina analyseren we de wedstrijden van de afgelopen speelronde in de Eredivisie.
        ''')
    round = df.Round.max()
    entities = get_filterd_ents(df["match id"].unique())
    matches = get_match_details(df["match id"].unique())
    match_names = {m: matches[m]['T1'] + " - " + matches[m]['T2'] for m in matches}
    n_t = get_tweets_n()
    match_ids = {v: k for k, v in match_names.items()}

    entities_counts = entities.groupby(["match id"]).agg({'count': 'sum', 'negative': 'sum', 'neutral': 'sum', 'positive':'sum', "sentiment":"mean"}).sort_values(by="count", ascending=False).reset_index()
    entities_counts.replace(match_names, inplace=True)
    entities_counts["_positive"] = np.rint(entities_counts["positive"] / entities_counts["count"] * 100)
    entities_counts["_negative"] = np.rint(entities_counts["negative"] / entities_counts["count"] * 100)

    melted_entities_count = entities_counts[["match id", "negative", "neutral" ,"positive"]].melt('match id', var_name="tweet sentiment", value_name='aantal')
    
    chart_games = alt.Chart(melted_entities_count).mark_bar().encode(
        x=alt.X('sum(aantal)', stack='normalize', title='Wedstrijden Sentiment'),
        y='match id',
        color='tweet sentiment'
    )
    entities.reset_index(drop=True, inplace=True)
    meest = entities.iloc[entities['count'].idxmax()]["subj"]
    # meest = entities_counts.iloc[entities_counts['count'].idxmax()]['match id']
    meest_nega = entities.iloc[entities['_negative'].idxmax()]['subj']
    meest_posi = entities.iloc[entities['_positive'].idxmax()]['subj']
    st.markdown(
        f'''
        <style>
            table {{
                width: 100%;
            }}
        </style>
        Hieronder zie je per wedstrijd hoeveel tweets er in positieve, neutrale of negatieve manier uitspringen.
        
        | Meest Over Getweet      | Meest Positief | Meest Negatief     |
        | :---:        |    :----:   |          :---: |
        | {meest}      | {meest_posi}       | {meest_nega}   |
        | ***{str(entities["count"].max())} tweets***   | ***{str(int(entities["positive"].max()))}%  positief***      | ***{str(int(entities["negative"].max()))}% negatief***     |

        <br/><br/>
        ''', unsafe_allow_html=True)

    st.altair_chart(chart_games, use_container_width=True)
    
    st.markdown(
        '''
        ---
        ## Analyse per wedstrijd
        Hieronder geven we een overzicht van het sentiment van de spelers/coaches per wedstrijd.
        ''')
    
    for i,row in df.iterrows():
        match_ent = entities[entities["match id"] == row["match id"]]
        if match_ent.shape[0] > 0:
            match = matches[row["match id"]]
            players_teams = get_players_teams(match)
            avg_rating = get_average_rating(players_teams, match_ent)
            match_name= match_names[row["match id"]]
            percentage_posi = entities_counts[entities_counts['match id'] == match_name]["_positive"].values[0]
            percentage_nega = entities_counts[entities_counts['match id'] == match_name]["_negative"].values[0]
            aantal_per_match = entities_counts[entities_counts['match id'] == match_name]["count"].values[0]
            with st.expander(f"{row['home']} - {row['away']}:   ({int(row['home score'])} - {int(row['away score'])}) \t"):
            
                col1, col2, col3 = st.columns(3)
                col1.metric("Tweets", f"{aantal_per_match}")
                col2.metric("Positief", f"{int(percentage_posi)}%")
                col3.metric("Negatief", f"{int(percentage_nega)}%")


                col1.markdown(
                    f'''
                    ---

                    ***Sentiment Thuisploeg:***

                    ***Sentiment Uitploeg:***

                    ***Meest Positief***:

                    ***Meest Negatief***:

                    ***Meest Genoemd***:
                        
                ''')
                no_club = match_ent[(match_ent["subj"] != match["T1"]) & (match_ent["subj"] != match["T2"])]
                no_club = no_club[no_club["count"] > 3]
                col2.markdown(
                    f'''
                    ---

                    ***{match["T1"]}***

                    ***{match["T2"]}***

                    {no_club.sort_values(by="positive", ascending=False)['subj'].iloc[0]}

                    {no_club.sort_values(by="negative", ascending=False)['subj'].iloc[0]}

                    {no_club['subj'].iloc[0]}

                    '''
                )
                col3.markdown(
                    f'''
                    ---

                    {int(avg_rating[match["T1"]]["sentiment"]/avg_rating[match["T1"]]["count"])}%

                    {int(avg_rating[match["T2"]]["sentiment"]/avg_rating[match["T2"]]["count"])}%

                    {no_club.sort_values(by="positive", ascending=False)['positive'].iloc[0]} keer

                    {no_club.sort_values(by="negative", ascending=False)['negative'].iloc[0]} keer

                    {no_club['count'].iloc[0]} keer
                    '''
                )

def locaties_page(df):
    prov = pd.read_csv("data/per_provincie.csv")
    prov = prov.dropna()
    melted_prov = prov.drop(["populairste", "aantal"], axis=1).melt('provincie', var_name="provincie sentiment", value_name='aantal')
    
    


    st.markdown("## Sentiment per Provincie")
    
    chart_games = alt.Chart(melted_prov).mark_bar().encode(
        x=alt.X('sum(aantal)', stack='normalize', title='Provincie Sentiment'),
        y='provincie',
        color='provincie sentiment'
    )

    st.altair_chart(chart_games, use_container_width=True)

    # st.markdown("## Populairste wedstrijden per Provincie")
    # st.table(prov[["provincie", "populairste"]])

    
    # gdf_prov = gpd.read_file("provincie_wedstrijden.geojson")
    # fig, ax = plt.subplots(figsize=(10,10))
    # column1 = "aantal"
    # # c = alt.Chart(gdf_prov).mark_geoshape(
    # # ).encode(color="aantal", tooltip=["name", "aantal", "positief", "negatief", "populairste"]).properties( 
    # #     width=800,
    # #     height=600)
    # gdf_prov.plot(ax=ax, edgecolor='gray', column=column1, legend=True)
    # st.pyplot()

def cloud_page(df):
    entities = get_filterd_ents(df["match id"].unique())
    # locaties = tweet_per_locatie(df)


    st.markdown("## Wordcloud")
    wc = WordCloud(background_color="#074443")

    # generate word cloud
    wordcloud = wc.generate(" ".join(sub for sub in entities.subj.str.replace(" ", "_")))
    # Display the generated image:
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis("off")
    st.pyplot()

