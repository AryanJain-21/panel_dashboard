"""
File: db_netflixapi.py
Author: Aryan Jain
Date: Oct. 15, 2024

An object-oriented API implementation that is connected to a database with MongoDB and functions
as data retrieval for Holo Viz Panel.
"""

import pandas as pd
from pymongo import MongoClient
from bson import ObjectId
import sankey as sk # Using sankey.py from class
import os 
from dotenv import load_dotenv

load_dotenv()

class db_NetflixAPI:
    
    def __init__(self, db_name='netflix_movies', collection_name='movies', connection_string=None):
        """
        With the MongoDB connection initialize the API with the collection in database
        """

        if connection_string is None:
            connection_string = os.getenv('MONGODB_CONNECTION_STRING')
    
        self.client = MongoClient(connection_string)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]
        self.data = self.get_data()
        self.data = db_NetflixAPI.clean_objectid(self.data)

    @staticmethod
    def clean_genre(genre):
        """
        Static method that cleans up the genre string data.
        
        genre - uncleaned string

        returns:
            cleaned list of genres from string
        
        """

        # Takes brackets and 's out, splitting by comma to make a list
        if isinstance(genre, str):
            return (genre.replace('[', '').replace(']', '').replace("'", "").strip()).split(",")
        
        return genre 
    
    @staticmethod
    def clean_objectid(df):
        """
        Static method that converts ObjectId fields in a DataFrame to strings for compatability with panel.

        df - dataframe of specified collection and db

        returns:
            df - dataframe that takes the objectID and makes it a string
        """
        
        # Goes through every column picking those of type object, to then go through and change into string
        for column in df.select_dtypes(include=[object]):

            if df[column].apply(lambda x: isinstance(x, ObjectId)).any():
                df[column] = df[column].astype(str)

        return df
    
    def get_data(self, filter_field=None, filter_value=None):
        """
        Get all data from Mongo Database, filtering by query if provided.

        filter_field - What column to filter by
        filter_value - What value to filter column by

        returns:
            dataframe with the filtered (if filter provided) data, or without filters, all data
        """

        # Gets filtered query, or if filter_field and filter_value is None, query returns all data
        query = {filter_field: filter_value} if filter_field and filter_value else {}
        # Takes away objectID to avoid potential errors
        data = list(self.collection.find(query, {'_id': False}))

        return pd.DataFrame(data)

    def get_years(self):
        """
        Gets all the unique release years from the MongoDB.

        returns:
            List of unique years from release_year
        """

        years = self.collection.distinct('release_year')

        return sorted(years)

    def get_unique_genres(self):
        """
        Gets all unique genres from MongoDB using pipeline aggregation.

        returns:
            list of unique genres within the database
        """

        # Break the lists of genres into indivdual entries, then group them together, getting unique genres
        pipeline = [
            {"$unwind": "$genres"},  
            {"$group": {"_id": "$genres"}}  
        ]
        result = self.collection.aggregate(pipeline)

        # Cleaning the genre output to be returned
        lst = []
        for dct in result:

            genre = db_NetflixAPI.clean_genre(dct['_id'])
            
            for x in genre:
                lst.append(x)

        return sorted(set(lst))

    def extract_local_network(self, release_year, min_rating, only_movies, only_tv):
        """
        Extracts a local network of movies/shows based on filters using the MongoDB.

        release_year (int) - What release year to match
        min_rating (float) - What lower bound for rating to match
        only_movies (boolean) - Filter by movies
        only_tv (boolean) - Filter by shows

        returns:
            df - dataframe with filtered values based on queries
        """

        pipeline = []

        # Match based on release year and lower limit IMDb score
        match_stage = {
            "$match": {
                "release_year": release_year,
                "imdb_score": {"$gte": min_rating}
            }
        }
        pipeline.append(match_stage)

        # Apply Movie/Show filters
        if only_movies and not only_tv:
            pipeline[0]["$match"]["type"] = 'MOVIE'
        elif only_tv and not only_movies:
            pipeline[0]["$match"]["type"] = 'SHOW'
        elif not only_movies and not only_tv:
            # If both are not selected then it returns values that do not include Movie and Show, or in this case
            # returns nothing
            pipeline[0]["$match"]["type"] = {'$nin': ['MOVIE', 'SHOW']}

        # Project only the required fields, excluding _id to avoid potential issues
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
                '_id': 0 
            }
        }
        pipeline.append(projection_stage)

        # The aggregation
        local_network = list(self.collection.aggregate(pipeline))
        
        # Convert to DataFrame
        df = pd.DataFrame(local_network)
        
        return df

    def get_media_details(self, title):
        """
        Getting details of a specific media from the MongoDB.
        
        title (str) - Name of media

        returns:
            Series - all data of media, none if no media is specified.
        """

        # Exclude _id to avoid potential errors, finding the media based on title selected
        media_details = self.collection.find_one({"title": title}, {'_id': False})  

        # When nothing selected, returns None, else will return the media details/data
        return pd.Series(media_details) if media_details else None

    def create_sankey_plot(self, sankey_data, sankey_width=1500, sankey_height=800, selected_genres=None):
        """
        Creates a Sankey diagram using provided data and sankey.py
        
        sankey_data (df) - Data to put on sankey diagram
        sankey_width (int) - Width of diagram
        sankey_height (int) - Height of diagram
        selected_genres (list of genres) - Genres to filter plot by, default all genres selected

        returns:
            fig - sankey diagram
        """

        # To clean genres and output movie to genre relations properly
        genre_df = None
        if not sankey_data.empty:
            # Going row by row to clean genres and adding src, targ columns
            rows = []
            for _, row in sankey_data.iterrows():

                # if statement added to avoid type error
                genre_lst = db_NetflixAPI.clean_genre(row['genres']) if isinstance(row['genres'], str) else []

                for genre in genre_lst:
                    # Appending each Media with the genres it is associated with
                    rows.append({'src': str(row['title']), 'targ': genre})

            # Put into dataframe to be used in sankey
            genre_df = pd.DataFrame(rows)

        # If no data to be showed (i.e. if both movies and tv show filters are off, none to be shown, thus returns nothing)
        if genre_df is None or genre_df.empty:
            return
        
        # Filter based on selected genres if given
        if selected_genres:
            genre_df = genre_df[genre_df['targ'].isin(selected_genres)]

        
        # Plot the Sankey diagram using sankey.py
        fig = sk.make_sankey(
            df=genre_df,
            src='src',
            targ='targ',
            width=sankey_width,
            height=sankey_height
        )
        return fig


