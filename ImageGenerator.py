import re
import os

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from imdb import IMDb


class ImageGenerator:
    IMG_HEIGHT = 1200
    IMG_WIDTH = 1600

    MIN_EPISODE_WIDTH = 18

    BEST_WORST_ANCHOR = 230

    GREEN = (11, 115, 15)
    RED = (138, 26, 4)
    YELLOW = (230, 168, 34)
    BACKGROUND_COLOR = (242, 242, 242)
    BACKGROUND_COLOR_ALPHA = .5

    def __init__(self, show_id, background_image):
        self.show_id = show_id
        self.background_image = background_image

        self.title_font = ImageFont.truetype("resources/CenturyGothic.ttf", size=66)
        self.normal_font = ImageFont.truetype("resources/CenturyGothic.ttf", size=14)
        self.medium_font = ImageFont.truetype("resources/CenturyGothic.ttf", size=20)
        self.large_font = ImageFont.truetype("resources/CenturyGothic.ttf", size=24)

    def generate(self):
        ratings, show_title, highest_lowest = self.get_imdb_data()
        image = self.create_image(ratings, show_title, highest_lowest)

        if not os.path.exists("images/"):
            os.mkdir("images/")

        image.save("images/" + re.sub("[^a-zA-Z0-9\n]", "_", show_title) + "_IMDB_Ratings.png")

    def get_imdb_data(self):
        ratings = {}
        highest_lowest = {}
        DB = IMDb()

        series = DB.get_movie(self.show_id)

        if series["kind"] == "tv series":
            DB.update(series, "episodes")

            for season in series["episodes"]:
                season_ratings = {}
                for episode in series["episodes"][season]:
                    episode_data = series["episodes"][season][episode].data
                    season_ratings[episode] = round(episode_data["rating"], 1) if "rating" in episode_data else 0

                    if 0 not in highest_lowest or \
                            (season_ratings[episode] < highest_lowest[0]["rating"] and season_ratings[episode] != 0.0):
                        highest_lowest[0] = episode_data

                    if 1 not in highest_lowest or season_ratings[episode] > highest_lowest[1]["rating"]:
                        highest_lowest[1] = episode_data

                ratings[season] = season_ratings

        return ratings, series.data["localized title"], highest_lowest

    def create_image(self, ratings, show_title, highest_lowest):
        # Load background image
        base_image = self.get_background_image(self.background_image)

        # Create graph background layer

        # Draw data background rectangle
        faded_background = Image.new("RGBA", base_image.size, (0, 0, 0) + (0,))
        max_episodes = len(max(ratings.values(), key=lambda k: len(k)))

        rect_width = 100 + 40 * max_episodes if max_episodes > self.MIN_EPISODE_WIDTH \
            else 100 + 40 * self.MIN_EPISODE_WIDTH
        rect_height = 300 + 40 * len(ratings)

        rect_start = (int((self.IMG_WIDTH - rect_width) / 2), int((self.IMG_HEIGHT - rect_height) / 2))
        rect_end = (int(self.IMG_WIDTH - rect_start[0]), int(self.IMG_HEIGHT - rect_start[1]))
        ImageDraw.Draw(faded_background).rectangle(((rect_start[0], rect_start[1] - 90), rect_end),
                                                   fill=self.BACKGROUND_COLOR +
                                                        (int(255 * self.BACKGROUND_COLOR_ALPHA),))

        # Apply overlay to base image
        base_image = base_image.convert("RGBA")
        base_image = Image.alpha_composite(base_image, faded_background)
        base_image = base_image.convert("RGB")

        # Draw titel
        ImageDraw.Draw(base_image).text((self.IMG_WIDTH / 2, rect_start[1] - 20),
                                        show_title,
                                        fill="Black",
                                        anchor="ms",
                                        font=self.title_font)

        data_image = self.generate_data_image(ratings, (rect_width, rect_height), highest_lowest, max_episodes)
        base_image.paste(data_image, rect_start, data_image)

        return base_image

    def generate_data_image(self, ratings, rect_size, highest_lowest, max_episodes):
        data_overlay = Image.new("RGBA", rect_size, (0, 0, 0) + (0,))

        # Draw ratings table
        ratings_table = self.get_ratings_table(ratings, max_episodes)
        table_width = 40 * max_episodes + 100

        data_overlay.paste(ratings_table, (int((rect_size[0] - table_width) / 2), 0), ratings_table)
        # data_overlay.paste(ratings_table, (20 * max_episodes - 52 - 20, 0), ratings_table)

        # Draw worst episode
        self.draw_worst_episode(data_overlay, highest_lowest, len(ratings))

        # Draw best episode
        self.draw_best_episode(data_overlay, highest_lowest, len(ratings), rect_size)

        return data_overlay

    def get_ratings_table(self, ratings, max_episodes):
        rect_width = 100 + 40 * max_episodes
        rect_height = 300 + 40 * len(ratings)
        ratings_overlay = Image.new("RGBA", (rect_width, rect_height), (0, 0, 0) + (0,))

        # Draw season
        ImageDraw.Draw(ratings_overlay).text((40, 40), "Season", fill="Black", anchor="ms", font=self.normal_font)
        # Draw episode
        ImageDraw.Draw(ratings_overlay).text((50, 25), "Episode", fill="Black", anchor="ms", font=self.normal_font)
        # Draw episode number
        for episode in max(ratings.values(), key=lambda k: len(k)):
            ImageDraw.Draw(ratings_overlay).text((70 + 40 * episode, 30),
                                                 str(episode),
                                                 fill="Black",
                                                 anchor="ms",
                                                 font=self.normal_font)
        for s_index, season in enumerate(ratings.values(), start=1):
            # Draw season number
            ImageDraw.Draw(ratings_overlay).text((40, 30 + 40 * s_index),
                                                 str(s_index),
                                                 fill="Black",
                                                 anchor="ms",
                                                 font=self.normal_font)

            for e_index, episode_rating in enumerate(season.values(), start=1):
                background_rect_box = ((52 + 40 * e_index, 7 + 40 * s_index),
                                       (88 + 40 * e_index, 43 + 40 * s_index))

                # Draw episode background
                ImageDraw.Draw(ratings_overlay).rectangle(background_rect_box,
                                                          fill=self.get_rating_color(episode_rating))

                # Draw episode rating
                ImageDraw.Draw(ratings_overlay).text((70 + 40 * e_index, 30 + 40 * s_index),
                                                     str(episode_rating),
                                                     fill="Black",
                                                     anchor="ms",
                                                     font=self.normal_font)

        return ratings_overlay

    def draw_best_episode(self, data_overlay, highest_lowest, ratings, rect_size):
        ImageDraw.Draw(data_overlay).text((rect_size[0] - self.BEST_WORST_ANCHOR, 100 + 40 * ratings),
                                          "Best Rated Episode",
                                          fill="Black",
                                          anchor="ms",
                                          font=self.medium_font)
        ImageDraw.Draw(data_overlay).text((rect_size[0] - self.BEST_WORST_ANCHOR, 132 + 40 * ratings),
                                          "\"" + highest_lowest[1]["title"] + "\"",
                                          fill="Black",
                                          anchor="ms",
                                          font=self.large_font)
        ImageDraw.Draw(data_overlay).text((rect_size[0] - self.BEST_WORST_ANCHOR, 160 + 40 * ratings),
                                          "(" + highest_lowest[1]["original air date"] + ")",
                                          fill="Black",
                                          anchor="ms",
                                          font=self.normal_font)
        ImageDraw.Draw(data_overlay).text((rect_size[0] - self.BEST_WORST_ANCHOR, 180 + 40 * ratings),
                                          "Season " + str(highest_lowest[1]["season"]) +
                                          ", Episode " + str(highest_lowest[1]["episode"]),
                                          fill="Black",
                                          anchor="ms",
                                          font=self.normal_font)
        ImageDraw.Draw(data_overlay).text((rect_size[0] - self.BEST_WORST_ANCHOR, 245 + 40 * ratings),
                                          str(round(highest_lowest[1]["rating"], 1)),
                                          fill="Black",
                                          anchor="ms",
                                          font=self.title_font)

    def draw_worst_episode(self, data_overlay, highest_lowest, ratings):
        ImageDraw.Draw(data_overlay).text((self.BEST_WORST_ANCHOR, 100 + 40 * ratings),
                                          "Worst Rated Episode",
                                          fill="Black",
                                          anchor="ms",
                                          font=self.medium_font)

        ImageDraw.Draw(data_overlay).text((self.BEST_WORST_ANCHOR, 132 + 40 * ratings),
                                          "\"" + highest_lowest[0]["title"] + "\"",
                                          fill="Black",
                                          anchor="ms",
                                          font=self.large_font)

        ImageDraw.Draw(data_overlay).text((self.BEST_WORST_ANCHOR, 160 + 40 * ratings),
                                          "(" + highest_lowest[0]["original air date"] + ")",
                                          fill="Black",
                                          anchor="ms",
                                          font=self.normal_font)

        ImageDraw.Draw(data_overlay).text((self.BEST_WORST_ANCHOR, 180 + 40 * ratings),
                                          "Season " + str(highest_lowest[0]["season"]) +
                                          ", Episode " + str(highest_lowest[0]["episode"]),
                                          fill="Black",
                                          anchor="ms",
                                          font=self.normal_font)

        ImageDraw.Draw(data_overlay).text((self.BEST_WORST_ANCHOR, 245 + 40 * ratings),
                                          str(round(highest_lowest[0]["rating"], 1)),
                                          fill="Black",
                                          anchor="ms",
                                          font=self.title_font)

    def get_rating_color(self, rating):
        if rating > 5:
            color_1 = self.GREEN
            color_2 = self.YELLOW
            fraction = (rating - 5) / 5
        else:
            color_1 = self.YELLOW
            color_2 = self.RED
            fraction = rating / 5

        R = round((color_1[0] - color_2[0]) * fraction + color_2[0])
        G = round((color_1[1] - color_2[1]) * fraction + color_2[1])
        B = round((color_1[2] - color_2[2]) * fraction + color_2[2])

        return R, G, B

    def get_background_image(self, image_name):
        target_ratio = self.IMG_WIDTH / self.IMG_HEIGHT
        img = Image.open(image_name)

        if (img.width / img.height) > target_ratio:
            target_width = round(img.height * target_ratio)
            crop_area = (round((img.width - target_width) / 2), 0,
                         round(img.width - ((img.width - target_width) / 2)), img.height)
            img = img.crop(crop_area)

        elif (img.width / img.height) < target_ratio:
            target_height = round(img.width / target_ratio)
            crop_area = (0, round((img.height - target_height) / 2),
                         img.width, round(img.height - ((img.height - target_height) / 2)))
            img = img.crop(crop_area)

        # Resize image
        img = img.resize((self.IMG_WIDTH, self.IMG_HEIGHT))
        img = img.filter(ImageFilter.GaussianBlur(3))

        return img
