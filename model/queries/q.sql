SELECT datetime, SUM(shows), AVG(cpa)
FROM (SELECT datetime, sum(ad_shows) as shows, 
		SUM(cpa_money) / SUM(postbacks_confirmed_count) as cpa, ad_id 
FROM luckyfeed.ad_shows
WHERE ad_id in (SELECT ad_id 
				FROM ads.ads 
				WHERE campaign_name LIKE '%${NAME}%')
GROUP BY datetime, ad_id) asu2
LEFT JOIN (SELECT ad_id, campaign_name FROM ads.ads) c ON c.ad_id == asu2.ad_id
WHERE campaign_name LIKE '%${NAME}%'
GROUP BY datetime
