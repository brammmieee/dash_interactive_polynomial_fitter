import json
import numpy as np
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, no_update, callback

# Initialize the Dash app with a Bootstrap theme
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Initial empty figure
fig = go.Figure()
fig.update_layout(
    dragmode="drawopenpath",
    xaxis=dict(range=[0, 100]),
    yaxis=dict(range=[0, 100])
)
config = {
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "drawclosedpath",
        "drawcircle",
        "drawrect",
        "eraseshape",
    ]
}

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H3("Draw a path and fit a polynomial", className="text-center mb-4"), width={"size": 8, "offset": 2})
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id="graph", figure=fig, config=config), width=12)
    ]),
    dbc.Row([
        dbc.Col([
            html.Label("Polynomial Degree:", className="form-label"),
            dcc.Slider(id="degree-slider", min=1, max=10, step=1, value=3,
                       marks={i: str(i) for i in range(1, 11)})
        ], width={"size": 6, "offset": 3})
    ]),
    dbc.Row([
        dbc.Col(html.Div(id="polynomial-equation", className="text-center mt-4"), width=12)
    ]),
], fluid=True)

def fit_polynomial(x, y, degree):
    """Fit a polynomial of the given degree to the x, y data."""
    p = np.polyfit(x, y, degree)
    return np.poly1d(p)

def polynomial_to_string(poly):
    """Convert a polynomial object to a string with high accuracy and without zero coefficients."""
    terms = []
    degree = poly.order
    for i, coeff in enumerate(poly.coefficients):
        if abs(coeff) < 1e-10:  # Filter out terms with very small coefficients
            continue
        power = degree - i
        term = f"{coeff:.5f}"
        if power > 0:
            term += f"x^{power}"
        terms.append(term)
    
    # Join terms with correct signs
    polynomial_str = ""
    for term in terms:
        if polynomial_str:
            if term.startswith("-"):
                polynomial_str += " - " + term[1:]
            else:
                polynomial_str += " + " + term
        else:
            polynomial_str = term
    
    return polynomial_str

@app.callback(
    Output("graph", "figure"),
    Output("polynomial-equation", "children"),
    Input("graph", "relayoutData"),
    Input("degree-slider", "value"),
    prevent_initial_call=True
)
def on_new_annotation(relayout_data, degree):
    if not relayout_data or "shapes" not in relayout_data:
        return no_update, no_update
    
    shapes = relayout_data["shapes"]
    if not shapes:
        return no_update, no_update
    
    # Extract path points
    path = shapes[-1]['path']
    coords = [tuple(map(float, p.split(','))) for p in path[1:].split('L')]
    x_points = [x for x, y in coords]
    y_points = [y for x, y in coords]
    
    # Fit polynomial
    poly = fit_polynomial(x_points, y_points, degree)
    x_fit = np.linspace(min(x_points), max(x_points), 500)
    y_fit = poly(x_fit)
    
    # Convert polynomial to string
    poly_str = polynomial_to_string(poly)
    
    # Update figure
    fig = go.Figure()
    fig.add_scatter(x=x_points, y=y_points, mode='markers', name='Drawn Points')
    fig.add_scatter(x=x_fit, y=y_fit, mode='lines', name=f'Polynomial Fit (degree {degree})')
    fig.update_layout(
        dragmode="drawopenpath",
        xaxis=dict(range=[0, 100]),
        yaxis=dict(range=[0, 100])
    )
    
    return fig, poly_str

if __name__ == "__main__":
    app.run(debug=True)
