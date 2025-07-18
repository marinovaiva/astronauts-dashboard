# app.py

import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")

@st.cache_data
def load_data(path):
    df = pd.read_csv(path, parse_dates=['Mission.Year'])
    df['year'] = df['Mission.Year'].dt.year
    return df

# 1) Load once
astro = load_data('astronauts.csv')

astro.columns = astro.columns.str.lower().str.replace('.', '_').str.replace(' ', '_')
astro['mission_role'] = astro['mission_role'].str.lower()
astro['mission_role'] = astro['mission_role'].str.replace('other (journalist)', 'journalist').str.replace('other (space tourist)', 'space tourist')
astro['mission_role'] = astro['mission_role'].str.replace('psp', 'payload specialist').str.replace('msp', 'mission specialist')
astro['profile_eva_activity'] = (astro['profile_lifetime_statistics_eva_duration'] != 0)
astro['profile_eva_activity'] = astro['profile_eva_activity'].replace({False: 'no', True: 'yes'})

st.sidebar.header("🔎 Filters")
# 2) Define filters on the raw df
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

# 3) Apply filters once
df_filt = astro[
    (astro['year'] >= selected_years[0]) &
    (astro['year'] <= selected_years[1]) &
    (astro['profile_gender'].isin(selected_genders)) &
    (astro['profile_nationality'].isin(selected_nats))
]

st.title("🚀 Astronaut Dashboard")

# — Plot 1: Cumulative overall astronauts over time —
def plot_cumulative(df):
    sorted_ = df.sort_values(['mission_year','profile_astronaut_numbers_overall'])
    yearly = (sorted_
                .groupby('year', as_index=False)
                .agg({'profile_astronaut_numbers_overall':'max'})
                .rename(columns={'profile_astronaut_numbers_overall':'cum_overall'}))
    fig = px.line(
        yearly, x='year', y='cum_overall', markers=True,
        title="Cumulative Astronauts (Overall)",
        labels={'cum_overall':'Total # Astronauts'}
    )
    fig.update_layout(xaxis=dict(range=[1961,2019], tickmode='linear',
                                 tick0=1965, dtick=5, tickangle=-45),
                      width=600, height=400)
    return fig

# — Plot 2: Top 10 nationalities by count (split by gender) —
def plot_top_nats(df):
    # pick top 10 by overall count
    top10 = (df['profile_nationality']
               .value_counts()
               .nlargest(10)
               .index.tolist())
    sub = df[df['profile_nationality'].isin(top10)]
    grp = (sub.groupby(['profile_nationality','profile_gender'])
              .size().reset_index(name='count'))
    fig = px.bar(
        grp, x='profile_nationality', y='count', color='profile_gender',
        barmode='group', title="Top 10 Nationalities by Gender",
        labels={'profile_nationality':'Country','count':'# Astronauts'}
    )
    fig.update_layout(xaxis_tickangle=-45, width=600, height=400)
    return fig

# — Plot 3: Pie chart of unique astronauts by gender —
def plot_gender_pie(df):
    unique_ = df.drop_duplicates(subset='profile_name')
    gc = (unique_['profile_gender']
             .value_counts()
             .reset_index(name='count')
             .rename(columns={'index':'gender'}))
    fig = px.pie(
        gc, names='profile_gender', values='count', hole=0.3,
        title="Unique Astronauts by Gender"
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(width=600, height=400)
    return fig

# 4) Layout in two columns
col1, col2 = st.columns(2)
with col1:
    st.plotly_chart(plot_cumulative(df_filt), use_container_width=True)
    st.plotly_chart(plot_gender_pie(df_filt), use_container_width=True)

with col2:
    st.plotly_chart(plot_top_nats(df_filt), use_container_width=True)
    # any additional plots go here…

