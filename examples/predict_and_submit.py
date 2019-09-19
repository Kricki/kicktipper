import kicktipper

GROUP_NAME = 'name'
USERNAME = None  # if None, the user if prompted for input
PASSWORD = None  # if None, the user if prompted for input
MATCHDAY = None  # if None, the upcoming matchday is predicted

tipper = kicktipper.TipperBundesliga(GROUP_NAME)
tipper.kicktipp_username = USERNAME
tipper.kicktipp_password = PASSWORD
tipper.login()

tipper.predict_and_submit_scores_for_matchday(MATCHDAY)
tipper.store_data_for_matchday_to_file(MATCHDAY)

tipper.logout()
