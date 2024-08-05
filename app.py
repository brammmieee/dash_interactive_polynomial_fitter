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
    xaxis=dict(range=[-0.1, 1.1]),
    yaxis=dict(range=[-110, 110])
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
        dbc.Col([
            html.Label("Down-Scaling Factor:", className="form-label"),
            dcc.Input(id="scaling-input", type="number", value=1, step=0.1, min=0, debounce=True)
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

def polynomial_to_string(poly, scale_factor):
    """
    Create a string representation of the polynomial with scaling factor applied to coefficients.
    """
    # Scale the coefficients vertically
    poly = (1/scale_factor) * poly
    
    # Build polynomial string
    terms = []
    degree = len(poly.coefficients) - 1
    for i, coeff in enumerate(poly.coefficients):
        if coeff == 0:
            continue
        coeff = coeff*(scale_factor**(degree - i))
        term = f"{coeff:.6f}"
        if degree - i > 0:
            term += f"*x**{degree - i}"
        terms.append(term)
    
    # Join terms with + or - signs
    poly_str = " + ".join(terms).replace("+ -", "- ")
    if poly_str.startswith("- "):
        poly_str = poly_str[2:]  # Remove leading "- " if present
    
    return f"{poly_str}"

@app.callback(
    Output("graph", "figure"),
    Output("polynomial-equation", "children"),
    Input("graph", "relayoutData"),
    Input("degree-slider", "value"),
    Input("scaling-input", "value"),
    prevent_initial_call=True
)
def on_new_annotation(relayout_data, degree, scaling_factor):
    if not relayout_data or "shapes" not in relayout_data:
        return no_update, no_update
    
    shapes = relayout_data["shapes"]
    if not shapes:
        return no_update, no_update
    
    # Handle scaling factor default
    if scaling_factor is None:
        scaling_factor = 1
    else:
        try:
            scaling_factor = float(scaling_factor)
        except ValueError:
            scaling_factor = 1

    # Extract path points
    path = shapes[-1]['path']
    coords = [tuple(map(float, p.split(','))) for p in path[1:].split('L')]
    x_points = [x for x, y in coords]
    y_points = [y for x, y in coords]
    
    # Fit polynomial
    poly = fit_polynomial(x_points, y_points, degree)
    x_fit = np.linspace(min(x_points), max(x_points), 500)
    y_fit = poly(x_fit)
    
    # Apply scaling
    if scaling_factor > 0:
        x_fit_scaled = x_fit / scaling_factor
        y_fit_scaled = y_fit / scaling_factor
    else:
        x_fit_scaled = x_fit
        y_fit_scaled = y_fit

    # Convert polynomial to string with scaling factor
    poly_str = polynomial_to_string(poly, scaling_factor)
    
    # Update figure
    fig = go.Figure()
    fig.add_scatter(x=x_points, y=y_points, mode='markers', name='Drawn Points')
    fig.add_scatter(x=x_fit_scaled, y=y_fit_scaled, mode='lines', name=f'Polynomial Fit (degree {degree})')
    
    return fig, poly_str

if __name__ == "__main__":
    app.run(debug=True)
