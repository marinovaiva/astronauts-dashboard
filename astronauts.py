# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

# Configure the Streamlit page
st.set_page_config(page_title="Astronaut Dashboard", layout="wide")

# --------------- Data Loading & Preprocessing ---------------
@st.cache(allow_output_mutation=True)
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=['Mission.Year'])
    df['year'] = df['Mission.Year'].dt.year
    return df

# Load data (ensure 'astronauts.csv' is in the repo root)
astro = load_data('astronauts.csv')

# Normalize column names & clean up fields
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
    "Year range",
    min_value=years[0],
    max_value=years[-1],
    value=(years[0], years[-1]),
    step=1
)

genders = astro['profile_gender'].dropna().unique().tolist()
selected_genders = st.sidebar.multiselect(
    "Gender", options=genders, default=genders
)

nats = astro['profile_nationality'].dropna().unique().tolist()
selected_nats = st.sidebar.multiselect(
    "Nationality", options=nats, default=nats
)

# Apply filters
df_filt = astro[
    (astro['year'] >= selected_years[0]) &
    (astro['year'] <= selected_years[1]) &
    (astro['profile_gender'].isin(selected_genders)) &
    (astro['profile_nationality'].isin(selected_nats))
]

# --------------- Plot Functions ---------------

def plot_cumulative(df: pd.DataFrame) -> px.Figure:
    yearly = (
        df
        .groupby('year', as_index=False)
        .agg(cum_overall=('profile_astronaut_numbers_overall', 'max'))
    )
    fig = px.line(
        yearly,
        x='year',
        y='cum_overall',
        markers=True,
        title="Cumulative Astronauts (Overall)",
        labels={'cum_overall': 'Total # Astronauts'}
    )
    fig.update_layout(
        xaxis=dict(
            range=[years[0], years[-1]],
            tickmode='linear',
            dtick=5,
            tickangle=-45
        ),
        width=600,
        height=400
    )
    return fig


def plot_top_nats(df: pd.DataFrame) -> px.Figure:
    top10 = df['profile_nationality'].value_counts().nlargest(10).index
    grp = (
        df[df['profile_nationality'].isin(top10)]
        .groupby(['profile_nationality', 'profile_gender'], as_index=False)
        .size()
        .rename(columns={'size': 'count'})
    )
    fig = px.bar(
        grp,
        x='profile_nationality',
        y='count',
        color='profile_gender',
        barmode='group',
        title="Top 10 Nationalities by Gender",
        labels={'profile_nationality': 'Country', 'count': '# Astronauts'}
    )
    fig.update_layout(xaxis_tickangle=-45, width=600, height=400)
    return fig


def plot_gender_pie(df: pd.DataFrame) -> px.Figure:
    unique_ = df.drop_duplicates(subset='profile_name')
    gc = (
        unique_['profile_gender']
        .value_counts(dropna=False)
        .reset_index(name='count')
        .rename(columns={'index': 'gender'})
    )
    if gc.empty:
        return px.Figure()
    fig = px.pie(
        data_frame=gc,
        names='gender',
        values='count',
        hole=0.3,
        title="Unique Astronauts by Gender"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(width=600, height=400)
    return fig


def plot_choropleth(df: pd.DataFrame) -> px.Figure:
    country_counts = (
        df
        .groupby('profile_nationality', as_index=False)
        .agg(count=('profile_astronaut_numbers_nationwide', 'max'))
    )
    fig = px.choropleth(
        country_counts,
        locations='profile_nationality',
        locationmode='country names',
        color='count',
        hover_name='profile_nationality',
        title='Unique Astronauts per Country'
    )
    fig.update_layout(
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0),
        width=600,
        height=400
    )
    return fig

# --------------- Main Layout ---------------
st.title("🚀 Astronaut Dashboard")
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(plot_cumulative(df_filt), use_container_width=True)
    pie_fig = plot_gender_pie(df_filt)
    st.plotly_chart(pie_fig, use_container_width=True)

with col2:
    st.plotly_chart(plot_top_nats(df_filt), use_container_width=True)
    st.plotly_chart(plot_choropleth(df_filt), use_container_width=True)
