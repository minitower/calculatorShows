from dotenv import load_dotenv
from scipy.optimize import minimize
import plotly.graph_objects as go

from model.hw import HoltWinters
from services.minmizeStopper import *
from model.cross_val import CVScore
from model.marginCalc import *


def loadData(host, user, password, campaign_name):
    with open('model/queries/q.sql', 'r') as f:
        q = f.read()
    q=q.replace('${NAME}', campaign_name)
    q=q.replace('${MODE}', 'ad_shows')
    sqlCH = ch.Client(host=host,
                        user=user,
                        password=password)
    df = pd.DataFrame(sqlCH.execute(q))
    df.columns = ['datetime', 'shows', 'cpa']
    df['datetime'] = pd.to_datetime(df['datetime'])
    df['shows'] = df['shows'].astype(int)
    df = df.sort_values('datetime')
    df = df.drop(df.loc[df['shows'] == 0].index)\
            .reset_index().drop('index', axis=1)
    df = df[:-20]
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

def paramInit(df, x, callback=None):
    try:
        timeseriesCV = CVScore(df['new_shows'], n_split=3)
        opt = minimize(timeseriesCV.timeseriesCVscore, x0=x, method='Nelder-Mead', 
                        bounds=((0, 1), (0, 1), (0, 1)), options={'maxiter': 10000},
                        callback=callback)
    except IndexError:
        timeseriesCV = CVScore(df['new_shows'], n_split=2)
        opt = minimize(timeseriesCV.timeseriesCVscore, x0=x, method='Nelder-Mead', 
                        bounds=((0, 1), (0, 1), (0, 1)), options={'maxiter': 10000},
                        callback=callback)
    return opt

def HWPredict(df, opt, n_preds):
    hw = HoltWinters(df['new_shows'], slen=24, alpha=opt.x[0], 
                    beta=opt.x[1], gamma=opt.x[2], n_preds=n_preds,
                    scaling_factor=2.56)
    hw.triple_exponential_smoothing()
    return hw

def validation(df, hw):
    validation = pd.DataFrame({'new_shows': df['new_shows'], 'predict': hw.result})
    validation['SSR'] = (validation['new_shows'] - validation['predict'])**2
    validation['SST'] = (validation['new_shows'] - validation['new_shows'].mean())**2
    check = validation['SSR'].sum()/validation['SST'].sum()
    return check

def forecast(df, opt, n_preds):
    hw_forecast = HWPredict(df, opt, n_preds)
    forecast_arr = list(df['datetime'].values)
    for i in range(1, n_preds+1):
        forecast_arr.append(df['datetime'].values[-1]+pd.Timedelta(hours=i))
    forecast = pd.DataFrame(forecast_arr, columns=['datetime'])
    forecast['forecast'] = hw_forecast.result
    forecast['markers'] = [0]*len(hw_forecast.result)
    forecast.loc[forecast['datetime'] > df['datetime'].values[-1], 'markers'] = 1
    forecast = forecast.sort_values('datetime')
    return forecast

def plotBuilder(df, campaign, check):
    fig = go.Figure()
    forecast = df.loc[df['markers'] == 1]
    predict = df.loc[df['markers'] != 1]
    fig.add_trace(go.Scatter(x=predict['datetime'].values, 
                            y=predict['shows'].values,
                            name=f'Campaigns {campaign[0]}'))

    fig.add_trace(go.Scatter(x=predict['datetime'].values,
                                y=predict['forecast'].values, 
                                name='Predict Holt-Winters'))

    fig.add_trace(go.Scatter(x=forecast['datetime'].values,
                                y=forecast['forecast'].values, 
                                name=f'Forecast Holt-Winters for {int(len(forecast)/24)} days'))
    fig.update_layout(
        font_family="Courier New",
        title_text=f'Forecast of shows for campaign {campaign[0]} with accurancy {round(check*100, 5)}%'
    )
    fig.write_html(f'templates/plots/fullPlot_shows_{campaign}.html')
    print(f'Plot saved on templates/fullPlot_shows_{campaign}.html')
    
