SELECT AVG(margin)
FROM (SELECT ad_id, AVG(shows) as avgShows, 
		AVG(cpa) as avgCPA, quantile(0.1)(shows) as minShows, 
		quantile(0.1)(cpa) as minCPA,
		avgShows-minShows as diffShows, 
		avgCPA-minCPA as diffCPA,
		diffShows/diffCPA as margin
FROM (SELECT datetime, sum(ad_shows) as shows,
			SUM(cpa_money) as cpa, ad_id 
		FROM luckyfeed.ad_shows
		WHERE ad_id in (SELECT ad_id 
						FROM ads.ads 
						WHERE campaign_name LIKE '%${NAME}%') and
		toDate(datetime) <= today() - 7
GROUP BY datetime, ad_id) asu2
LEFT JOIN (SELECT ad_id, campaign_name FROM ads.ads) c ON c.ad_id == asu2.ad_id
WHERE campaign_name LIKE '%${NAME}%' and 
		shows != 0 and 
		cpa!= 0
GROUP BY ad_id)
WHERE diffShows!=0 and diffCPA!=0;