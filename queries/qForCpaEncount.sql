SELECT * FROM (SELECT campaign_name, 
		AVG(bid) as current_bid, 
		AVG(shows) as campaignShows
FROM (SELECT AVG(IF(cpa_money=0,NULL,cpa_money)) as bid, 
			ad_id, sum(ad_shows) as shows
		FROM luckyfeed.ad_shows
		WHERE ad_id in (SELECT ad_id 
						FROM ads.ads)
GROUP BY ad_id) asu2
LEFT JOIN (SELECT ad_id, campaign_name FROM ads.ads) c ON c.ad_id == asu2.ad_id
GROUP BY campaign_name) 
WHERE current_bid>${BID}-${INTERVAL} and
			current_bid<${BID}+${INTERVAL};