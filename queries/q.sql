SELECT datetime, name, SUM(ad_shows) as shows
FROM luckyfeed.ad_shows as2 
LEFT JOIN (SELECT name, user_id FROM ads.campaigns) c ON c.user_id == as2.advertiser_id
WHERE name LIKE '%${NAME}%'
GROUP BY datetime, name