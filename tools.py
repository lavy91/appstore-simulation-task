import pandas as pd
from sklearn.preprocessing import LabelEncoder


def freqs_to_probs(freqs):
    """Help function to turn frequencies into probability vector"""

    return freqs / freqs.sum()


def preprocess(log_data='simulator_assignment_dataset.csv'):
    """Data pre-processing function to clean and to extract useful variables"""
    # Import data and preprocessing

    data = pd.read_csv(log_data)
    data = data.sort_values('eventTime')

    # Encode userID and storeID

    lb_make = LabelEncoder()
    data['storeId'] = lb_make.fit_transform(data['storeId']).astype('str')
    data['uId'] = lb_make.fit_transform(data['uId']).astype('int')

    # Calculate StartTime

    startTime = pd.to_datetime(data[['eventTime', 'uId']].groupby(['uId'
                                                                   ]).first().eventTime.str[:22]).rename('startTime'
                                                                                                         )

    # Get Start date, day, weekend

    startDate = startTime.astype('str'
                                 ).str.slice(stop=10).rename('startDate')
    startDay = pd.to_datetime(startDate).dt.dayofweek.rename('startDay')
    weekend = (startDay > 4).rename('weekend')
    startHour = startTime.astype('str').str.slice(start=11,
                                                  stop=13).astype('int').rename('startHour')

    # Dummify action column

    df = pd.concat([data, pd.get_dummies(data['action'])], axis=1)

    df = pd.concat([
        1 * df.groupby(['uId']).sum(),
        data[['uId', 'storeId']].groupby(['uId']).first(),
        startDate,
        startDay,
        startHour,
        weekend,
        startTime,
    ], axis=1)

    df['activeActions'] = sum([df['appPageScroll'], df['appRedirect'],
                               df['galleryScroll'], df['openReviews'],
                               df['rmd']])

    # Filter df according to validity criteria

    df['validUser'] = (df['activeActions'] > 0) * (df['serverInit'] == 1) * df['viewAppPage'] + (
            df['activeActions'] == 0) * (df['serverInit'
                                         ] == 1)
    df = df[df['validUser'] == 1]

    # Sort Data Frame by time

    df = df.sort_values('startTime')

    # Define prior distribution parameters for CVR according to those who viewed the app

    prior_a = round(df[df.viewAppPage==1].mean().loc['appRedirect']
              * 100)
    prior_b = 100 - prior_a


    # This string represents the actions the user will/won't do

    df['userBehaviour'] = (1 * (df['appPageScroll'] > 0)).astype('str') + (1 * (df['galleryScroll'] > 0)).astype(
        'str') + (1
                  * (df['openReviews'] > 0)).astype('str') + (1 * (df['rmd']
                                                                   > 0)).astype('str') + (
                                  1 * (df['viewAppPage'] > 0)).astype('str'
                                                                      )

    # User Behaviour Data Frames

    userBehaviourDf = df.groupby(['storeId', 'weekend', 'userBehaviour'
                                  ]).describe()

    behaviourFreqs = userBehaviourDf.rmd['count']

    # Getting lambda rates for simulating the poisson process

    (testStartDate, testEndDate) = (df.iloc[0]['startDate'],
                                    df.iloc[-1]['startDate'])

    # Assuming our test lasts longer than 3 days

    trafficCount = df[(df.startDate != testStartDate) & (df.startDate
                                                         != testEndDate)].groupby(['weekend', 'startHour'
                                                                                   ]).rmd.count()

    weekdaysNum = len(df[(df.startDate != testStartDate) & (df.startDate
                                                            != testEndDate) & (df.weekend
                                                                               == 0)].startDate.unique())
    weekendDaysNum = len(df[(df.startDate != testStartDate) & (df.startDate
                                                               != testEndDate) & (df.weekend
                                                                                  == 1)].startDate.unique())
    (lambdasVecWeekday, lambdasVecWeekend) = (trafficCount[False]
                                              / weekdaysNum, trafficCount[True] / weekendDaysNum)

    # Getting median time per action to simulate time passing

    actionTimeDf = data.sort_values(['uId', 'eventTime'])

    # Getting the timedelta for consecutive actions

    actionTimeDf['actionTime'] = abs(pd.to_datetime(actionTimeDf.eventTime.str[:22])[::
                                                                                     -1].diff().astype(
        'timedelta64[ms]'))

    # We only want to look at consecutive actions for the same user

    actionTimeDf['changeUser'] = actionTimeDf.uId[::-1].diff()

    # This contains the median time for all actions given the store

    actionTimeVec = actionTimeDf[actionTimeDf['changeUser']
                                 == 0].groupby(['action'
                                                ]).median().actionTime / 1000

    return lambdasVecWeekday, lambdasVecWeekend, behaviourFreqs, userBehaviourDf, df, prior_a, prior_b, actionTimeVec
