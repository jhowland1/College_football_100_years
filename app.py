import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, Input, Output, dcc, html, dash_table


DATA_PATH = "data/cfb_games.pkl"
BACKGROUND_COLOR = "#0f172a"
PANEL_COLOR = "#111827"
BORDER_COLOR = "#334155"
TEXT_COLOR = "#e5e7eb"
MUTED_TEXT_COLOR = "#94a3b8"
ACCENT_COLOR = "#38bdf8"


def card_style():
    return {
        "backgroundColor": PANEL_COLOR,
        "padding": "18px",
        "borderRadius": "14px",
        "border": f"1px solid {BORDER_COLOR}",
        "boxShadow": "0 10px 30px rgba(0, 0, 0, 0.18)",
    }


def panel_style():
    return {
        "backgroundColor": PANEL_COLOR,
        "padding": "20px",
        "borderRadius": "16px",
        "border": f"1px solid {BORDER_COLOR}",
        "boxShadow": "0 10px 30px rgba(0, 0, 0, 0.18)",
    }


def make_card(title, value, subtitle=None):
    children = [
        html.Div(
            title,
            style={
                "color": MUTED_TEXT_COLOR,
                "fontSize": "13px",
                "textTransform": "uppercase",
                "letterSpacing": "0.08em",
                "marginBottom": "10px",
                "fontWeight": "600",
            },
        ),
        html.Div(
            str(value),
            style={
                "fontSize": "30px",
                "fontWeight": "700",
                "color": "white",
                "lineHeight": "1.1",
            },
        ),
    ]

    if subtitle:
        children.append(
            html.Div(
                subtitle,
                style={
                    "marginTop": "8px",
                    "fontSize": "13px",
                    "color": MUTED_TEXT_COLOR,
                },
            )
        )

    return children


def clean_series(series):
    cleaned = series.astype(str).str.strip()
    return cleaned.replace({"nan": np.nan, "None": np.nan, "": np.nan})


def apply_figure_theme(fig):
    fig.update_layout(
        paper_bgcolor=PANEL_COLOR,
        plot_bgcolor=PANEL_COLOR,
        font_color=TEXT_COLOR,
        title_font_size=18,
        margin=dict(l=40, r=20, t=60, b=40),
        legend_title_text="",
    )
    fig.update_xaxes(
        gridcolor="rgba(148, 163, 184, 0.15)",
        zerolinecolor="rgba(148, 163, 184, 0.15)",
    )
    fig.update_yaxes(
        gridcolor="rgba(148, 163, 184, 0.15)",
        zerolinecolor="rgba(148, 163, 184, 0.15)",
    )
    return fig


