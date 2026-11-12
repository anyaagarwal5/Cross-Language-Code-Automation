import configparser

config = configparser.ConfigParser()
config.read('config.ini')

gemini_cred = {
    'api_key': config['gemini']['api_key']
}

polyglot_frontend = {
    'base_url': config['polyglot-code-runner-frontend']['base_url']
}
