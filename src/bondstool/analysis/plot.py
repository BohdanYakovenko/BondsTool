import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def make_base_monthly_payments_fig(monthly_bag: pd.DataFrame):

    fig = px.line(monthly_bag["total_pay_val"])

    fig.data[0]["name"] = "Виплати за портфелем"

    return fig


def plot_potential_payments(
    base_fig: go.Figure, potential_payments: pd.DataFrame, monthly_bag: pd.DataFrame
):
    fig = go.Figure()

    trace = px.line(potential_payments).data[0]
    trace["line"]["color"] = "rgb(34, 130, 47)"
    trace["name"] = "Спрогнозовані виплати"

    fig.add_trace(trace)

    for tr in base_fig.data:
        fig.add_trace(tr)

    area_trace = go.Scatter(
        x=trace["x"],
        y=trace["y"],
        mode="lines",
        fill="tonexty",
        fillcolor="rgba(11, 156, 49, 0.4)",
        line=dict(color="rgba(255, 0, 0, 0.0)"),
        name="Area Shading",
        showlegend=False,
    )
    fig.add_trace(area_trace)

    avg_bag = monthly_bag.mean().values[0]
    avg_bag_trace = go.Scatter(
        x=trace["x"],
        y=[avg_bag] * len(trace["x"]),
        mode="lines",
        line=dict(color="gray", dash="dash"),
        name="Середня щомісячна виплата",
    )
    fig.add_trace(avg_bag_trace)

    fig.update_layout(legend_title_text="Облігації", title_font=dict(size=25))
    fig.update_xaxes(title_text="Дата", title_font=dict(size=25))
    fig.update_yaxes(title_text="Сума", title_font=dict(size=25))

    return fig
