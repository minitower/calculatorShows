import pandas as pd
import clickhouse_driver as ch
from dotenv import load_dotenv
import os
from scipy.optimize import minimize
import plotly.graph_objects as go

from hw import HoltWinters
from minmizeStopper import *
from cross_val import CVScore


def loadData(host, user, password, campaign_name, mode, userCPAShows=None):
    modeDict = {'shows': 'ad_shows',
                'clicks': 'clicks', 
                'postbacks': 'postbacks_total_count',
                'confirm_postbacks': 'postbacks_confirmed_count'}
    with open('./queries/q.sql', 'r') as f:
        q = f.read()
    q=q.replace('${NAME}', campaign_name)
    q=q.replace('${MODE}', modeDict[mode])
    sqlCH = ch.Client(host=host,
                        user=user,
                        password=password)

    df = pd.DataFrame(sqlCH.execute(q))
    df.columns = ['datetime', mode]
    df['datetime'] = pd.to_datetime(df['datetime'])
    df[mode] = df[mode].astype(int)
    df = df.sort_values('datetime')
    df = df.drop(df.loc[df[mode] == 0].index)\
            .reset_index().drop('index', axis=1)
    df = df[:-20]
    
    if mode == 'shows':
        diff = abs(df['shows'].mean()-userCPAShows)/len(df)
        df['shows'] = df['shows']+diff
    return df

def loadDataLocal(path, campaign_name):
    df = pd.read_csv(path).drop('Unnamed: 0', axis=1)
    df.columns = ['datetime', 'campaings', 'shows']
    df = df.loc[df['campaings'] == campaign_name]
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime')
    df = df.drop(df.loc[df['shows'] == 0].index)\
            .drop(df.index.values[-5:])\
            .reset_index().drop('index', axis=1)
    return df

def paramInit(df, x, mode, callback=None):
    try:
        timeseriesCV = CVScore(df[mode], n_split=3)
        opt = minimize(timeseriesCV.timeseriesCVscore, x0=x, method='Nelder-Mead', 
                        bounds=((0, 1), (0, 1), (0, 1)), options={'maxiter': 10000},
                        callback=callback)
    except IndexError:
        timeseriesCV = CVScore(df[mode], n_split=2)
        opt = minimize(timeseriesCV.timeseriesCVscore, x0=x, method='Nelder-Mead', 
                        bounds=((0, 1), (0, 1), (0, 1)), options={'maxiter': 10000},
                        callback=callback)
    return opt

def HWPredict(df, opt, n_preds, mode):
    hw = HoltWinters(df[mode], slen=24, alpha=opt.x[0], 
                    beta=opt.x[1], gamma=opt.x[2], n_preds=n_preds,
                    scaling_factor=2.56)
    hw.triple_exponential_smoothing()
    return hw

def validation(df, hw, mode):
    validation = pd.DataFrame({mode: df[mode], 'predict': hw.result})
    validation['SSR'] = (validation[mode] - validation['predict'])**2
    validation['SST'] = (validation[mode] - validation[mode].mean())**2
    check = validation['SSR'].sum()/validation['SST'].sum()
    return check

def forecast(df, opt, n_preds, mode):
    hw_forecast = HWPredict(df, opt, n_preds, mode)
    forecast_arr = list(df['datetime'].values)
    for i in range(1, n_preds+1):
        forecast_arr.append(df['datetime'].values[-1]+pd.Timedelta(hours=i))
    forecast = pd.DataFrame(forecast_arr, columns=['datetime'])
    forecast['forecast'] = hw_forecast.result
    forecast['markers'] = [0]*len(hw_forecast.result)
    forecast.loc[forecast['datetime'] > df['datetime'].values[-1], 'markers'] = 1
    forecast = forecast.sort_values('datetime')
    return forecast

def plotBuilder(df, campaign, check, mode, full=False):
    fig = go.Figure()
    forecast = df.loc[df['markers'] == 1]
    predict = df.loc[df['markers'] != 1]
    fig.add_trace(go.Scatter(x=predict['datetime'].values, 
                            y=predict[mode].values,
                            name=f'Campaigns {campaign[0]}'))

    fig.add_trace(go.Scatter(x=predict['datetime'].values,
                                y=predict['forecast'].values, 
                                name='Predict Holt-Winters'))

    fig.add_trace(go.Scatter(x=forecast['datetime'].values,
                                y=forecast['forecast'].values, 
                                name=f'Forecast Holt-Winters for {int(len(forecast)/24)} days'))
    fig.update_layout(
        font_family="Courier New",
        title_text=f'Forecast of {mode} for campaign {campaign[0]} with accurancy {round(check*100, 5)}%'
    )
    if full:
        fig.write_html(f'templates/plots/fullPlot_{mode}_{campaign}.html')
        print(f'Plot saved on templates/fullPlot_{mode}_{campaign}.html')
    else:
        fig.write_html(f'templates/plots/plot_{mode}_{campaign}.html')
        print(f'Plot saved on templates/plot_{mode}_{campaign}.html')
    

