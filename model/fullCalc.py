# Project script
from model.main import *
from services.loger import Loger

def resultParser(result):
    return dict(accurancy=result[0], mean=result[1],
                std=result[2], median=result[3],
                pred_n=result[4], alpha=result[5],
                beta=result[6], gamma=result[7],
                sumShows=result[8])


def getCampaignById(host, user, password, campaignId):
    with open('model/queries/q_campaignId.sql', 'r') as f:
        q = f.read()
    q = q.replace('${CAMPAIGNS_ID}', str(campaignId))

    sqlCH = ch.Client(host=host,
                      user=user,
                      password=password)
    df = pd.DataFrame(sqlCH.execute(q))
    print(df)
    return df[0][0]


def getCampaignStatByName(host, user, password, campaign):
    with open('model/queries/q_campaign_stat.sql', 'r') as f:
        q = f.read()
    q = q.replace('${NAME}', str(campaign))

    sqlCH = ch.Client(host=host,
                      user=user,
                      password=password)
    df = pd.DataFrame(sqlCH.execute(q))
    df.columns = ['name', 'bid', 'approve', 'ctr', 'cr', 'epc', 'ecpm']
    bid = df['bid'].mean()
    approve = df['approve'].mean()
    ctr = df['ctr'].mean()
    cr = df['cr'].mean()
    epc = df['epc'].mean()
    ecpm = df['ecpm'].mean()
    return [bid, approve, ctr, cr, epc, ecpm]


def fullCalc(pred_n, minAccurancy, campaignId,
             campaignName, custom_approve, custom_bid):
    load_dotenv()
    loger=Loger()
    host = os.environ.get("HOST")
    user = os.environ.get("CLICKHOUSE_USERNAME")
    password = os.environ.get("PASSWORD")
    loger.calcStart()
    if campaignId is not None:
        campaign = getCampaignById(host=host,
                                   user=user,
                                   password=password,
                                   campaignId=campaignId)
    elif campaignName is not None:
        campaign = campaignName

    loger.campaignIdFound(campaign)
    try:
        bid, approve, ctr, cr, epc, ecpm = getCampaignStatByName(host=host,
                                                                 user=user,
                                                                 password=password,
                                                                 campaign=campaign)
    except ValueError:
        return {'err': "No shows"}

    loger.statLoad({'bid': bid, 'approve': approve,
                    'ctr': ctr, 'cr': cr, 'epc': epc, 
                    'ecpm': ecpm})
    if custom_bid is None:
        custom_bid = bid
    if custom_approve is None:
        custom_approve = approve
    
    if custom_approve >= 1:
        custom_approve = custom_approve / 100
    
    paramDict, meanClicks, stdClicks, medianClicks, \
    meanPostbacks, stdPostbacks, medianPostbacks, \
    meanConfirmPostbacks, stdConfirmPostbacks, \
    medianConfirmPostbacks = mainAll(campaign=campaign,
                                     pred_n=pred_n,
                                     minAccurancy=minAccurancy,
                                     ctr=ctr, cr=cr, approve=approve,
                                     custom_approve=custom_approve,
                                     custom_bid=custom_bid)

    if paramDict[0] == 'error 2':
        paramDict = {'err': "Predict can't be calculated"}

    elif paramDict[0] != 'error 2':
        paramDict = resultParser(result=paramDict)
        paramDict.update(dict(bid=bid, approve=approve * 100, ctr=ctr * 100,
                              cr=cr * 100, epc=epc, ecpm=ecpm, campaign=campaign,
                              meanClicks=meanClicks, stdClicks=stdClicks,
                              medianClicks=medianClicks, meanPostbacks=meanPostbacks,
                              stdPostbacks=stdPostbacks, medianPostbacks=medianPostbacks,
                              meanConfirmPostbacks=meanConfirmPostbacks,
                              stdConfirmPostbacks=stdConfirmPostbacks,
                              medianConfirmPostbacks=medianConfirmPostbacks,
                              sumClicks=paramDict['sumShows'] * ctr,
                              sumPostbacksUnconf=paramDict['sumShows'] * ctr * cr,
                              sumPostbacksConf=paramDict['sumShows'] * ctr * cr * custom_approve))
    return paramDict
