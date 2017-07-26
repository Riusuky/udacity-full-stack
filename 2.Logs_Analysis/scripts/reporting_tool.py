#!/usr/bin/env python3

import psycopg2

DB_NAME = 'news'


def run_query(query):
    """Requests a given query to the DB."""
    try:
        news_connection = psycopg2.connect(database=DB_NAME)
        cursor = news_connection.cursor()

        cursor.execute(query)
    except psycopg2.Error as error:
        print('Failed to retrieve data from the news database.')
        print(error.pgerror)
        return None
    else:
        return cursor.fetchall()
        forum_db.close()


def format_query(row_format, header_format, header, rows):
    if rows is None:
        return 'Failed to retrieve data...'

    output = header_format.format(header[0], header[1])
    output += '\n'

    for row in rows:
        output += row_format.format(row[0], row[1])

    print(output)

    return output


def get_most_popular_articles():
    """Returns the top 3 most popular articles from the database."""
    query = """SELECT title,
                    views
             FROM article_views
             LIMIT 3;"""

    return format_query(
        '{:<45}\t{:>8}\n',
        '{:<45}\t{:>8}\n',
        ('ARTICLE TITLE', 'VIEWS'),
        run_query(query))


def get_most_popular_authors():
    """Returns a list of authors and their total article views."""
    query = """SELECT name,
                    SUM(views) AS views
             FROM authors
                JOIN article_views ON authors.id = article_views.author
             GROUP BY authors.id,
                      authors.name
             ORDER BY views DESC;"""

    return format_query(
        '{:<30}\t{:>8}\n',
        '{:<30}\t{:>8}\n',
        ('AUTHOR', 'VIEWS'),
        run_query(query))


def get_unlucky_days():
    """Returns the days that had article request fails percentage higher
    than 1%."""
    query = """SELECT date,
                      error
             FROM request_errors_per_dar
             WHERE error > 0.01;"""

    return format_query(
        '{:<20}\t{:<8.2%}\n',
        '{:<20}\t{:<8}\n',
        ('DATE', 'ERROR PERCENTAGE'),
        run_query(query))

with open('output.txt', 'w') as output_file:
    output_file.write(
        'What are the most popular three articles of all time?\n')
    output_file.write(get_most_popular_articles())
    output_file.write('\n\n')

    output_file.write(
        'Who are the most popular article authors of all time?\n')
    output_file.write(get_most_popular_authors())
    output_file.write('\n\n')

    output_file.write(
        'On which days did more than 1% of requests lead to errors?\n')
    output_file.write(get_unlucky_days())
    output_file.write('\n\n')