def main(campaign, pred_n, minAccurancy, userCPAShows, full=False, mode='shows'):
    """
        mode: one of ['clicks', 'shows', 'postbacks', 'confirm_postbacks']
    """
    #WARN: for this script is nercessury: 
    #1. Data length must be more then 24 dots (1 dot==1 hour)
    # Load enviroment variables
    load_dotenv()
    # Load program constant
    host=os.environ.get("HOST")
    user=os.environ.get("CLICKHOUSE_USERNAME")
    password=os.environ.get("PASSWORD")
    # Load data from database
    #df = loadDataLocal('./test.csv', campaign)
    df = loadData(host=host, user=user, password=password,
                    campaign_name=campaign, userCPAShows=userCPAShows, 
                    mode=mode)
    if len(df) <= 200:
        df2 = pd.DataFrame(pd.to_datetime(pd.date_range(start=df['datetime'].values[0], 
                                                        end=df['datetime'].values[-1], 
                                                        freq='1H')))
        df2 = df2.join(df.set_index('datetime'), on=0)
        df = df2.copy()
        df.columns = ['datetime', mode]
        df[mode] = df[mode].interpolate(method='nearest').astype(int)
    if df.empty:
        return ['error']
    df_daily = df.copy()
    df_daily['datetime'] = pd.to_datetime(df_daily['datetime']).dt.date
    df_daily = df_daily.groupby('datetime').sum()
    df_daily = df_daily.loc[df_daily.index + pd.Timedelta(days=1)
                             <= pd.Timestamp.today()]

    mean=df_daily[mode].mean()
    std=df_daily[mode].std()
    median=df_daily[mode].median()
    # Optimise Holt-Winters vector
    xArr = [[0,0,0], [0,0,1], [1,0,0], 
            [0,0,1], [0,1,1], [1,0,1], 
            [1,1,0], [1,1,1]]
    n=0
    accurancy=0
    while accurancy <= minAccurancy and n<len(xArr):
        opt = paramInit(df, xArr[n], mode, callback=MinimizeStopper(60).__call__)
        alpha=opt.x[0]
        beta=opt.x[1]
        gamma=opt.x[2]
        if alpha == 'err' and \
                    beta=='err' and \
                    gamma=='err':
            continue
        # Predict value for custom data
        hw = HWPredict(df, opt, 0, mode)
        check = validation(df, hw, mode)
        accurancy=round(1-check, pred_n)
        n+=1
    if accurancy <= minAccurancy:
        return ['error 2']
    predict = forecast(df, opt, pred_n, mode)
    predict.loc[predict['forecast'] <= 0, 'forecast'] = 0
    df_save = predict[['datetime', 'forecast', 'markers']].join(df[['datetime', mode]].set_index('datetime'), 
                                            on='datetime')
    df_save=df_save.sort_values(by='datetime').reset_index(drop=True)
    sumShows = df_save.loc[df_save[mode].isna() == True]['forecast'].sum()
    campaignSave=campaign.replace(' | ', '_')

    #Build plot with HW result
    plotBuilder(df_save, campaignSave, accurancy, mode, full)
    return [accurancy, mean, std, median, 
            pred_n, alpha, 
            beta, gamma, sumShows, df_save]

def loadStat(campaign, mode):
    load_dotenv()
    # Load program constant
    host=os.environ.get("HOST")
    user=os.environ.get("CLICKHOUSE_USERNAME")
    password=os.environ.get("PASSWORD")
    
    df = loadData(host=host, user=user, password=password,
                    campaign_name=campaign, mode=mode)
    if len(df) <= 200:
        df2 = pd.DataFrame(pd.to_datetime(pd.date_range(start=df['datetime'].values[0], 
                                                        end=df['datetime'].values[-1], 
                                                        freq='1H')))
        df2 = df2.join(df.set_index('datetime'), on=0)
        df = df2.copy()
        df.columns = ['datetime', mode]
        df[mode] = df[mode].interpolate(method='nearest').astype(int)
    if df.empty:
        return ['error']
    df_daily = df.copy()
    df_daily['datetime'] = pd.to_datetime(df_daily['datetime']).dt.date
    df_daily = df_daily.groupby('datetime').sum()
    df_daily = df_daily.loc[df_daily.index + pd.Timedelta(days=1)
                             <= pd.Timestamp.today()]
    return [df_daily[mode].mean(), df_daily[mode].std(), df_daily[mode].median()]

def mainAll(campaign, pred_n, minAccurancy, ctr, cr, approve, userCPAShows, full=False):
    d = main(campaign, pred_n, minAccurancy, full, userCPAShows, mode='shows')
    df_save = d.pop(-1)
    df_save['shows_forecast'] = df_save['forecast'].astype(int).copy()
    df_save = df_save.drop('forecast', axis=1)
    
    tmp = loadStat(campaign, mode='clicks')
    meanClicks=tmp[0]
    stdClicks=tmp[1]
    medianClicks=tmp[2]
    df_save['clicks_forecast'] = (df_save['shows_forecast']*ctr).astype(int).copy()

    tmp = loadStat(campaign, mode='postbacks')
    meanPostbacks=tmp[0]
    stdPostbacks=tmp[1]
    medianPostbacks=tmp[2]
    df_save['postbacks_forecast'] = (df_save['clicks_forecast']*cr).astype(int).copy()

    tmp = loadStat(campaign, mode='confirm_postbacks')
    meanConfirmPostbacks=tmp[0]
    stdConfirmPostbacks=tmp[1]
    medianConfirmPostbacks=tmp[2]
    df_save['confirm_postbacks_forecast'] = (df_save['clicks_forecast']*approve).astype(int).copy()
    
    campaignSave=campaign.replace(' | ', '_')
    if full:
        with open(f'./templates/tables/fullTable_{campaignSave}.html', 'w+') as f:
            f.write(df_save.to_html())
    else:
        with open(f'./templates/tables/table_{campaignSave}.html', 'w+') as f:
            f.write(df_save.to_html())
    return [d, meanClicks, stdClicks, medianClicks,
            meanPostbacks, stdPostbacks, medianPostbacks,
            meanConfirmPostbacks, stdConfirmPostbacks, medianConfirmPostbacks]