def main(campaign, pred_n, minAccurancy, custom_bid, 
         full=False):
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
                    campaign_name=campaign)
    df = CPASimulator(campaign, custom_bid).calcGrow(df)
    if len(df) <= 200:
        df2 = pd.DataFrame(pd.to_datetime(pd.date_range(start=df['datetime'].values[0], 
                                                        end=df['datetime'].values[-1], 
                                                        freq='1H')))
        df2 = df2.join(df.set_index('datetime'), on=0)
        df = df2.copy()
        df.columns = ['datetime', 'shows']
        df['shows'] = df['shows'].interpolate(method='nearest').astype(int)
    if df.empty:
        return ['error']
    df_daily = df.copy()
    df_daily['datetime'] = pd.to_datetime(df_daily['datetime']).dt.date
    df_daily = df_daily.groupby('datetime').sum()
    df_daily = df_daily.loc[df_daily.index + pd.Timedelta(days=1)
                             <= pd.Timestamp.today()]

    mean=df_daily['shows'].mean()
    std=df_daily['shows'].std()
    median=df_daily['shows'].median()
    # Optimise Holt-Winters vector
    xArr = [[0,0,0], [0,0,1], [1,0,0], 
            [0,0,1], [0,1,1], [1,0,1], 
            [1,1,0], [1,1,1]]
    n=0
    accurancy=0
    while accurancy <= minAccurancy and n<len(xArr):
        opt = paramInit(df, xArr[n], callback=MinimizeStopper(60).__call__)
        alpha=opt.x[0]
        beta=opt.x[1]
        gamma=opt.x[2]
        if alpha == 'err' and \
                    beta=='err' and \
                    gamma=='err':
            continue
        # Predict value for custom data
        hw = HWPredict(df, opt, 0)
        check = validation(df, hw)
        accurancy=round(1-check, pred_n)
        n+=1
    if accurancy <= minAccurancy:
        return ['error 2']
    predict = forecast(df, opt, pred_n)
    predict.loc[predict['forecast'] <= 0, 'forecast'] = 0
    df_save = predict[['datetime', 'forecast', 'markers']].join(df[['datetime', 'shows', 'new_shows']].set_index('datetime'), 
                                            on='datetime')
    df_save=df_save.sort_values(by='datetime').reset_index(drop=True)
    sumShows = df_save.loc[df_save['new_shows'].isna() == True]['forecast'].sum()
    campaignSave=campaign.replace(' | ', '_')

    #Build plot with HW result
    plotBuilder(df_save, campaignSave, accurancy)
    return [accurancy, mean, std, median, 
            pred_n, alpha, 
            beta, gamma, sumShows, df_save]

def mainAll(campaign, pred_n, minAccurancy, ctr, cr, approve, 
                    custom_approve, custom_bid):
    d = main(campaign, pred_n, minAccurancy, custom_bid)
    df_save = d.pop(-1)
    df_save['shows_forecast'] = df_save['forecast'].astype(int).copy()
    df_save = df_save.drop('forecast', axis=1)
    
    #Calculate stat for clicks
    meanClicks=int(d[1]*ctr)
    stdClicks=int(d[2]*ctr)
    medianClicks=int(d[3]*ctr)
    
    #Calculate stat for postbacks
    meanPostbacks=int(meanClicks*cr)
    stdPostbacks=int(stdClicks*cr)
    medianPostbacks=int(medianClicks*cr)
    
    #Calculate stat for confirmed postbacks
    meanConfirmPostbacks=int(meanPostbacks*approve)
    stdConfirmPostbacks=int(stdPostbacks*approve)
    medianConfirmPostbacks=int(medianPostbacks*approve)
    
    #Insert values to final table
    df_save['clicks_forecast'] = (df_save['shows_forecast']*ctr).astype(int).copy() 
    df_save['postbacks_forecast'] = (df_save['clicks_forecast']*cr).astype(int).copy()
    df_save['confirm_postbacks_forecast'] = (df_save['postbacks_forecast']*custom_approve).astype(int).copy()
    
    campaignSave=campaign.replace(' | ', '_')
    with open(f'./templates/tables/fullTable_{campaignSave}.html', 'w+') as f:
        f.write(df_save.to_html())
    return [d, meanClicks, stdClicks, medianClicks,
            meanPostbacks, stdPostbacks, medianPostbacks,
            meanConfirmPostbacks, stdConfirmPostbacks, medianConfirmPostbacks]