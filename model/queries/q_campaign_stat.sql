SELECT campaign_name, AVG(bid), AVG(approve), AVG(ctr), AVG(cr), AVG(epc), AVG(ecpm)
FROM (SELECT AVG(IF(cpa_money=0,NULL,cpa_money)) as bid,
			sum(postbacks_confirmed_count)/sum(postbacks_total_count) as approve,	
			sum(clicks)/sum(ad_shows) as ctr,
			sum(postbacks_total_count)/sum(clicks) as cr,
			bid*sum(postbacks_confirmed_count)/sum(clicks) as epc,
			bid*sum(postbacks_confirmed_count)/sum(ad_shows)*1000 as ecpm, ad_id, sum(ad_shows) as shows
		FROM luckyfeed.ad_shows
		WHERE ad_id in (SELECT ad_id 
						FROM ads.ads 
						WHERE campaign_name LIKE '%${NAME}%')
GROUP BY ad_id) asu2
LEFT JOIN (SELECT ad_id, campaign_name FROM ads.ads) c ON c.ad_id == asu2.ad_id
WHERE bid is not NULL and 
		shows!=0
GROUP BY campaign_name;