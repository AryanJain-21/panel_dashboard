"""
File: netflixapi.py

Description: The primary API for interacting with the Netflix movies dataset in MongoDB.
"""

import pandas as pd
from pymongo import MongoClient
from bson import ObjectId

class db_NetflixAPI:
    
    def __init__(self, db_name='netflix_movies', collection_name='movies', connection_string=None):
        """
        Initialize the MongoDB connection and set the database and collection.
        """
        if connection_string is None:
            connection_string = 'mongodb://mongoadmin:password@localhost:27017/'  # Use environment variables in production
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        # Fetch initial data and convert ObjectId to string
        self.data = self.fetch_data()  # Fetch all data on initialization
        self.data = self.convert_objectid_to_string(self.data)

    def fetch_data(self, filter_field=None, filter_value=None):
        """
        Fetch data from the MongoDB collection, optionally filtered by a field and value.
        
        :param filter_field: Field to filter on (e.g., 'release_year')
        :param filter_value: Value to filter by (e.g., 2000)
        :return: pandas DataFrame of fetched data
        """
        # Construct the query
        query = {filter_field: filter_value} if filter_field and filter_value else {}
        
        # Fetch the data from the MongoDB collection
        data = list(self.collection.find(query))
        
        # Convert to DataFrame
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

    def fetch_by_year(self, year):
        """
        Fetch movies released in a specific year.
        
        :param year: Year to filter by (e.g., 2000)
        :return: pandas DataFrame of movies released in the specified year
        """
        return self.fetch_data(filter_field='release_year', filter_value=year)
    
    def get_movies_by_year_and_rating(self, release_year, min_rating):
        df = self.fetch_data(filter_field='release_year', filter_value=release_year)
        df['imdb_score'] = df['imdb_score'].astype(float)  # Ensure rating is float
        return df[df['imdb_score'] >= min_rating]


def main():
    # Create an instance of NetflixAPI
    netflix_api = db_NetflixAPI()
    print(sorted(netflix_api.fetch_data()['release_year'].unique()))
    # Fetch movies from the year 2001
    df = netflix_api.fetch_by_year(2001)
    
    # Print the first few rows of the DataFrame
    print(df.head())

if __name__ == '__main__':
    main()
