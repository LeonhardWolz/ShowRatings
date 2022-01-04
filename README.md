# Television Show Ratings Image Generator
A script to generate images, that visualize television show episode ratings, based on IMDB ratings.

## How to Use

1. Get the IMDB ID for the tv show.

    https://www.imdb.com/title/tt **0460649**
2. Download any image you would like to use as the background. Place the image in the resources folder.

3. Create an entry in the _config.json_ file under shows and enter the information.
You can enter and generate images for more than one show at once.

```json
{
  "shows": [
    {
      "Title": "How I Met Your Mother",
      "IMDB_ID": "0460649",
      "BackgroundImage": "resources/YourBackground.jpg"
    }
  ]
}
```

4. Run the script
