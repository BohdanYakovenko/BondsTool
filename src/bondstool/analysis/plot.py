import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_base_monthly_payments_fig(monthly_bag: pd.DataFrame):

    fig = px.line(monthly_bag)

    fig.add_hline(
        y=monthly_bag.mean().values[0],
        line_width=2,
        line_dash="dot",
        annotation_text="month avg payment",
        annotation_position="bottom right",
    )

    return fig


def plot_potential_payments(base_fig: go.Figure, potential_payments: pd.DataFrame):
    fig = go.Figure(base_fig)
    fig = fig.add_trace(px.line(potential_payments).data[0])
    fig["data"][1]["line"]["color"] = "rgb(204, 204, 204)"
    return fig
