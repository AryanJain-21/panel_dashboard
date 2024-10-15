import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
import sankey as sk

class db_NetflixAPI:
    
    def __init__(self, db_name='netflix_movies', collection_name='movies', connection_string=None):
        """Initialize the MongoDB connection and set the database and collection."""
        if connection_string is None:
            connection_string = 'mongodb://mongoadmin:password@localhost:27017/'  # Use environment variables in production
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.netflix = self.fetch_data()

        # Fetch initial data and convert ObjectId to string
        self.data = self.fetch_data()  # Fetch all data on initialization
        self.data = self.convert_objectid_to_string(self.data)

    def fetch_data(self, filter_field=None, filter_value=None):
        """Fetch data from the MongoDB collection, optionally filtered by a field and value."""
        query = {filter_field: filter_value} if filter_field and filter_value else {}
        data = list(self.collection.find(query))
        df = pd.DataFrame(data)
        if '_id' in df.columns:
            df['_id'] = df['_id'].astype(str)
        return df

    def convert_objectid_to_string(self, df):
        """Convert ObjectId fields in a DataFrame to strings."""
        for column in df.select_dtypes(include=[object]):
            if df[column].apply(lambda x: isinstance(x, ObjectId)).any():
                df[column] = df[column].astype(str)
        return df

    def get_years(self):
        """Fetches unique release years from the dataset."""
        return sorted(self.data['release_year'].unique())

    def get_unique_genres(self):
        """Returns a sorted list of unique genres in the dataset."""
        unique_genres = set()
        for genres in self.data['genres'].dropna():
            genre_list = [genre.strip().replace('[', '').replace(']', '').replace("'", "") for genre in genres.split(',')]
            unique_genres.update(genre_list)
        return sorted(unique_genres)

    def extract_local_network(self, release_year, min_rating, only_movies, only_tv, selected_genres=None):
        """Extracts a local network of movies/shows based on filters."""
        if selected_genres is None:
            selected_genres = [] 

        local_network = self.data.copy()

        # Filtering based on release year
        local_network = local_network[local_network['release_year'] == release_year]

        # Filtering based on minimum rating
        local_network = local_network[local_network['imdb_score'] >= min_rating]

        # Applying movie and TV show filters
        if only_movies:
            local_network = local_network[local_network['type'] == 'MOVIE']
        if only_tv:
            local_network = local_network[local_network['type'] == 'SHOW']

        # Filtering by selected genres
        if selected_genres:
            local_network = local_network[local_network['genres'].apply(lambda x: any(genre in x for genre in selected_genres))]

        columns_to_display = ['title', 'type', 'imdb_score', 'release_year', 'genres', 'age_certification', 'runtime', 'seasons']
        existing_columns = [col for col in columns_to_display if col in local_network.columns]
        local_network = local_network.reset_index(drop=True)[existing_columns]

        return local_network

    def get_movie_details(self, title):
        """Fetches details of a specific movie based on its title."""
        movie_details = self.data[self.data['title'] == title]
        return movie_details.squeeze() if not movie_details.empty else None

    def create_sankey_plot(self, data, sankey_width=1500, sankey_height=800):
        """Creates a Sankey diagram based on the provided data."""
        def clean_genre(genre):
            if isinstance(genre, str):
                return genre.replace('[', '').replace(']', '').replace("'", "").strip()
            return genre 

        data['genres'] = data['genres'].apply(lambda x: [clean_genre(genre) for genre in x.split(',')] if isinstance(x, str) else [])
        genre_expanded = data.explode('genres').dropna(subset=['genres'])
        sankey_data = genre_expanded[['title', 'genres']].rename(columns={'title': 'src', 'genres': 'targ'})

        fig = sk.make_sankey(
            df=sankey_data,
            src='src',
            targ='targ',
            width=sankey_width,
            height=sankey_height
        )
        return fig

def main():
    # Create an instance of db_NetflixAPI
    netflix_api = db_NetflixAPI()
    
    # Example: Print all unique release years
    print(sorted(netflix_api.get_years()))
    
    # Example: Fetch movies from the year 2001
    df = netflix_api.fetch_data(filter_field='release_year', filter_value=2001)
    print(df.head())

if __name__ == '__main__':
    main()
