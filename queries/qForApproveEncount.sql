SELECT campaign_name, 
	campaignShows 
FROM (
		SELECT campaign_name,
			AVG(approve) as current_approve,
			AVG(shows) as campaignShows
		FROM (
			SELECT sum(postbacks_confirmed_count)/sum(postbacks_total_count) as approve, 
				ad_id, sum(ad_shows) as shows
			FROM luckyfeed.ad_shows
			WHERE ad_id in (SELECT ad_id 
							FROM ads.ads)
			GROUP BY ad_id) asu2
			LEFT JOIN (
			SELECT ad_id, campaign_name 
			FROM ads.ads) c ON c.ad_id == asu2.ad_id
		GROUP BY campaign_name) 

WHERE current_approve>${APPROVE}-${INTERVAL} and
			current_approve<${APPROVE}+${INTERVAL};