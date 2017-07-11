import media
import httplib
import json
import fresh_tomatoes

TMDB_API_KEY = 'bd8bbad27dd75e98097e8012e05735cb'

tmdb_connection = httplib.HTTPSConnection('api.themoviedb.org')

def tmdb_api_get(connection, endpoint, payload):
    connection.request("GET", endpoint+'?api_key='+TMDB_API_KEY, payload)
    response = tmdb_connection.getresponse()

    if response.status == 200:
        return json.loads(response.read().decode('utf-8'))
    else:
        print('Could not retrieve data for endpoint "'+endpoint+'". Error: '+response.reason)
        return None

def tmdb_get_movie_youtube_video(connection, movie_id):
    movies_result = tmdb_api_get(connection, '/3/movie/{}/videos'.format(movie_id), '{}')

    if movies_result is not None:
        for movie in movies_result['results']:
            if movie['site'].lower() == 'youtube':
                movie_key = movie['key']
                # Quick hack to avoid selecting a video with a invalid youtube key
                if len(movie_key) >= 5:
                    return 'https://www.youtube.com/watch?v={}'.format(movie['key'])

        return None
    else:
        raise Exception


movie_list = []

try:
    # Gets global configuration
    tmdb_config = tmdb_api_get(tmdb_connection, '/3/configuration', '{}')
    tmdb_base_poster_url = ''

    if tmdb_config is not None:
        tmdb_image_config = tmdb_config['images']
        tmdb_base_poster_url = tmdb_image_config['base_url']+tmdb_image_config['poster_sizes'][-2]
    else:
        raise Exception

    # Gets popular movie list and instantiates our movie objects
    tmdb_popular = tmdb_api_get(tmdb_connection, '/3/movie/popular', '{}')

    if tmdb_popular is not None:
        popular_list = tmdb_popular['results']

        for i in range(15):
            movie = popular_list[i]
            movie_youtube_url = tmdb_get_movie_youtube_video(tmdb_connection, movie['id'])

            # print('title: {} | {} | {}'.format(movie['title'], movie['id'], movie_youtube_url))

            if movie_youtube_url is not None:
                movie_list.append(media.Movie(
                    movie['title'],
                    tmdb_base_poster_url+movie['poster_path'],
                    tmdb_get_movie_youtube_video(tmdb_connection, movie['id']),
                ))
    else:
        raise Exception
except:
    print('Could not retrieve data from TMDB.')
finally:
    tmdb_connection.close()

if movie_list:
    fresh_tomatoes.open_movies_page(movie_list)
else:
    print('Could not create movie trailer website.')
