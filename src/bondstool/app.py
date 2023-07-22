import numpy as np
from bondstool.analysis.plot import (
    make_base_monthly_payments_fig,
    plot_potential_payments,
)
from bondstool.analysis.utils import (
    calc_potential_payments,
    fill_missing_months,
    payments_by_month,
)
from bondstool.data.auction import (
    filter_trading_bonds,
    get_auction_xml,
    parse_xml_isins,
)
from bondstool.data.bag import merge_bonds_info, read_bag_info
from bondstool.data.bonds import get_bonds_info, normalize_payments
from dash import Dash, Input, Output, callback, dcc, html

bonds = get_bonds_info()
bonds = normalize_payments(bonds)

bag = read_bag_info()
bag = merge_bonds_info(bag, bonds)

isin_df = parse_xml_isins(get_auction_xml())

trading_bonds = filter_trading_bonds(isin_df, bonds)

monthly_bag = payments_by_month(bag)
monthly_bag = fill_missing_months(monthly_bag)

base_fig = make_base_monthly_payments_fig(monthly_bag)


app = Dash(__name__)

SLIDER_STEPS = np.arange(0, 5000, 200)

app.layout = html.Div(
    [
        dcc.Graph(id="graph-with-slider"),
        dcc.Slider(
            SLIDER_STEPS.min(),
            SLIDER_STEPS.max(),
            step=None,
            value=SLIDER_STEPS.min(),
            marks={str(val): str(val) for val in SLIDER_STEPS},
            id="bond-quant-slider",
        ),
    ]
)


@callback(Output("graph-with-slider", "figure"), Input("bond-quant-slider", "value"))
def update_figure(amount):

    potential_payments = calc_potential_payments(
        trading_bonds.loc[trading_bonds.ISIN == "UA4000227656"], amount, monthly_bag
    )

    fig = plot_potential_payments(base_fig, potential_payments)

    fig.update_layout(transition_duration=500)

    return fig


if __name__ == "__main__":
    app.run(debug=True)
