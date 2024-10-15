import panel as pn
from netflixapi import NetflixAPI  # Assuming you renamed the API for Netflix
import sankey as sk
import pandas as pd  # Ensure pandas is imported for DataFrame manipulation

# Load JavaScript dependencies and configure Panel (required)
pn.extension()

# Initialize API
api = NetflixAPI()
api.load_net('titles.csv')

# Widget Declarations

# Autocomplete Input for movie titles
autocomplete = pn.widgets.AutocompleteInput(
    name="Media Title",
    value='',
    placeholder='Type media title...',
    options=list(api.netflix['title'].unique())  # Use unique titles for suggestions
)

# Dropdown for selecting release year
years = pn.widgets.Select(name="Year", options=api.get_years(), value=2000)

# Slider for controlling the minimum rating
min_rating = pn.widgets.FloatSlider(name="Min Rating", start=0.0, end=10.0, step=0.1, value=5.0)

# Checkboxes for filtering by type
only_movies = pn.widgets.Checkbox(name='Only Movies', value=False)
only_tv = pn.widgets.Checkbox(name='Only TV Shows', value=False)

# Plotting Widgets for Sankey Diagram
sankey_width = pn.widgets.IntSlider(name="Sankey Width", start=250, end=2000, step=250, value=1500)
sankey_height = pn.widgets.IntSlider(name="Sankey Height", start=200, end=2500, step=100, value=800)

# Callback Functions

# Function to get movie details from the autocomplete input
def show_movie_details(title):
    movie_info = api.get_movie_details(title)
    if movie_info is not None:
        details = pn.pane.Markdown(
            f"### Title: {movie_info['title']}  \n"
            f"**Release Year:** {movie_info['release_year']}  \n"
            f"**Type of Media:** {movie_info['type']}  \n"
            f"**IMDb Score:** {movie_info['imdb_score']}  \n"
            f"**Genres:** {movie_info['genres']}  \n"
            f"**Age Certification:** {movie_info['age_certification']}  \n"
            f"**Runtime:** {movie_info['runtime']} minutes  \n"
            f"**Description:** {movie_info['description']}",
            height=300,
            width=500  # Set the desired height here (in pixels)
        )
        return details
    else:
        return pn.pane.Markdown("Media not found.")

# Function to get the movie catalog based on year, minimum rating, and type
def get_catalog(release_year, min_rating, only_movies, only_tv):
    global local
    local = api.extract_local_network(release_year, min_rating)
    
    # Filter by type
    if only_movies and not only_tv:
        local = local[local['type'] == 'MOVIE']
    elif only_tv and not only_movies:
        local = local[local['type'] == 'SHOW']
    
    table = pn.widgets.Tabulator(local, selectable=False, width=1500, height=800)
    return table

# Function to create the Sankey diagram
def get_plot(years, min_rating, sankey_width, sankey_height, only_movies, only_tv):
    # Update local based on filters for the Sankey plot
    filtered_local = local.copy()
    
    # Apply filtering by type if applicable
    if only_movies and not only_tv:
        filtered_local = filtered_local[filtered_local['type'] == 'MOVIE']
    elif only_tv and not only_movies:
        filtered_local = filtered_local[filtered_local['type'] == 'SHOW']
    
    # Ensure genres are in a list format and then expand the genres
    filtered_local['genres'] = filtered_local['genres'].apply(lambda x: x.split(', ') if isinstance(x, str) else x)
    # Clean up genre names
    filtered_local['genres'] = filtered_local['genres'].apply(lambda genres: [genre.strip("[]'") for genre in genres])
    
    genre_expanded = filtered_local.explode('genres')

    # Create the Sankey plot with unique titles and genres
    fig = sk.make_sankey(genre_expanded, "title", "genres", vals="imdb_score", width=sankey_width, height=sankey_height)
    return fig

# Callback Bindings
movie_details_output = pn.bind(show_movie_details, autocomplete)
movie_catalog = pn.bind(get_catalog, years, min_rating, only_movies, only_tv)
sankey_plot = pn.bind(get_plot, years, min_rating, sankey_width, sankey_height, only_movies, only_tv)

# Dashboard Widget Containers ("Cards")
card_width = 560

search_card = pn.Card(
    pn.Column(
        autocomplete,
        years,
        min_rating,
        only_movies,
        only_tv,
    ),
    title="Search", width=card_width, collapsed=False
)

# Create a separate card for plotting dimensions
plotting_card = pn.Card(
    pn.Column(
        sankey_width,
        sankey_height
    ),
    title="Plotting", width=card_width, collapsed=False
)

# Updated catalog_card to include the new layout with added spacing
catalog_card = pn.Card(
    pn.Column(
        movie_details_output,  # Movie details output above the table
        movie_catalog           # Movie catalog table below
    ),
    title="Media Catalog", width=card_width, collapsed=False
)

# Layout
layout = pn.template.FastListTemplate(
    title="Netflix Movie Explorer",
    sidebar=[search_card, plotting_card],  # Add the plotting card to the sidebar
    main=[
        pn.Tabs(
            ("Search Movie Catalog", catalog_card),
            ("Network", sankey_plot),  # Only in the main area
            active=0  # Which tab is active by default?
        )
    ],
    header_background='#a93226'
).servable()

layout.show()
