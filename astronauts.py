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
)

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
COLOR_SEQ = px.colors.sequential.Plasma
#COLOR_SEQ = COLOR_SEQ1[::-1]

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
        title="Number of Astronauts to have been in Space",
        labels={'cum_overall':'Total # Astronauts'},
        color_discrete_sequence=COLOR_SEQ
    )
    fig.update_layout(
        xaxis=dict(
            range=[1961,2019],
            tickmode='linear',
            tick0=1965,
            dtick=5,
            tickangle=-45
        ),
        
        height=800
    )
    fig.update_layout(
  font=dict(size=40)
)
    return fig


def plot_top_nats(df):
    """
    Plot top 10 nationalities by gender as a grouped bar chart with Plasma colors, sorted by total count.
    """
    # ADDED: compute top 10 nationalities by total count for sorting
    top10_series = df['profile_nationality'].value_counts().nlargest(10)  # ADDED
    top10_list = top10_series.index.tolist()  # ADDED

    # Filter and group by nationality and gender
    grp = (
        df[df['profile_nationality'].isin(top10_list)]  # CHANGED: use top10_list, not alphabetical
          .groupby(['profile_nationality', 'profile_gender'], as_index=False)
          .size()
          .rename(columns={'size': 'count'})
    )

    # CHANGED: enforce categorical ordering to sort countries by total count
    grp['profile_nationality'] = pd.Categorical(
        grp['profile_nationality'],
        categories=top10_list,
        ordered=True
    )  # ADDED

    # CHANGED: invert female/male colors by reversing the Plasma palette

    # Create bar chart with reversed colors
    fig = px.bar(
        grp,
        x='profile_nationality',
        y='count',
        color='profile_gender',
        barmode='group',
        title="Top 10 Nationalities by Gender",
        labels={'profile_nationality': 'Country', 'count': '# Astronauts'},
        color_discrete_sequence=COLOR_SEQ,  # CHANGED: use inverted colors
        template='plotly_white'
    )

    # CHANGED: update legend title
    # CHANGED: update legend position below chart, centered
    fig.update_layout(
        xaxis_tickangle=-45,
        
        height=800,
        showlegend=False
        
    )  # CHANGED
    return fig


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
        names='profile_gender',
        values='count',
        hole=0.3,
        title="Gender Split of Astronauts",
        color_discrete_sequence=COLOR_SEQ
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    fig.update_layout(height=800,
                      showlegend=False)
    return fig

# Plot 4: Choropleth map of unique astronauts per country
def plot_choropleth(df):
    country_counts = (
        df.groupby('profile_nationality', as_index=False)
          .agg(count=('profile_astronaut_numbers_nationwide','max'))
    )
    fig_choro = px.choropleth(
        country_counts,
        locations='profile_nationality',
        locationmode='country names',
        color='count',
        hover_name='profile_nationality',
        color_continuous_scale='Plasma',
        title='Astronaut Country of Origin',
        template='plotly_white'
    )
    # Make background transparent
    fig_choro.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=50, b=0),
        
        height=800
    )
    
    return fig_choro

# 5) Pie chart of EVA activity (duration > 0)
def plot_eva_pie(df):
    unique_ = df.drop_duplicates(subset='profile_name')
    ec = (
        unique_["profile_eva_activity"]
               .value_counts()
               .reset_index(name='count')
               .rename(columns={'index':'eva_activity'})
    )
    fig = px.pie(
        ec, names='eva_activity', values='count', hole=0.3,
        title="EVA Activity (Any EVA vs. None)",
        color_discrete_sequence=COLOR_SEQ,
        height=600,
        template=None
    )
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig


# --------------- Layout ---------------
st.title("🚀 Astronaut Dashboard")
st.header("👨‍🚀🌌There have been 565 people is space so far!")
st.markdown("As of 2020")
st.plotly_chart(plot_cumulative(df_filt), use_container_width=True)
st.header("🇺🇸🏆 The United States have the lead!")
st.plotly_chart(plot_top_nats(df_filt), use_container_width=True)
st.header("🗺️🚀 So far, 39 nationalities have been to space!")
st.plotly_chart(plot_choropleth(df_filt), use_container_width=True)
st.header("🤔👨‍🚀They keep sending men to space?")
st.plotly_chart(plot_gender_pie(df_filt), use_container_width=True)
#st.header("Extravehicular Activity Overview")
#st.plotly_chart(plot_eva_pie(df_filt), use_container_width=True)
    
    

