from butter.base import env

def default_settings():
    """
    Depricated method to add env global variables to the env.settings dictionary
    Eventually these should be placed within env.settings.
    """
    print ('+ Using depricated default settings')
    if 'db_db' in env:
        env.settings.db_db = env.db_db
    if 'db_user' in env:
        env.settings.db_user = env.db_user
    if 'db_pw' in env:
        env.settings.db_pw = env.db_pw
    if 'db_host' in env:
        env.settings.db_host = env.db_host
    if 'smtp_pw' in env:
        env.settings.smtp_pw = env.smtp_pw
    if 'base_url' in env:
        env.settings.base_url = env.base_url
