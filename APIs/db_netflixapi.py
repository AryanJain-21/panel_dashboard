import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
import APIs.sankey as sk  # Ensure this is the correct import for your Sankey implementation

class db_NetflixAPI:
    
    def __init__(self, db_name='netflix_movies', collection_name='movies', connection_string=None):
        """Initialize the MongoDB connection and set the database and collection."""
        if connection_string is None:
            connection_string = 'mongodb://mongoadmin:password@localhost:27017/'  # Use environment variables in production
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.data = self.fetch_data()  # Fetch all data on initialization
        self.data = db_NetflixAPI.convert_objectid_to_string(self.data)

    def fetch_data(self, filter_field=None, filter_value=None):
        """Fetch data from the MongoDB collection, optionally filtered by a field and value."""
        query = {filter_field: filter_value} if filter_field and filter_value else {}
        data = list(self.collection.find(query, {'_id': False}))  # Exclude _id from results
        
        # Add debug output
        if not data:
            print("No data returned from MongoDB")
        else:
            print(f"Fetched {len(data)} records from MongoDB")

        return pd.DataFrame(data)

    @staticmethod
    def convert_objectid_to_string(df):
        """Convert ObjectId fields in a DataFrame to strings."""
        for column in df.select_dtypes(include=[object]):
            if df[column].apply(lambda x: isinstance(x, ObjectId)).any():
                df[column] = df[column].astype(str)
        return df

    def get_years(self):
        """Fetches unique release years from MongoDB."""
        years = self.collection.distinct('release_year')
        return sorted(years)
        
    @staticmethod
    def clean_genre(genre):
        """Cleans up the genre string."""
        if isinstance(genre, str):
            return (genre.replace('[', '').replace(']', '').replace("'", "").strip()).split(",")
        return genre 

    def get_unique_genres(self):
        """Fetch unique genres from MongoDB using aggregation."""
        pipeline = [
            {"$unwind": "$genres"},  # Break down lists of genres into individual entries
            {"$group": {"_id": "$genres"}}  # Collect unique genres
        ]
        result = self.collection.aggregate(pipeline)
        lst = []
        for dct in result:

            genre = db_NetflixAPI.clean_genre(dct['_id'])
            
            for x in genre:
                lst.append(x)

        return sorted(set(lst))

    def extract_local_network(self, release_year, min_rating, only_movies, only_tv):
        """Extracts a local network of movies/shows based on filters using MongoDB."""

        # Start building the aggregation pipeline
        pipeline = []

        # Match based on release year and IMDb score
        match_stage = {
            "$match": {
                "release_year": release_year,
                "imdb_score": {"$gte": min_rating}
            }
        }
        pipeline.append(match_stage)

        # Apply type filters
        if only_movies and not only_tv:
            pipeline[0]["$match"]["type"] = 'MOVIE'
        elif only_tv and not only_movies:
            pipeline[0]["$match"]["type"] = 'SHOW'
        elif not only_movies and not only_tv:
            # Create a match condition that cannot be satisfied
            pipeline[0]["$match"]["type"] = {'$nin': ['MOVIE', 'SHOW']}  # Example of an impossible match

        # Project only the required fields, excluding _id
        projection_stage = {
            "$project": {
                'title': 1,
                'type': 1,
                'imdb_score': 1,
                'release_year': 1,
                'genres': 1,
                'age_certification': 1,
                'runtime': 1,
                'seasons': 1,
                '_id': 0  # Exclude _id
            }
        }
        pipeline.append(projection_stage)

        # Perform the aggregation
        local_network = list(self.collection.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(local_network)
        
        # Expand genres so that each movie is linked to each of its genres

        return df  # Return original if df is empty

    def get_movie_details(self, title):
        """Fetches details of a specific movie from MongoDB based on its title."""
        movie_details = self.collection.find_one({"title": title}, {'_id': False})  # Exclude _id
        return pd.Series(movie_details) if movie_details else None

    def create_sankey_plot(self, sankey_data, sankey_width=1500, sankey_height=800, selected_genres=None):

        expanded_df = None
        if not sankey_data.empty:
            rows = []
            for _, row in sankey_data.iterrows():

                genre_lst = db_NetflixAPI.clean_genre(row['genres']) if isinstance(row['genres'], str) else []

                for genre in genre_lst:
                    rows.append({'src': str(row['title']), 'targ': genre})

            # Create a new DataFrame from the expanded rows
            expanded_df = pd.DataFrame(rows)

        if expanded_df is None or expanded_df.empty:
            return
        
        # Filter based on selected genres if provided
        if selected_genres:
            expanded_df = expanded_df[expanded_df['targ'].isin(selected_genres)]

        """Creates a Sankey diagram using provided data."""
        # Plot the Sankey diagram using your library
        fig = sk.make_sankey(
            df=expanded_df,
            src='src',
            targ='targ',
            width=sankey_width,
            height=sankey_height
        )
        return fig


