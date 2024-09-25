import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import numpy as np
import re

# URL of the tags page
tags_url = "https://letterboxd.com/718cinemaclub/tags/"

# URL of 718's followers page
followers_url = "https://letterboxd.com/718cinemaclub/followers/"

# Function to get tags containing "win"
def get_tags_with_win():
    response = requests.get(tags_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    tags = {}
    
    # Find all tags with class "hoverable"
    tag_elements = soup.select('li.hoverable')
    
    for tag in tag_elements:
        tag_name = tag.text.strip()
        if 'win' in tag_name.lower():
            tag_link = tag.a['href']
            tags[tag_name] = tag_link  # Store tag name and its link
    return tags

# Function to get movies for each tag
def get_movies_for_tags(tags):
    movies_data = []  # List to store movie data
    
    for tag_name, tag_link in tags.items():
        tag_url = f"https://letterboxd.com{tag_link}"
        response = requests.get(tag_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all movie entries on the tag page
        movie_elements = soup.select('li.poster-container')

        for movie in movie_elements:
            div_element = movie.find('div', class_='poster')
            film_id = div_element.get('data-film-id')
            film_slug = div_element.get('data-film-slug')
            film_link = "https://letterboxd.com/film/" + film_slug
            
            img_tag = div_element.find('img')
            film_name = img_tag.get('alt')

            # Append a dictionary with movie data to the list
            movies_data.append({
                'Tag': tag_name,
                'Film Name': film_name,
                'Film ID': film_id,
                'Film Slug': film_slug,
                'Film Link': film_link,
            })

     # Convert to DataFrame and format
    movies_df = pd.DataFrame(movies_data)
    movies_df[['Winner', 'Wins']] = movies_df['Tag'].str.split('   ', expand=True)
    movies_df = movies_df.drop('Tag', axis=1)
    movies_df = pd.concat([movies_df.iloc[:,-2:], movies_df.iloc[:, :-2]], axis=1)
    movies_df['Wins'] = movies_df['Wins'].fillna(1)

    return movies_df

# Function to get a list of follower usernames
def get_followers():
    response = requests.get(followers_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Select follower links (these are typically inside 'a' tags with a specific class)
    follower_elements = soup.select('a.avatar')

    # Get the href attribute which links to the follower's page
    followers = []
    for follower in follower_elements:
        followers.append(follower['href'].strip('/'))  # Extract username from the URL

    return followers

# Function to get ratings from each follower per movie
def get_ratings(movies_df):
    slugs = movies_df['Film Slug'].tolist()
    movie_ratings = {}

    for slug in slugs:
        activity_url = f"https://letterboxd.com/718cinemaclub/friends/film/{slug}/"
        response = requests.get(activity_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Find all span elements with class 'rating'
        ratings = soup.find_all('span', class_='rating')

        # Extract all instances of the rating class
        rating_classes = [rating['class'][1] for rating in ratings if 'class' in rating.attrs]

        # Filter classes that start with 'rated-' and extract the number
        rating_numbers = [
            float(re.findall(r'\d+(?:\.\d+)?', rating_class)[0])
            for rating_class in rating_classes 
            if rating_class.startswith('rated-')
        ]
        
        # Store the extracted rating numbers in the dictionary
        movie_ratings[slug] = rating_numbers

    return movie_ratings

# Function to generate dataframe of movies, averages, and number of ratings
def get_ratings_df(ratings_dict):
    film_slugs = []
    average_ratings = []
    number_ratings = []

    # Loop through dictionary of ratings
    for title, ratings in ratings_dict.items():
        film_slugs.append(title)
        average_ratings.append(sum(ratings)/len(ratings) if ratings else 0)
        number_ratings.append(len(ratings))
    
    ratings_df = pd.DataFrame({
        'Film Title': film_slugs,
        'Average Rating': average_ratings,
        'Number of Ratings': number_ratings
    })

    return ratings_df

# Main script
if __name__ == "__main__":
    tags = get_tags_with_win()
    movies_df = get_movies_for_tags(tags)
    ratings_dict = get_ratings(movies_df)
    ratings_df = get_ratings_df(ratings_dict)

    # Write results to a CSV file
    movies_df.to_csv("movies_by_tag.csv", index=False)
    ratings_df.to_csv("ratings_by_movie.csv", index=False)
    
    print("done")
