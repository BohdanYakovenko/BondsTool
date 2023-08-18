import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_base_monthly_payments_fig(monthly_bag: pd.DataFrame):

    fig = px.line(monthly_bag)

    fig.data[0]["name"] = "Bag payment"

    fig.add_hline(
        y=monthly_bag.mean().values[0],
        line_width=2,
        line_dash="dot",
        annotation_text="month avg payment",
        annotation_position="bottom right",
    )

    return fig


def plot_potential_payments(base_fig: go.Figure, potential_payments: pd.DataFrame):
    fig = go.Figure()

    potential_payments_trace = px.line(potential_payments).data[0]
    potential_payments_trace["line"]["color"] = "rgb(34, 130, 47)"
    potential_payments_trace["name"] = "Forecast"

    fig.add_trace(potential_payments_trace)

    for trace in base_fig.data:
        fig.add_trace(trace)

    potential_payments_area_trace = go.Scatter(
        x=potential_payments_trace["x"],
        y=potential_payments_trace["y"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(11, 156, 49, 0.4)",
        line=dict(color="rgba(255, 0, 0, 0.0)"),
        name="Area Shading",
        showlegend=False,
    )
    fig.add_trace(potential_payments_area_trace)

    fig.update_layout(legend_title_text="Bonds", title_font=dict(size=25))
    fig.update_xaxes(title_text="Date", title_font=dict(size=25))
    fig.update_yaxes(title_text="Amount", title_font=dict(size=25))

    return fig
