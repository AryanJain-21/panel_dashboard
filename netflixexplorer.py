import panel as pn
from netflixapi import NetflixAPI  # Assuming you renamed the API for Netflix
import holoviews as hv  # For plotting

# Loads javascript dependencies and configures Panel (required)
pn.extension()

# INITIALIZE API
api = NetflixAPI()
api.load_net('titles.csv')

# WIDGET DECLARATIONS

# Search Widgets

# Dropdown for selecting release year (assuming your MongoDB has a field 'release_year')
years = pn.widgets.Select(name="Year", options=api.get_years(), value=2000)

# Slider for controlling the minimum rating or other numeric filters
min_rating = pn.widgets.IntSlider(name="Min Rating", start=1, end=10, step=1, value=5)

# Plotting widgets
width = pn.widgets.IntSlider(name="Width", start=250, end=2000, step=250, value=1500)
height = pn.widgets.IntSlider(name="Height", start=200, end=2500, step=100, value=800)

# CALLBACK FUNCTIONS

def get_catalog(release_year, min_rating):
    global local
    local = api.extract_local_network(release_year, min_rating)
    table = pn.widgets.Tabulator(local, selectable=False)
    return table


"""def plot_ratings_by_year(release_year, min_rating, width, height):
    df = api.fetch_data(filter_field='release_year', filter_value=release_year)
    df = df[df['rating'] >= min_rating]  # Assuming there is a 'rating' column
    bars = hv.Bars(df, kdims='title', vdims='rating').opts(width=width, height=height)
    return pn.pane.HoloViews(bars)"""

# CALLBACK BINDINGS
movie_catalog = pn.bind(get_catalog, years, min_rating)
#rating_plot = pn.bind(plot_ratings_by_year, release_year, min_rating, width, height)

# DASHBOARD WIDGET CONTAINERS ("CARDS")

card_width = 320

search_card = pn.Card(
    pn.Column(
        years,
        min_rating
    ),
    title="Search", width=card_width, collapsed=False
)

plot_card = pn.Card(
    pn.Column(
        width,
        height
    ),
    title="Plot", width=card_width, collapsed=True
)

# LAYOUT

layout = pn.template.FastListTemplate(
    title="Netflix Movie Explorer",
    sidebar=[
        search_card,
        plot_card,
    ],
    theme_toggle=False,
    main=[
        pn.Tabs(
            ("Movies", movie_catalog),
            #("Rating Distribution", rating_plot),
            active=0
        )
    ],
    header_background='#a93226'
).servable()

layout.show()
