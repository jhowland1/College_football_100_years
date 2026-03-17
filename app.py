import pandas as pd
import numpy as np
import plotly.express as px
from dash import Dash, Input, Output, dcc, html, dash_table

def card_style():
    return {
        "backgroundColor": "#111827",
        "padding": "18px",
        "borderRadius": "12px",
        "border": "1px solid #334155",
    }


def panel_style():
    return {
        "backgroundColor": "#111827",
        "padding": "18px",
        "borderRadius": "12px",
        "border": "1px solid #334155",
    }
data_path = "data/cfb_games.pkl"

df = pd.read_pickle(data_path)

df = df.copy()
df["date"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
df["year"] = df["date"].dt.year
df["decade"] = (df["year"] // 10) * 10

team1_df = df[["date", "year", "decade", "Team1", "Conf1"]].copy()
team1_df.columns = ["date", "year", "decade", "team", "conference"]

team2_df = df[["date", "year", "decade", "Team2", "Conf2"]].copy()
team2_df.columns = ["date", "year", "decade", "team", "conference"]

app_df = pd.concat([team1_df, team2_df], ignore_index=True)

app_df["team"] = app_df["team"].astype(str).str.strip()
app_df["conference"] = app_df["conference"].astype(str).str.strip()

app_df["team"] = app_df["team"].replace({"nan": np.nan, "None": np.nan})
app_df["conference"] = app_df["conference"].replace({"nan": np.nan, "None": np.nan})

app_df = app_df.dropna(subset=["team", "year", "decade"])
app_df["conference"] = app_df["conference"].fillna("Unknown")
app_df["year"] = app_df["year"].astype(int)
app_df["decade"] = app_df["decade"].astype(int)

conference_options = [{"label": "All Conferences", "value": "All"}] + [
    {"label": conf, "value": conf}
    for conf in sorted(app_df["conference"].unique())
]

decade_options = [{"label": "All Decades", "value": "All"}] + [
    {"label": f"{decade}s", "value": decade}
    for decade in sorted(app_df["decade"].unique())
]

app = Dash(__name__)
server = app.server
app.title = "College Football Dashboard"

app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#0f172a",
        "minHeight": "100vh",
        "padding": "24px",
        "color": "white",
    },
    children=[
        html.H1("College Football Conference Dashboard"),
        html.P("Filter by conference and decade."),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr",
                "gap": "16px",
                "marginBottom": "24px",
            },
            children=[
                html.Div(
                    [
                        html.Label("Conference"),
                        dcc.Dropdown(
                            id="conference-filter",
                            options=conference_options,
                            value="All",
                            clearable=False,
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.Label("Decade"),
                        dcc.Dropdown(
                            id="decade-filter",
                            options=decade_options,
                            value="All",
                            clearable=False,
                        ),
                    ]
                ),
            ],
        ),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(4, 1fr)",
                "gap": "16px",
                "marginBottom": "24px",
            },
            children=[
                html.Div(id="card-total", style=card_style()),
                html.Div(id="card-teams", style=card_style()),
                html.Div(id="card-first", style=card_style()),
                html.Div(id="card-last", style=card_style()),
            ],
        ),
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1.2fr 1fr",
                "gap": "24px",
            },
            children=[
                html.Div(
                    style=panel_style(),
                    children=[
                        html.H3("Top Teams"),
                        dash_table.DataTable(
                            id="teams-table",
                            columns=[
                                {"name": "Team", "id": "team"},
                                {"name": "Conference", "id": "conference"},
                                {"name": "Appearances", "id": "appearances"},
                                {"name": "First Year", "id": "first_year"},
                                {"name": "Last Year", "id": "last_year"},
                            ],
                            page_size=15,
                            sort_action="native",
                            style_table={"overflowX": "auto"},
                            style_header={
                                "backgroundColor": "#1e293b",
                                "color": "white",
                                "fontWeight": "bold",
                            },
                            style_cell={
                                "backgroundColor": "#111827",
                                "color": "white",
                                "padding": "10px",
                                "textAlign": "left",
                            },
                        ),
                    ],
                ),
                html.Div(
                    style=panel_style(),
                    children=[
                        html.H3("Top Teams by Appearances"),
                        dcc.Graph(id="teams-bar-chart"),
                    ],
                ),
            ],
        ),
    ],
)


def card_style():
    return {
        "backgroundColor": "#111827",
        "padding": "18px",
        "borderRadius": "12px",
        "border": "1px solid #334155",
    }


def panel_style():
    return {
        "backgroundColor": "#111827",
        "padding": "18px",
        "borderRadius": "12px",
        "border": "1px solid #334155",
    }


def make_card(title, value):
    return [
        html.Div(title, style={"color": "#94a3b8", "fontSize": "14px", "marginBottom": "8px"}),
        html.Div(str(value), style={"fontSize": "28px", "fontWeight": "bold"}),
    ]


@app.callback(
    Output("card-total", "children"),
    Output("card-teams", "children"),
    Output("card-first", "children"),
    Output("card-last", "children"),
    Output("teams-table", "data"),
    Output("teams-bar-chart", "figure"),
    Input("conference-filter", "value"),
    Input("decade-filter", "value"),
)
def update_dashboard(selected_conference, selected_decade):
    filtered = app_df.copy()

    if selected_conference != "All":
        filtered = filtered[filtered["conference"] == selected_conference]

    if selected_decade != "All":
        filtered = filtered[filtered["decade"] == selected_decade]

    if filtered.empty:
        fig = px.bar(title="No data available")
        fig.update_layout(
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            font_color="white",
        )
        return (
            make_card("Total Appearances", 0),
            make_card("Unique Teams", 0),
            make_card("First Year", "—"),
            make_card("Last Year", "—"),
            [],
            fig,
        )

    total_appearances = len(filtered)
    unique_teams = filtered["team"].nunique()
    first_year = filtered["year"].min()
    last_year = filtered["year"].max()

    summary = (
        filtered.groupby(["team", "conference"])
        .agg(
            appearances=("team", "size"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
        .sort_values(["appearances", "team"], ascending=[False, True])
    )

    table_data = summary.head(15).to_dict("records")
    chart_df = summary.head(10).sort_values("appearances", ascending=True)

    fig = px.bar(
        chart_df,
        x="appearances",
        y="team",
        color="conference",
        orientation="h",
        title="Top 10 Teams",
    )
    fig.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="white",
    )

    return (
        make_card("Total Appearances", f"{total_appearances:,}"),
        make_card("Unique Teams", f"{unique_teams:,}"),
        make_card("First Year", first_year),
        make_card("Last Year", last_year),
        table_data,
        fig,
    )


if __name__ == "__main__":
    app.run(debug=True)