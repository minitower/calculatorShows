SELECT datetime, SUM(shows) 
FROM (SELECT datetime, sum(ad_shows) as shows, ad_id 
FROM luckyfeed.ad_shows
WHERE ad_id in (SELECT ad_id 
				FROM ads.ads 
				WHERE campaign_name LIKE '%${NAME}%')
GROUP BY datetime, ad_id) asu2
LEFT JOIN (SELECT ad_id, campaign_name FROM ads.ads) c ON c.ad_id == asu2.ad_id
WHERE campaign_name LIKE '%${NAME}%'
GROUP BY datetime;