def load_data():
    df = pd.read_pickle(DATA_PATH).copy()

    df["date"] = pd.to_datetime(df["timestamp"], unit="s", errors="coerce")
    df["year"] = df["date"].dt.year
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df["decade"] = (df["year"] // 10) * 10

    team1_df = df[["date", "year", "decade", "Team1", "Conf1"]].copy()
    team1_df.columns = ["date", "year", "decade", "team", "conference"]

    team2_df = df[["date", "year", "decade", "Team2", "Conf2"]].copy()
    team2_df.columns = ["date", "year", "decade", "team", "conference"]

    appearances_df = pd.concat([team1_df, team2_df], ignore_index=True)
    appearances_df["team"] = clean_series(appearances_df["team"])
    appearances_df["conference"] = clean_series(appearances_df["conference"]).fillna("Unknown")
    appearances_df = appearances_df.dropna(subset=["team", "year", "decade"])
    appearances_df["year"] = appearances_df["year"].astype(int)
    appearances_df["decade"] = appearances_df["decade"].astype(int)

    games_df = df[["date", "year", "decade", "Conf1", "Conf2"]].copy()
    games_df.columns = ["date", "year", "decade", "conference_1", "conference_2"]
    games_df["conference_1"] = clean_series(games_df["conference_1"]).fillna("Unknown")
    games_df["conference_2"] = clean_series(games_df["conference_2"]).fillna("Unknown")
    games_df["year"] = games_df["year"].astype(int)
    games_df["decade"] = games_df["decade"].astype(int)

    return appearances_df, games_df


def filter_appearances(df, selected_conferences, decade_range):
    start_decade, end_decade = decade_range

    filtered = df[(df["decade"] >= start_decade) & (df["decade"] <= end_decade)].copy()

    if selected_conferences:
        filtered = filtered[filtered["conference"].isin(selected_conferences)]

    return filtered


def filter_games(df, selected_conferences, decade_range):
    start_decade, end_decade = decade_range

    filtered = df[(df["decade"] >= start_decade) & (df["decade"] <= end_decade)].copy()

    if selected_conferences:
        filtered = filtered[
            filtered["conference_1"].isin(selected_conferences)
            | filtered["conference_2"].isin(selected_conferences)
        ]

    return filtered


appearances_df, games_df = load_data()

all_conferences = sorted(appearances_df["conference"].unique())
min_decade = int(appearances_df["decade"].min())
max_decade = int(appearances_df["decade"].max())

conference_options = [{"label": conference, "value": conference} for conference in all_conferences]
decade_marks = {
    decade: {"label": f"{decade}s", "style": {"color": MUTED_TEXT_COLOR}}
    for decade in range(min_decade, max_decade + 10, 10)
}

app = Dash(__name__)
server = app.server
app.title = "College Football Conference Dashboard"

app.layout = html.Div(
    style={
        "fontFamily": "Inter, Arial, sans-serif",
        "backgroundColor": BACKGROUND_COLOR,
        "minHeight": "100vh",
        "padding": "24px",
        "color": TEXT_COLOR,
    },
    children=[
        html.Div(
            style={"maxWidth": "1440px", "margin": "0 auto"},
            children=[
                html.Div(
                    style={"marginBottom": "24px"},
                    children=[
                        html.H1(
                            "College Football Conference Dashboard",
                            style={
                                "margin": "0 0 8px 0",
                                "fontSize": "34px",
                                "fontWeight": "800",
                                "color": "white",
                            },
                        ),
                        html.P(
                            "Explore conference activity over time with multi-select filters, decade range controls, trend analysis, and a decade heatmap.",
                            style={
                                "margin": "0",
                                "fontSize": "15px",
                                "color": MUTED_TEXT_COLOR,
                                "maxWidth": "900px",
                            },
                        ),
                    ],
                ),
                html.Div(
                    style={
                        **panel_style(),
                        "marginBottom": "24px",
                    },
                    children=[
                        html.Div(
                            style={
                                "display": "grid",
                                "gridTemplateColumns": "1.5fr 1fr",
                                "gap": "24px",
                                "alignItems": "start",
                            },
                            children=[
                                html.Div(
                                    children=[
                                        html.Label(
                                            "Conferences",
                                            style={
                                                "display": "block",
                                                "marginBottom": "10px",
                                                "fontWeight": "600",
                                                "color": "white",
                                            },
                                        ),
                                        dcc.Dropdown(
                                            id="conference-filter",
                                            options=conference_options,
                                            value=all_conferences,
                                            multi=True,
                                            placeholder="Select one or more conferences",
                                            style={"color": "#111827"},
                                        ),
                                        html.Div(
                                            "Tip: clear the selection to compare all conferences.",
                                            style={
                                                "marginTop": "10px",
                                                "fontSize": "13px",
                                                "color": MUTED_TEXT_COLOR,
                                            },
                                        ),
                                    ]
                                ),
                                html.Div(
                                    children=[
                                        html.Label(
                                            "Decade Range",
                                            style={
                                                "display": "block",
                                                "marginBottom": "14px",
                                                "fontWeight": "600",
                                                "color": "white",
                                            },
                                        ),
                                        dcc.RangeSlider(
                                            id="decade-range",
                                            min=min_decade,
                                            max=max_decade,
                                            step=10,
                                            value=[min_decade, max_decade],
                                            marks=decade_marks,
                                            allowCross=False,
                                            tooltip={"placement": "bottom", "always_visible": False},
                                        ),
                                    ]
                                ),
                            ],
                        )
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
                        html.Div(id="card-total-appearances", style=card_style()),
                        html.Div(id="card-total-games", style=card_style()),
                        html.Div(id="card-unique-teams", style=card_style()),
                        html.Div(id="card-year-span", style=card_style()),
                    ],
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1.3fr 1fr",
                        "gap": "24px",
                        "marginBottom": "24px",
                    },
                    children=[
                        html.Div(
                            style=panel_style(),
                            children=[
                                html.H3(
                                    "Conference Trend by Year",
                                    style={"marginTop": "0", "marginBottom": "14px", "color": "white"},
                                ),
                                dcc.Graph(id="conference-trend-chart", config={"displayModeBar": False}),
                            ],
                        ),
                        html.Div(
                            style=panel_style(),
                            children=[
                                html.H3(
                                    "Heatmap by Conference and Decade",
                                    style={"marginTop": "0", "marginBottom": "14px", "color": "white"},
                                ),
                                dcc.Graph(id="conference-decade-heatmap", config={"displayModeBar": False}),
                            ],
                        ),
                    ],
                ),
                html.Div(
                    style={
                        "display": "grid",
                        "gridTemplateColumns": "1.15fr 1fr",
                        "gap": "24px",
                    },
                    children=[
                        html.Div(
                            style=panel_style(),
                            children=[
                                html.H3(
                                    "Top Teams",
                                    style={"marginTop": "0", "marginBottom": "14px", "color": "white"},
                                ),
                                dash_table.DataTable(
                                    id="teams-table",
                                    columns=[
                                        {"name": "Team", "id": "team"},
                                        {"name": "Conference", "id": "conference"},
                                        {"name": "Appearances", "id": "appearances"},
                                        {"name": "First Year", "id": "first_year"},
                                        {"name": "Last Year", "id": "last_year"},
                                    ],
                                    page_size=12,
                                    sort_action="native",
                                    style_table={"overflowX": "auto"},
                                    style_header={
                                        "backgroundColor": "#1e293b",
                                        "color": "white",
                                        "fontWeight": "700",
                                        "border": f"1px solid {BORDER_COLOR}",
                                    },
                                    style_cell={
                                        "backgroundColor": PANEL_COLOR,
                                        "color": TEXT_COLOR,
                                        "padding": "10px",
                                        "textAlign": "left",
                                        "border": f"1px solid {BORDER_COLOR}",
                                        "fontSize": "13px",
                                    },
                                    style_data_conditional=[
                                        {
                                            "if": {"row_index": "odd"},
                                            "backgroundColor": "#0b1220",
                                        }
                                    ],
                                ),
                            ],
                        ),
                        html.Div(
                            style=panel_style(),
                            children=[
                                html.H3(
                                    "Top Teams by Appearances",
                                    style={"marginTop": "0", "marginBottom": "14px", "color": "white"},
                                ),
                                dcc.Graph(id="teams-bar-chart", config={"displayModeBar": False}),
                            ],
                        ),
                    ],
                ),
            ],
        )
    ],
)


