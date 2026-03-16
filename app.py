from dash import Dash, html

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("College Football Dashboard")
])

app_df = appearances.copy()

app_df = app_df.dropna(subset=["team", "year", "decade"])
app_df["team"] = app_df["team"].astype(str).str.strip()
app_df["conference"] = app_df["conference"].fillna("Unknown").astype(str).str.strip()
app_df["year"] = app_df["year"].astype(int)
app_df["decade"] = app_df["decade"].astype(int)

conference_options = [{"label": "All Conferences", "value": "All"}] + [
    {"label": conf, "value": conf}
    for conf in sorted(app_df["conference"].dropna().unique())
]

decade_options = [{"label": "All Decades", "value": "All"}] + [
    {"label": f"{decade}s", "value": decade}
    for decade in sorted(app_df["decade"].dropna().unique())
]

app = Dash(__name__)
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
                    children=[
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
                    children=[
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
                                "border": "1px solid #334155",
                            },
                            style_cell={
                                "backgroundColor": "#111827",
                                "color": "white",
                                "border": "1px solid #334155",
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
        empty_fig = px.bar(title="No data available")
        empty_fig.update_layout(
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
            empty_fig,
        )

    total_appearances = len(filtered)
    unique_teams = filtered["team"].nunique()
    first_year = filtered["year"].min()
    last_year = filtered["year"].max()

    team_summary_filtered = (
        filtered.groupby(["team", "conference"])
        .agg(
            appearances=("team", "size"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
        .sort_values(["appearances", "team"], ascending=[False, True])
    )

    table_data = team_summary_filtered.head(15).to_dict("records")

    chart_df = team_summary_filtered.head(10).sort_values("appearances", ascending=True)

    fig = px.bar(
        chart_df,
        x="appearances",
        y="team",
        orientation="h",
        color="conference",
        title="Top 10 Teams",
    )
    fig.update_layout(
        paper_bgcolor="#111827",
        plot_bgcolor="#111827",
        font_color="white",
        yaxis_title="Team",
        xaxis_title="Appearances",
        legend_title="Conference",
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