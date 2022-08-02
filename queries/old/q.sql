SELECT datetime, shows, name 
FROM (SELECT datetime, sum(ad_shows) as shows, advertiser_id 
FROM luckyfeed.ad_shows
WHERE advertiser_id in (SELECT user_id 
								FROM ads.campaigns 
								WHERE name LIKE '%${NAME}%')
GROUP BY datetime, advertiser_id) asu2
LEFT JOIN (SELECT user_id, name FROM ads.campaigns) c ON c.user_id == asu2.advertiser_id
WHERE name LIKE '%${NAME}%'