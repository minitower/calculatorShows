SELECT name, bid, approve, ctr, cr, epc, ecpm
FROM (SELECT SUM(cpa_money)/SUM(postbacks_total_count) as bid,
			sum(postbacks_confirmed_count)/sum(postbacks_total_count) as approve,	
			sum(clicks)/sum(ad_shows) as ctr,
			sum(postbacks_total_count)/sum(clicks) as cr,
						bid*sum(postbacks_confirmed_count)/sum(clicks) as epc,
			bid*sum(postbacks_confirmed_count)/sum(ad_shows)*1000 as ecpm, advertiser_id 
		FROM luckyfeed.ad_shows
		WHERE advertiser_id in (SELECT user_id 
								FROM ads.campaigns 
								WHERE name LIKE '%${NAME}%')
GROUP BY advertiser_id) asu2
LEFT JOIN (SELECT user_id, name FROM ads.campaigns) c ON c.user_id == asu2.advertiser_id
WHERE name LIKE '%${NAME}%';