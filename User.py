from tools import freqs_to_probs
import numpy as np

action_idx_dict = {
    0: 'appPageScroll',
    1: 'galleryScroll',
    2: 'openReviews',
    3: 'rmd',
    4: 'viewAppPage',
}


class User:
    """This class creates a user, assigns him to a store and simulates interaction with the appstore page"""

    def __init__(self, user_id, server_init_time, behaviour_freqs, user_behaviour_df, df, prior_a, prior_b, action_time_vec):
        self.behaviour_freqs = behaviour_freqs
        self.user_behaviour_df = user_behaviour_df
        self.df = df
        self.prior_a = prior_a
        self.prior_b = prior_b
        self.action_time_vec = action_time_vec
        self.time = server_init_time
        self.user_id = user_id
        self.day = int(server_init_time / 24)
        self.day_of_week = self.day % 7
        self.weekend = self.day_of_week > 4
        self.hour = int(server_init_time) % 24
        self.store = np.random.choice(['0', '1', '2'])
        self.behaviour = np.random.choice(self.behaviour_freqs[self.store, self.weekend].index,
                                          p=freqs_to_probs(self.behaviour_freqs[self.store, self.weekend]))
        self.evidence_count = self.user_behaviour_df['appRedirect'].loc[self.store, self.weekend, self.behaviour]['count']
        self.evidence_a = round(self.evidence_count * self.user_behaviour_df['appRedirect'].loc[self.store, self.weekend,
                                                                                                self.behaviour]['mean'])
        self.evidence_b = self.evidence_count - self.evidence_a
        self.log = []

    def log_action(self, action):
        """logs an action and adds time according to an exponential distribution"""
        self.log += [{
            'uId': self.user_id,
            'storeId': self.store,
            'action': action,
            'eventTime': self.time,
        }]

        self.time += np.random.exponential(self.action_time_vec[action]) / (60 * 60)

    def interact(self):
        """Simulates user interaction with the appstore page"""
        # First of all serverInit
        self.log_action('serverInit')
        if self.behaviour == '00000':
            return
        # Second viewAppPage
        self.log_action('viewAppPage')
        # Take out the 'viewAppPage' action
        behaviour = list(self.behaviour)[:-1]
        # Then look at other actions (if there are any)
        possible_actions = [action_idx_dict[i] for (i, item) in enumerate(behaviour) if item == '1']
        num_of_possible_actions = len(possible_actions)
        # Do all actions prior to downloading
        for i in range(num_of_possible_actions):
            action = np.random.choice(possible_actions)
            action_freq_vec = freqs_to_probs((np.unique(self.df[action], return_counts=True)[1])[1:])
            action_n = np.random.choice(np.unique(self.df[action])[1:], p=action_freq_vec)
            for j in range(action_n):
                self.log_action(action)
            possible_actions.remove(action)

        # Will the user download based on everything we know
        if np.random.binomial(n=1, p=np.random.beta(a=self.prior_a + self.evidence_a, b=self.prior_b + self.evidence_b)):
            self.log_action('appRedirect')
