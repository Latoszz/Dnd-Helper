import configparser


def get_config(path="config.ini"):
    config = configparser.ConfigParser()
    config.read(path)

    return config
