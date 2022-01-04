import json

from ImageGenerator import ImageGenerator


def main():
    with open("config.json") as config_file:
        config = json.load(config_file)
        for show in config["shows"]:
            ImageGenerator(int(show["IMDB_ID"]), show["BackgroundImage"]).generate()


if __name__ == '__main__':
    main()
