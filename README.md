# Youtube-Context-Research

Youtube Context Research allows you to pull data from two different YouTube channels with different political bias and return two .json files 
that retrieves videos from both channels based on a list of common search queries. 

## Dependencies

Use the package manager pip to install the following dependencies:

```bash
pip install google-api-python-client
```
```bash
pip install youtube_transcript_api
```
## Usage

There are several optional commands that the user could input in the CLI.

```bash
python -u YoutubeAPI.py -c1 "name of first channel" -c2 "name of second channel" -k "/path/to/keywords.txt" -api "Your API Key" 
```
The format is outlined above. 

To obtain an API Key, go to https://console.cloud.google.com to create a new project, add YouTube Data API v3 as an API to your project and obtain an API Key from authentication in order to run the file

A quickstart YouTube tutorial to create a project as such is located here : https://www.youtube.com/watch?v=-QMg39gK624

For your own search terms create a .txt file in the format of 

```bash
search term #1
search term #2
search term #3
search term #4
search term #5
... etc ..
```

in order to search for your own keywords. 

## Quickstart

```bash
python -u YoutubeAPI.py 
```
The quickstart will utilize the YouTube Data API V3 with a default API key to pull videos from CNN and Fox News YouTube Channel whose title has at least one match to any of the keywords outline in the file Search.txt

Included in the repo is the file JohnOliver.json, a .json file example that shows how the data is organized for viewing
