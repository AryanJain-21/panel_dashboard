import panel as pn
from netflixapi import NetflixAPI  # Assuming you renamed the API for Netflix

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
min_rating = pn.widgets.IntSlider(name="Min Rating", start=1, end=10, step=1, value=5)

# Checkboxes for filtering by type
only_movies = pn.widgets.Checkbox(name='Only Movies', value=False)
only_tv = pn.widgets.Checkbox(name='Only TV Shows', value=False)

# Fixed dimensions for the table
table_width = 1500
table_height = 800

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
            f"**Description:** {movie_info['description']}"
        )
        return details
    else:
        return pn.pane.Markdown("Movie not found.")

# Function to get the movie catalog based on year, minimum rating, and type
def get_catalog(release_year, min_rating, only_movies, only_tv):
    local = api.extract_local_network(release_year, min_rating)
    
    # Filter by type
    if only_movies and not only_tv:
        local = local[local['type'] == 'MOVIE']
    elif only_tv and not only_movies:
        local = local[local['type'] == 'SHOW']
    
    table = pn.widgets.Tabulator(local, selectable=False, width=table_width, height=table_height)
    return table

# Callback Bindings
movie_details_output = pn.bind(show_movie_details, autocomplete)
movie_catalog = pn.bind(get_catalog, years, min_rating, only_movies, only_tv)

# Dashboard Widget Containers ("Cards")
card_width = 320

search_card = pn.Card(
    pn.Column(
        autocomplete,
        years,
        min_rating,
        only_movies,
        only_tv
    ),
    title="Search", width=card_width, collapsed=False
)

# Adding the catalog display to the layout
catalog_card = pn.Card(
    movie_catalog,
    title="Movie Catalog", width=card_width, collapsed=False
)

# Layout
layout = pn.template.FastListTemplate(
    title="Netflix Movie Explorer",
    sidebar=[search_card],
    main=[
        movie_details_output,
        catalog_card
    ],
    header_background='#a93226'
).servable()

layout.show()
