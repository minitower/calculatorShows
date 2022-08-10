# Open libs
import pandas as pd
import clickhouse_driver as ch
from dotenv import load_dotenv
import os

# Project script
from main import *
from cpaEncounter import cpaEnc
from approveEncounter import appEnc


def loadCheckData(host, user, password,
                  bid, ecpm, step):
    campaignsPriority = ['RU', 'KZ', 'UA', 'BY']
    campaigns=None

    with open('./queries/q2.sql', 'r') as f:
        q = f.read()
    q = q.replace('${BID}', str(bid))

    sqlCH = ch.Client(host=host,
                      user=user,
                      password=password)

    df = pd.DataFrame(sqlCH.execute(q))
    df.columns = ['campaigns', 'adv_id', 'shows',
                  'postbacks', 'ecpm']
    df['diff'] = abs(df['ecpm']-ecpm)
    df['geo'] = df['campaigns'].apply(lambda x: x[:2])
    df_diff = df.loc[df['diff'] == df['diff'].min()]
    for i in campaignsPriority:
        check = df_diff.loc[df_diff['geo'] == i]
        if not check.empty:
            campaigns = check['campaigns'].values[0+step]
            break
    if campaigns is None:
        campaigns = df_diff.sort_values(by='shows',
                                        ascending=False)['campaigns'].values[0+step]
    return campaigns


def resultParser(result):
    return dict(accurancy=result[0], mean=result[1],
                std=result[2], median=result[3],
                pred_n=result[4], alpha=result[5],
                beta=result[6], gamma=result[7],
                sumShows=result[8])

def getCampaignById(host, user, password, campaignId):
    with open('./queries/q_campaignId.sql', 'r') as f:
        q = f.read()
    q = q.replace('${CAMPAIGNS_ID}', str(campaignId))

    sqlCH = ch.Client(host=host,
                      user=user,
                      password=password)
    df = pd.DataFrame(sqlCH.execute(q))
    print(df)
    return df[0][0]


def getCampaignStatByName(host, user, password, campaign):
    with open('./queries/q_campaign_stat.sql', 'r') as f:
        q = f.read()
    q = q.replace('${NAME}', str(campaign))

    sqlCH = ch.Client(host=host,
                      user=user,
                      password=password)
    df = pd.DataFrame(sqlCH.execute(q))
    print(df)
    df.columns=['name', 'bid', 'approve', 'ctr', 'cr', 'epc', 'ecpm']
    bid = df['bid'].mean()
    approve = df['approve'].mean()
    ctr = df['ctr'].mean()
    cr = df['cr'].mean()
    epc = df['epc'].mean()
    ecpm = df['ecpm'].mean()
    return [bid, approve, ctr, cr, epc, ecpm]


def fullCalc(bid, approve, cr, ctr, epc, ecpm,
             pred_n, minAccurancy, campaignId, 
             campaignName, step=0):
    load_dotenv()
    host = os.environ.get("HOST")
    user = os.environ.get("CLICKHOUSE_USERNAME")
    password = os.environ.get("PASSWORD")
    if campaignId is None and campaignName is None:
        campaign = loadCheckData(host=host,
                                 user=user,
                                 password=password,
                                 bid=bid,
                                 ecpm=ecpm,
                                 step=step)
        paramDict = main(campaign=campaign,
                         pred_n=pred_n,
                         minAccurancy=minAccurancy,
                         full=True)

        if paramDict[0] == 'error 2' and step <= 3:
            paramDict = fullCalc(bid=bid, approve=approve, ctr=ctr,
                                    cr=cr, epc=epc, ecpm=ecpm, pred_n=pred_n, 
                                    minAccurancy=minAccurancy, step=step+1)

        elif paramDict[0] == 'error 2':
            paramDict = {'err': "Predict can't be calculated"}
        elif paramDict[0] != 'error 2':
            paramDict = resultParser(result=paramDict)
            paramDict.update(dict(bid=bid, approve=ctr, ctr=ctr, 
                                    cr=cr, epc=epc, ecpm=ecpm,
                                    campaign=campaign, sumClicks=paramDict['sumShows']*ctr,
                                    sumPostbacksUnconf=paramDict['sumShows']*ctr*cr,
                                    sumPostbacksConf=paramDict['sumShows']*ctr*cr*approve))
    else:
        if campaignId is not None:
            campaign = getCampaignById(host=host,
                                     user=user,
                                     password=password,
                                     campaignId=campaignId)
        elif campaignName is not None:
            campaign=campaignName

        userCPAShows = cpaEnc(campaign=campaign,
                                    user_bid=bid)
        
        userApproveShows = appEnc(campaign=campaign,
                                  user_approve=approve)
        meanDistance=(userCPAShows+userApproveShows)/2
        
        try:
            bid, approve, ctr, cr, epc, ecpm = getCampaignStatByName(host=host,
                                                    user=user,
                                                    password=password,
                                                    campaign=campaign)
        except ValueError:
            return {'err': "No shows"}
            
        paramDict, meanClicks, stdClicks, medianClicks, \
            meanPostbacks, stdPostbacks, medianPostbacks,\
            meanConfirmPostbacks, stdConfirmPostbacks, \
            medianConfirmPostbacks = mainAll(campaign=campaign,
                         pred_n=pred_n,
                         minAccurancy=minAccurancy,
                         userCPAShows=meanDistance,
                         ctr=ctr, cr=cr, approve=approve,
                         full=True)

        if paramDict[0] == 'error 2':
            paramDict = {'err': "Predict can't be calculated"}

        elif paramDict[0] != 'error 2':
            paramDict = resultParser(result=paramDict)
            paramDict.update(dict(bid=bid, approve=approve*100, ctr=ctr*100, 
                                cr=cr*100, epc=epc, ecpm=ecpm, campaign=campaign,
                                meanClicks=meanClicks, stdClicks=stdClicks, 
                                medianClicks=medianClicks, meanPostbacks=meanPostbacks, 
                                stdPostbacks=stdPostbacks, medianPostbacks=medianPostbacks,
                                meanConfirmPostbacks=meanConfirmPostbacks, 
                                stdConfirmPostbacks=stdConfirmPostbacks,
                                medianConfirmPostbacks=medianConfirmPostbacks, 
                                sumClicks=paramDict['sumShows']*ctr,
                                sumPostbacksUnconf=paramDict['sumShows']*ctr*cr,
                                sumPostbacksConf=paramDict['sumShows']*ctr*cr*approve))
    return paramDict