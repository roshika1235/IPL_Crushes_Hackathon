app_code = """import streamlit as st

st.set_page_config(page_title="IPL Data Analysis", page_icon="🏏", layout="wide")
st.title("🏏 IPL Data Analysis — 5 Seasons")

# ── Load & Clean Data ─────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("cric_info.csv")

    df['date'] = pd.to_datetime(df['date'])

    df['season'] = df['season'].astype(str)
    df = df[~df['season'].str.contains('2007')]
    df['season'] = df['season'].str.split('/').str[0].astype(int)

    df = df.dropna(subset=['city'])
    df = df.dropna(subset=['win_by_wickets'])
    df['win_by_wickets'] = df['win_by_wickets'].astype(int)
    df['runs_total'] = pd.to_numeric(df['runs_total'], errors='coerce')

    # Q1
    df['toss_and_match_win'] = df['toss_winner'] == df['winner']

    # Q2
    df['runs_on_ball'] = (
        df['runs_batter'] + df['extras_wides'] + df['extras_noballs']
        + df['extras_byes'] + df['extras_legbyes']
    )

    def get_phase(over):
        if over < 6:   return 'Powerplay'
        elif over < 16: return 'Middle Overs'
        else:           return 'Death Overs'

    df['phase'] = df['over'].apply(get_phase)

    return df

df = load_data()

# ── Q1: Toss vs Match Win ─────────────────────────────────────
st.header("Q1 — Does Winning the Toss Help?")

toss_win  = df['toss_and_match_win'].mean() * 100
toss_lose = 100 - toss_win

fig1, ax1 = plt.subplots(figsize=(5, 3))
ax1.bar('Toss Winner', toss_win,  color='green', label='Toss Winner')
ax1.bar('Toss Loser',  toss_lose, color='red',   label='Toss Loser')
ax1.set_title('Toss Winner vs Loser Win Rate')
ax1.set_ylabel('Win Rate (%)')
ax1.legend()
st.pyplot(fig1)

st.info("Winning the toss only increases win probability by ~7–8%. On-field performance matters more than the coin flip.")

# ── Q2: Phase Analysis ────────────────────────────────────────
st.header("Q2 — Which Phase is Most Linked to Winning?")

phase_runs = df.groupby(['match_id', 'batting_team', 'phase'])['runs_on_ball'].sum().reset_index()
match_winners = df[['match_id', 'winner']].drop_duplicates()
phase_runs = phase_runs.merge(match_winners, on='match_id')
phase_runs['team_won'] = phase_runs['batting_team'] == phase_winners['winner']

phase_summary = phase_runs.groupby(['phase', 'team_won'])['runs_on_ball'].mean().unstack()
phase_summary.columns = ['Lost', 'Won']

phase_order = ['Powerplay', 'Middle Overs', 'Death Overs']
won_avg  = phase_summary.loc[phase_order, 'Won'].values
lost_avg = phase_summary.loc[phase_order, 'Lost'].values
x = np.arange(len(phase_order))

fig2, ax2 = plt.subplots(figsize=(6, 3))
ax2.bar(x - 0.2, won_avg,  width=0.4, color='green', label='Winner')
ax2.bar(x + 0.2, lost_avg, width=0.4, color='red',   label='Loser')
ax2.set_xticks(x)
ax2.set_xticklabels(phase_order)
ax2.set_title('Avg Runs per Phase — Winners vs Losers')
ax2.set_ylabel('Average Runs')
ax2.legend()
st.pyplot(fig2)

st.info("Winning teams dominate in Powerplay, maintain momentum in Middle Overs, and finish strong in Death Overs.")

# ── Q3: Top 5 Batters & Bowlers ───────────────────────────────
st.header("Q3 — Top 5 Batters & Bowlers across 5 Seasons")

top_batters = (
    df.groupby('batter')['runs_batter'].sum()
    .reset_index()
    .rename(columns={'runs_batter': 'Total Runs'})
    .sort_values('Total Runs', ascending=False)
    .head(5)
    .reset_index(drop=True)
)
top_batters.index += 1
top_batters.rename(columns={'batter': 'Batter'}, inplace=True)

legal_df = df[(df['extras_wides'] == 0) & (df['extras_noballs'] == 0)]
bowler_wickets = (
    df[df['wicket_kind'].notna() & (df['wicket_kind'] != 'run out')]
    .groupby('bowler')['wicket_kind'].count()
    .reset_index().rename(columns={'wicket_kind': 'Total Wickets'})
)
bowler_runs  = legal_df.groupby('bowler')['runs_on_ball'].sum().reset_index().rename(columns={'runs_on_ball': 'Runs Conceded'})
bowler_balls = legal_df.groupby('bowler').size().reset_index(name='Balls')
bowlers_df   = bowler_wickets.merge(bowler_runs, on='bowler').merge(bowler_balls, on='bowler')
bowlers_df['Economy'] = (bowlers_df['Runs Conceded'] / bowlers_df['Balls'] * 6).round(2)

top_bowlers = (
    bowlers_df.sort_values('Total Wickets', ascending=False)
    .head(5).reset_index(drop=True)
)
top_bowlers.index += 1
top_bowlers.rename(columns={'bowler': 'Bowler'}, inplace=True)

col1, col2 = st.columns(2)
with col1:
    st.subheader("🏏 Top 5 Batters")
    st.dataframe(top_batters[['Batter', 'Total Runs']], use_container_width=True)
with col2:
    st.subheader("🎯 Top 5 Bowlers")
    st.dataframe(top_bowlers[['Bowler', 'Total Wickets', 'Economy']], use_container_width=True)

# ── Surprise Insight ──────────────────────────────────────────
st.header("💡 Surprise Insight — Death Over Finishers")

death = df[df['over'] >= 16].groupby('batter')['runs_batter'].sum()
power = df[df['over'] < 6].groupby('batter')['runs_batter'].sum()
finishers = (death - power).sort_values(ascending=False).head(5).reset_index()
finishers.columns = ['Batter', 'Death - Powerplay Runs']
finishers.index += 1

st.dataframe(finishers, use_container_width=True)
st.info("These batters score far more in death overs than powerplay — pure finishers who thrive under pressure when it matters most.")"""

with open('app.py', 'w') as f:
    f.write(app_code)

print("Streamlit app saved to app.py")