@app.callback(
    Output("card-total-appearances", "children"),
    Output("card-total-games", "children"),
    Output("card-unique-teams", "children"),
    Output("card-year-span", "children"),
    Output("conference-trend-chart", "figure"),
    Output("conference-decade-heatmap", "figure"),
    Output("teams-table", "data"),
    Output("teams-bar-chart", "figure"),
    Input("conference-filter", "value"),
    Input("decade-range", "value"),
)
def update_dashboard(selected_conferences, decade_range):
    selected_conferences = selected_conferences or []

    filtered_appearances = filter_appearances(appearances_df, selected_conferences, decade_range)
    filtered_games = filter_games(games_df, selected_conferences, decade_range)

    if filtered_appearances.empty:
        empty_line = apply_figure_theme(px.line(title="No data available"))
        empty_heatmap = apply_figure_theme(px.imshow([[0]], text_auto=True, title="No data available"))
        empty_bar = apply_figure_theme(px.bar(title="No data available"))

        return (
            make_card("Total Appearances", 0),
            make_card("Total Games", 0),
            make_card("Unique Teams", 0),
            make_card("Year Span", "—"),
            empty_line,
            empty_heatmap,
            [],
            empty_bar,
        )

    total_appearances = len(filtered_appearances)
    total_games = len(filtered_games)
    unique_teams = filtered_appearances["team"].nunique()
    first_year = int(filtered_appearances["year"].min())
    last_year = int(filtered_appearances["year"].max())

    trend_df = (
        filtered_appearances.groupby(["year", "conference"])
        .size()
        .reset_index(name="appearances")
        .sort_values(["year", "conference"])
    )

    trend_fig = px.line(
        trend_df,
        x="year",
        y="appearances",
        color="conference",
        markers=True,
        title="Conference appearances by year",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    trend_fig.update_traces(line={"width": 3})
    trend_fig.update_layout(
        hovermode="x unified",
        xaxis_title="Year",
        yaxis_title="Appearances",
    )
    trend_fig = apply_figure_theme(trend_fig)

    heatmap_df = (
        filtered_appearances.groupby(["conference", "decade"])
        .size()
        .reset_index(name="appearances")
        .pivot(index="conference", columns="decade", values="appearances")
        .fillna(0)
        .astype(int)
    )

    heatmap_fig = px.imshow(
        heatmap_df,
        text_auto=True,
        aspect="auto",
        color_continuous_scale="Blues",
        labels={"x": "Decade", "y": "Conference", "color": "Appearances"},
        title="Conference activity by decade",
    )
    heatmap_fig.update_layout(
        xaxis_title="Decade",
        yaxis_title="Conference",
        coloraxis_colorbar=dict(title="Appearances"),
    )
    heatmap_fig = apply_figure_theme(heatmap_fig)

    teams_summary = (
        filtered_appearances.groupby(["team", "conference"])
        .agg(
            appearances=("team", "size"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
        .sort_values(["appearances", "team"], ascending=[False, True])
    )

    table_data = teams_summary.head(12).to_dict("records")
    bar_df = teams_summary.head(10).sort_values("appearances", ascending=True)

    teams_bar_fig = px.bar(
        bar_df,
        x="appearances",
        y="team",
        color="conference",
        orientation="h",
        title="Most frequent teams in the current view",
        color_discrete_sequence=px.colors.qualitative.Bold,
    )
    teams_bar_fig.update_layout(
        xaxis_title="Appearances",
        yaxis_title="Team",
        showlegend=True,
    )
    teams_bar_fig = apply_figure_theme(teams_bar_fig)

    selected_label = "All conferences" if not selected_conferences else f"{len(selected_conferences)} selected"

    return (
        make_card("Total Appearances", f"{total_appearances:,}", selected_label),
        make_card("Total Games", f"{total_games:,}", f"Decades {decade_range[0]}s–{decade_range[1]}s"),
        make_card("Unique Teams", f"{unique_teams:,}", "Teams in filtered view"),
        make_card("Year Span", f"{first_year}–{last_year}", "Observed seasons"),
        trend_fig,
        heatmap_fig,
        table_data,
        teams_bar_fig,
    )


if __name__ == "__main__":
    app.run(debug=True)