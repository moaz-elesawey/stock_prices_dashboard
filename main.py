from datetime import datetime
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf


external_styles = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css"
]
external_scripts = [
    "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"
]

app = Dash(
    __name__,
    external_stylesheets=external_styles,
    external_scripts=external_scripts,
    meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=2.0, maximum-scale=1.2, minimum-scale=0.5,",
        }
    ],
    title="Stock Prices",
)


tickers = ["GOOG", "AAPL", "AMZN", "BTC-USD", "FB", "TSLA", "NVDA"]

tickers_select = dcc.Dropdown(
    id="ticker-select",
    options=[{"label": ticker, "value": ticker} for ticker in tickers],
    style={"min-width": "13rem"},
    value="AMZN",
)


nav = html.Nav(
    className="navbar navbar-expand-lg navbar-light bg-light shadow-sm fixed-top",
    children=[
        html.Div(
            className="container d-flex flex-row flex-lg-row justify-content-lg-between justify-content-md-between align-items-sm-center flex-sm-column  justify-content-sm-center ",
            children=[
                html.A(
                    className="navbar-brand mb-0",
                    children="AMZN Prices Trends",
                    id="ticker-title",
                ),
                tickers_select,
            ],
        )
    ],
)


recommendation = html.Div(
    className="card card-body shadow-sm p-3",
    children=[
        html.Div(
            className="d-flex justify-content-between align-items-center",
            children=[
                html.H3(id="recommendation"),
                html.H5(id="current-time", children="text"),
            ],
        ),
    ],
)

adj_close_element = html.Div(
    className="row mt-4",
    children=[
        html.Div(
            className="col mb-4",
            children=[
                html.Div(
                    className="card card-body p-0 shadow-sm",
                    children=[dcc.Graph(id="ticker-finance")],
                ),
            ],
        ),
    ],
)

data_table = html.Div(
    id="data-table",
    className="table-responsive",
)


interval_updater = dcc.Interval(id="interval-updater", interval=1 * 1000*60, n_intervals=0)

body = html.Div(
    className="container mt-4",
    style={"padding-top": "3.5rem", "margin-bottom": "2rem"},
    children=[
        recommendation,
        adj_close_element,
        interval_updater,
        html.Div(
            className="row",
            children=[
                html.Div(
                    className="col-12 col-sm-12 col-md-6 col-lg-6 h-50 mb-sm-4",
                    children=[
                        html.Div(
                            className="card card-body p-0 shadow-sm",
                            children=[dcc.Graph(id="ticker-extra")],
                        ),
                    ],
                ),
                html.Div(
                    className="col-12 col-sm-12 col-md-6 col-lg-6 h-50",
                    style={"max-height": "22rem"},
                    children=[
                        html.Div(
                            className="card card-body p-0 shadow-sm",
                            children=[dcc.Graph(id="ticker-volume")],
                        ),
                    ],
                ),
            ],
        ),
        html.Div(className="card card-body shadow-sm mt-4 p-0", children=[data_table]),
    ],
)


@app.callback(
    Output("current-time", "children"), Input("interval-updater", "n_intervals")
)
def update_live(n):

    return datetime.utcnow().strftime("%d %b %Y at %H:%M:%S")


@app.callback(
    [
        Output("ticker-title", "children"),
        Output("ticker-finance", "figure"),
        Output("ticker-extra", "figure"),
        Output("ticker-volume", "figure"),
        Output("recommendation", "children"),
        Output("data-table", "children"),
    ],
    [Input("ticker-select", "value")],
)
def update_select_ticker(ticker):
    if not ticker:
        return
    try:
        data = yf.download(tickers=ticker, period="3mo", interval="1d")
    except Exception as e:
        data = pd.read_csv("data/{}.csv".format(ticker))
        print("error")

    title = ticker + " Stock Prices"

    df = data.copy().reset_index()
    df.columns = ['Date','Open','High','Low','Close','Adj Close','Volume']

    df["Date"] = pd.to_datetime(df["Date"])
    df.sort_values("Date", inplace=True)

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="Close"))
    fig1.add_trace(go.Scatter(x=df["Date"], y=df["Open"], mode="lines", name="Open"))
    fig1.update_layout(
        title=f"{ticker} Prices, Currancy in USD",
    )

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df["Date"], y=df["High"], mode="lines", name="High"))
    fig2.add_trace(
        go.Scatter(x=df["Date"], y=df["Close"], mode="lines", name="Close", fill="tonexty")
    )
    fig2.update_layout(title="High vs. Low Prices")

    fig3 = px.box(
        df,
        x="Volume",
        title=f"{ticker} Volume Distribution",
    )

    recommend_text, color = (
        ("BUY", "blue")
        if df["Close"].values[-1] > df["Open"].values[-1]
        else ("SELL", "red")
    )
    recommendation_text = [
        "Recommendation: ",
        html.Span(children=recommend_text, style={"color": color}),
    ]

    table_header = html.Thead(
        className="bg-dark text-white",
        children=html.Tr(
            children=[html.Th(children=col, scope="row") for col in df.columns]
        ),
    )

    def format_datatime(x):
        if isinstance(x, pd.Timestamp):
            return x.strftime("%d %b %Y")
        elif isinstance(x, float):
            return int(x)
        return x

    table_body = html.Tbody(
        children=[
            html.Tr(
                children=[
                    html.Td(
                        children=format_datatime(col), style={"white-space": "nowrap"}
                    )
                    for col in row
                ]
            )
            for row in df.head(10).values
        ]
    )

    table = html.Div(
        className="table-responsive",
        children=[
            html.Table(className="table table-sm", children=[table_header, table_body])
        ],
    )

    return title, fig1, fig2, fig3, recommendation_text, table


layout = html.Div(children=[nav, body])

app.layout = layout

if __name__ == "__main__":
    app.run_server(debug=False)
