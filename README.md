# Simulator Task
In this task I built a pipeline to simulate users interaction with 3 versions of the same app in an appstore page based on a dataset representing a 2-week A/B/n test of an app detailing over 89K actions of approximately 14.5K app-store users.
which includes the following features:
1.	uId - a user ID string (unique).
2.	storeId - version ID string (unique).
3.	action - an action attributed to the user. Actions are either active (e.g. scrolling the page) or passive, in which case they reflect a state of the store for the user at a certain point in time (e.g. loading the store gallery).
Possible actions include:
-	serverInit - a request to load the store variation page (the variation is loaded in a browser). This action is prompted when a user clicks on the link that redirects to the test. Each user that clicks on the ad costs money for the client running the test. Note that clicking on an ad doesn’t guarantee that the user saw the page as he/she may close it before any assets are loaded.
-	viewAppPage - indicates that a user was exposed to all “first impression” assets of the store.
-	appRedirect - when a user clicks on the install/get button.
-	appPageScroll - when a user scrolls the page vertically.
-	galleryScroll - when a user scrolls the gallery (horizontally).
-	rmd - “read more description” when a user opens the app description.
-	openReviews - when a user opens the reviews section.

4.	eventTime - timestamp for the action.

The pipeline is comprised of 4 main parts:
## Pre-processing (tools.py)
In order to extract useful data from the csv given to me, some pre-processing had to be done:
1. Loading our data and re-labeling our user IDs and store IDs so that the names won't be as long.
![Raw data](https://github.com/lavy91/storemaven-task/blob/master/images/dfraw.png)
2. Transform our raw data by grouping by userId, make "dummy variables" for each possible action and sum them for each user.
![New data](https://github.com/lavy91/storemaven-task/blob/master/images/dfchanged.png)

3. Once we've done that, we can create a column that sums up all of the "active" actions, and this way easily filter out the invalid users using this formula:

<img src="https://latex.codecogs.com/gif.latex?\inline&space;\dpi{150}&space;\tiny&space;1_{valid}=&space;1_{(\sum&space;active&space;Actions)>0}*1_{viewAppPage}*1_{serverInit}&space;&plus;1_{(\sum&space;active&space;Actions)=0}*1_{serverInit}" title="\tiny 1_{valid}= 1_{(\sum active Actions)>0}*1_{viewAppPage}*1_{serverInit} +1_{(\sum active Actions)=0}*1_{serverInit}" />

4. Create a column representing user behaviour:
- Now that we made dummy variables for each action, we can tie all these variables into one string representing all the actions that the user has done (or not done). For example:
a user that scrolled the app page, didn't scroll the gallery, opened the reviews, didn't open the "read more description" tab and viewed the app page -->'10101'.

- By making this column we can group by user behaviours to see the distribution of different user behaviour between stores (userBehaviourDf, userBehaviourFreqs)

5. Making a column to represent the hour of the day and weekend status:
There seems to be a spike in the traffic and CVR during weekeends, this needs to be represented in our simulator.


![CVR weekend](https://github.com/lavy91/storemaven-task/blob/master/images/weekendcvr.png)
![Traffic weekend](https://github.com/lavy91/storemaven-task/blob/master/images/weekendtraffic.png)


6. The traffic rates change during different times of the day, we extract the average traffic rates for each hour of the day during weekdays and weekend (lambdasVecWeekday, lambdasVecWeekend)

7. We also extract the median time it takes for each action in order to simulate user interaction more accurately. (actionTimeVec)

8. Lastly, prior distribution parameters for the CVR are taken according to the CVR amongst all the users who have seen the app page. (prior_a, prior_b).

## Simulating User Arrival Times (Timeline.py)
The Poisson distribution is often used to model how many people walk into a bank/store in a day.
The time between each arrival of a person to the store follows an exponential distribution and all inter-arrival times are independent.
We use the same model to simulate user arrival times (serverInit times) using the class "Timeline".

The class recieves the start day of the simulation (0=Monday, 6=Sunday), start hour and duration of the simulation along with the traffic rates per hour for weekend and weekdays.

The "simulate_server_init_times" method runs a loop which keeps sampling inter-arrival time, t, where 
<img src="https://latex.codecogs.com/gif.latex?\inline&space;\dpi{150}&space;\tiny&space;t\sim&space;Exp(\lambda={relevant\&space;traffic\&space;rate})" title="\tiny T\sim Exp(\lambda={relevant\ traffic\ rate})" />

t is added to the time counter and that time is appended to the list of server_init_times.The method  follows that by checking if a day or hour has passed and updates lambda accordingly. The loop keeps running until the time counter has passed the selected duration of the test.

In the end we have a list of server_init_times, each one will ne assigned to a different user.

## Simulating User Interaction (User.py)
1. The first thing a user is assigned to is its server_init time from the previous section. As it initializes, it is assigned randomly to one of the 3 stores.
It also initializes an empty action log to document every action it will do later using the 'log_action' method which also advances the time counter according to an exponential distribution with the mean being the selected actions median time.

2. According to the selected store and if its a weekend/weekday a "behaviour" (discussed in the preprocessing section part 4) is selected according to the distribution of behaviours for the selected store (behaviourFreqs).

3. Once a behaviour is chosen we can say how many people in the selected store with this behaviour pattern downloaded the app (evidence_a) and how many didn't (evidence_b). 

4. The "interact" method represents the flow of a user's actions in the appstore page.
- The first action that must be executed for every user is the serverInit function.It is immediately logged in the user log.
- If the chosen behaviour is '00000' meaning the user wasn't even exposed to the app page, we stop there.
- Else we look at all the "1"s in the behaviour string, representing the list of possible actions and randomly select an action from there.
- Next we select how many times we'll do this action according to the distribution from the csv. We'll log the action according to the number of times selected and remove this action from the list. We'll keep doing this for all the "1"s in the list.

- At last we get to the most important action, whether the user has downloaded the app or not, given everything we know about him. We take a Bayesian approach to do this, meaning:

<img src="https://latex.codecogs.com/gif.latex?\tiny&space;1_{downloaded\&space;app}\sim&space;Ber(p\sim&space;Beta(a=prior_a&plus;evidence_a,b=prior_b&plus;evidence_b))" title="\tiny 1_{downloaded\ app}\sim Ber(p\sim Beta(a=prior_a+evidence_a,b=prior_b+evidence_b))" />

This way the sparsity of different "behaviour" groups is accounted for.


- If the bernoulli trial is successful the "appRedirect" action is logged.


## The Simulation Function (simulation.py)

The simulation function ties everything together. It uses Timeline to simulate serverInit times (random seed=3), assigns those to users, each user interacts with the app and all their actions are added to a large log which is exported to "simulation_results.csv" in the same format as the original csv except that the time is in hours units
Here you have the traffic and downloads from the real data (up) and the simulated data (down).
![Real](https://github.com/lavy91/storemaven-task/blob/master/images/actualdata.png)
![Sim](https://github.com/lavy91/storemaven-task/blob/master/images/simdata.png)


## Questions
1.	If there’s already a process for A/B/n testing what’s the point of experimenting with other algorithms?
- Just because we have a process in place for A/B/n testing, doesn't mean other algorithms can't preform better economically, i.e. reach similar levels of accuracy with a smaller sample size or that certain aspects of these algorithms can be incorporated to improve our existing process.
2. The optimal procedure would score best on these following criteria, all weighted according to the current economics (cost of traffic, computing cost, etc.):
- Highest accuracy in determining version with highest CVR
- Lowest algorithm development cost
- Lowest deployment cost
- Smallest sample size needed

3. Given an A/B/n testing statistical procedure and a simulation mechanism, describe the steps you would follow in order to assess the usefulness of the procedure?

- Given a statistical procedure we can run a certain A/B/n test.
- Feed the test data in the simulator to simulate this test a large number of times (lets say 100,000).
- Check in how many of these simulations the statistical procedure agreed with the simulation in regards to which version has the highest CVR.
- Check how this changes with different cut-off times for the test. Perhaps we could have stopped the test much sooner.
