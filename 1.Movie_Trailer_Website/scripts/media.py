class Movie():
    """Class that represents a movie in the movie trailer list.

    Args:
        title (str): Movie's title.
        poster_image_url (str): url of the movie's poster image.
        trailer_youtube_url (str): Youtube url for the movie's trailer.

    """

    def __init__(self, title, poster_image_url, trailer_youtube_url):
        self.title = title
        self.poster_image_url = poster_image_url
        self.trailer_youtube_url = trailer_youtube_url
