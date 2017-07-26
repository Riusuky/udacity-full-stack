# Log Analysis

This project consists of a python script that requests data from a article news database in order to generate a report.

## Getting Started

This project requires the user to have a [PostgreSQL](https://www.postgresql.org/) database server set up and running.

Before running any script, you need to create the `news` database in which we will be connecting to. To do that, enter the database terminal and run `CREATE DATABASE news`.

Next, you need to populate the database with the data we will be analyzing. To do that, unzip the file `scripts/newsdata.rar`. This will give you a file called `newsdata.sql` with all the commands to populate the news database. To run it, connect to the previously created `news` database (from the database server terminal run `\c news`) and run `\i path_to_the_newsdata.sql_file`, where `path_to_the_newsdata.sql_file` should be replaced by the path to the `newsdata.sql` file.

With the database populated, you need to create two views that are used in our queries. To create them, run the following commands on the database terminal connected to the `news` database:

`CREATE VIEW article_views AS
    SELECT articles.id AS id,
           articles.author AS author,
           title,
           COUNT(*) AS views
    FROM articles
        JOIN log ON log.path LIKE '/article/' || articles.slug
    WHERE method = 'GET'
          AND status LIKE '2%'
    GROUP BY title,
             articles.id
    ORDER BY views DESC;`

and

`CREATE VIEW request_errors_per_dar AS
    SELECT to_char(time, 'Month DD, YYYY') as date,
           (SUM(CASE WHEN status LIKE '2%' THEN 0.0 ELSE 1.0 END) / COUNT(*)) AS error
    FROM log
    GROUP BY date
    ORDER BY date;`

alternatively, you can also use the `scripts/views.sql` to create the views.

Finally, run the `scripts/reporting_tool.py` to generated the report. The reports are both printed and written in a file named `output.txt`.
