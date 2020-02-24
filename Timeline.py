import numpy as np


class Timeline:
    """This class manages the timeline and simulates serverInit times as a Poisson process with a changing rate"""

    def __init__(self, lambdas_vec_weekend, lambdas_vec_weekday, start_day=0, duration_in_days=14, start_hour=0):
        self.lambdas_vec_weekend = lambdas_vec_weekend
        self.lambdas_vec_weekday = lambdas_vec_weekday
        self.duration = duration_in_days * 24
        self.end_time = start_hour + self.duration
        self.day = start_day
        self.day_of_week = self.day % 7
        self.weekend = self.day_of_week > 4
        self.time = start_hour
        self.hour = start_hour
        self.lambda_ = self.weekend * lambdas_vec_weekend[self.hour] + (1 - self.weekend) * lambdas_vec_weekday[self.hour]
        self.server_init_times = []

    def reset_lambda(self):
        """Resets the rate of server init times"""
        self.lambda_ = self.weekend * self.lambdas_vec_weekend[self.hour] + (1 - self.weekend) * self.lambdas_vec_weekday[self.hour]

    def simulate_server_init_times(self):
        """Runs simulation"""
        while self.time < self.end_time:
            # Generate the inter-event time from the exponential distribution
            inter_event_time = np.random.exponential(1 / self.lambda_)
            # Create copy of time to keep track of changes
            old_time = self.time
            # Updates time and list of server_init times
            self.time += inter_event_time
            self.server_init_times += [self.time]
            # Checks if a day has passed and updates accordingly
            if self.time % 24 < old_time % 24:
                self.day += 1
                self.hour += 1
                self.hour = self.hour % 24
                self.day_of_week = self.day % 7
                self.weekend = self.day_of_week > 4
                self.reset_lambda()
                # Checks if an hour has passed and updates lambda accordingly
            elif self.time % 1 < old_time % 1:
                self.hour += 1
                self.reset_lambda()

        # Remove last item as it exceeded the time limit
        self.server_init_times.pop()
