from tools import preprocess
from Timeline import Timeline
from User import User
import pandas as pd
import numpy as np


def simulation(start_day=4, start_hour=8, duration_in_days=14 + 7 / 24, seed=3):
    """Runs full simulation and returns log"""
    lambdas_vec_weekday, lambdas_vec_weekend, behaviour_freqs, user_behaviour_df, df, prior_a, prior_b, action_time_vec\
        = preprocess()
    np.random.seed(seed)
    sim_log = []
    timeline = Timeline(lambdas_vec_weekend, lambdas_vec_weekday, start_day=start_day, duration_in_days=duration_in_days, start_hour=start_hour)
    timeline.simulate_server_init_times()

    for (i, time) in enumerate(timeline.server_init_times):
        user = User(i, time, behaviour_freqs, user_behaviour_df, df, prior_a, prior_b, action_time_vec)
        user.interact()
        sim_log += user.log

    sim_log_df = pd.DataFrame(sim_log, columns=['uId', 'storeId', 'action', 'eventTime']).sort_values('eventTime')

    sim_log_df.to_csv('simulation_results.csv')


if __name__ == "__main__":
    simulation()
