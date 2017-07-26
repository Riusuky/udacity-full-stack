CREATE VIEW article_views AS
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
    ORDER BY views DESC;

CREATE VIEW request_errors_per_dar AS
    SELECT to_char(time, 'Month DD, YYYY') as date,
           (SUM(CASE WHEN status LIKE '2%' THEN 0.0 ELSE 1.0 END) / COUNT(*)) AS error
    FROM log
    GROUP BY date
    ORDER BY date;
