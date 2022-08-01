with bid as (SELECT ${BID})
SELECT name, advertiser_id, sum(ad_shows) as shows,
		sum(postbacks_confirmed_count) as postbacks,
		1500*postbacks/shows*1000 as ecpm
FROM (SELECT toDayOfYear(datetime) as date,
			advertiser_id, 
			sum(ad_shows) as ad_shows,
			sum(postbacks_confirmed_count) as postbacks_confirmed_count
		FROM luckyfeed.ad_shows
		WHERE datetime >= today()-1
		GROUP BY date, advertiser_id) asu2
LEFT JOIN (SELECT user_id, name 
			FROM ads.campaigns) c ON c.user_id == asu2.advertiser_id
GROUP BY advertiser_id, name