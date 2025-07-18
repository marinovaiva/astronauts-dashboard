# app.py


import streamlit as st
import pandas as pd
import plotly.express as px

# configure page layout
st.set_page_config(layout="wide")

# --------------- Data Loading & Preprocessing ---------------
@st.cache_data
def load_data(path):
    df = pd.read_csv(path, parse_dates=['Mission.Year'])
    df['year'] = df['Mission.Year'].dt.year
    return df

# load once
astro = load_data('astronauts.csv')

# normalize column names & clean up mission_role, EVA flag
astro.columns = (
    astro.columns
         .str.lower()
         .str.replace('.', '_', regex=False)
         .str.replace(' ', '_', regex=False)
)
astro['mission_role'] = (
    astro['mission_role']
         .str.lower()
         .str.replace('other (journalist)', 'journalist', regex=False)
         .str.replace('other (space tourist)', 'space tourist', regex=False)
         .str.replace('psp', 'payload specialist', regex=False)
         .str.replace('msp', 'mission specialist', regex=False)
)
astro['profile_eva_activity'] = (
    astro['profile_lifetime_statistics_eva_duration'] != 0
).map({False: 'no', True: 'yes'})

# --------------- Sidebar Filters ---------------
st.sidebar.header("🔎 Filters")

years = sorted(astro['year'].unique())
selected_years = st.sidebar.slider(
    "Year range", min_value=years[0], max_value=years[-1],
    value=(1961, 2019)
)

genders = astro['profile_gender'].unique().tolist()
selected_genders = st.sidebar.multiselect(
    "Gender", options=genders, default=genders
)

nats = astro['profile_nationality'].unique().tolist()
selected_nats = st.sidebar.multiselect(
    "Nationality", options=nats, default=nats
)

# apply filters
df_filt = astro[
    (astro['year'] >= selected_years[0]) &
    (astro['year'] <= selected_years[1]) &
    (astro['profile_gender'].isin(selected_genders)) &
    (astro['profile_nationality'].isin(selected_nats))
]

# --------------- Plot Functions ---------------

# Plot 1: Cumulative overall astronauts over time
def plot_cumulative(df):
    sorted_ = df.sort_values(
        ['mission_year','profile_astronaut_numbers_overall']
    )
    yearly = (
        sorted_
          .groupby('year', as_index=False)
          .agg({'profile_astronaut_numbers_overall':'max'})
          .rename(columns={'profile_astronaut_numbers_overall':'cum_overall'})
    )
    fig = px.line(
        yearly,
        x='year',
        y='cum_overall',
        markers=True,
        title="Cumulative Astronauts (Overall)",
        labels={'cum_overall':'Total # Astronauts'}
    )
    fig.update_layout(
        xaxis=dict(
            range=[1961,2019],
            tickmode='linear',
            tick0=1965,
            dtick=5,
            tickangle=-45
        ),
        width=600,
        height=400
    )
    return fig

# Plot 2: Top 10 nationalities by count (split by gender)
def plot_top_nats(df):
    top10 = (
        df['profile_nationality']
          .value_counts()
          .nlargest(10)
          .index.tolist()
    )
    sub = df[df['profile_nationality'].isin(top10)]
    grp = (
        sub
          .groupby(['profile_nationality','profile_gender'])
          .size()
          .reset_index(name='count')
    )
    fig = px.bar(
        grp,
        x='profile_nationality',
        y='count',
        color='profile_gender',
        barmode='group',
        title="Top 10 Nationalities by Gender",
        labels={'profile_nationality':'Country','count':'# Astronauts'}
    )
    fig.update_layout(xaxis_tickangle=-45, width=600, height=400)
    return fig

# Plot 3: Pie chart of unique astronauts by gender
def plot_gender_pie(df):
    unique_ = df.drop_duplicates(subset='profile_name')
    gc = (
        unique_['profile_gender']
               .value_counts()
               .reset_index(name='count')
               .rename(columns={'index':'gender'})
    )
    fig = px.pie(
        gc,
        names='gender',
        values='count',
        hole=0.3,
        title="Unique Astronauts by Gender"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(width=600, height=400)
    return fig

# Plot 4: Choropleth map of unique astronauts per country
def plot_choropleth(df):
    country_counts = (
        df
          .groupby('profile_nationality')['profile_astronaut_numbers_nationwide']
          .max()
          .reset_index(name='count')
    )
    fig = px.choropleth(
        country_counts,
        locations='profile_nationality',
        locationmode='country names',
        color='count',
        hover_name='profile_nationality',
        color_continuous_scale='Viridis',
        title='Unique Astronauts per Country'
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0),
        width=600,
        height=400
    )
    return fig

# --------------- Layout ---------------
st.title("🚀 Astronaut Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(plot_cumulative(df_filt), use_container_width=True)
    st.plotly_chart(plot_gender_pie(df_filt), use_container_width=True)

with col2:
    st.plotly_chart(plot_top_nats(df_filt), use_container_width=True)
    st.plotly_chart(plot_choropleth(df_filt), use_container_width=True)

