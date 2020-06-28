from apiclient.discovery import build
from datetime import datetime
import io
from googleapiclient.http import MediaIoBaseDownload
from youtube_transcript_api import YouTubeTranscriptApi
import argparse
import json

def print_title_from_search_results_video(res):
	for item in res['items']:
		print(item['snippet']['title'])


def print_channel_data(res):
	for item in res['items']:
		print(item['snippet'])


def search_videos(query):
	req = youtube.search().list(q=query, part='snippet', type='video',
								maxResults=5)  # Max 5 results, highest is 50 results, Searching for videos
	res = req.execute()  # JSON Format
	return res


def search_videos_by_dates(query, start_date, end_date):
	req = youtube.search().list(q=query, part='snippet', type='video', publishedAfter=start_date,
								publishedBefore=end_date,
								maxResults=5)  # Max 5 results, highest is 50 results, Searching for videos
	res = req.execute()  # JSON Format
	return res


def fetch_all_videos_by_channel(channel_id):
	res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
	uploads_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']  # Get uploaded playlist ids

	videos = []
	next_page_token = None
	pages = 6  # 6 Pages
	i = 0

	while i < pages:
		res = youtube.playlistItems().list(playlistId=uploads_id, part="snippet", maxResults=5,
										   pageToken=next_page_token).execute()
		videos += res['items']
		next_page_token = res['nextPageToken']

		if next_page_token is None:
			break

		i += 1

	return videos  # return list of videos


def print_title_from_videos_json(video):
	print(video['snippet']['title'])


def get_comment(video_id, next_page_token):
	try:
		if next_page_token is not None:
			comment_results = youtube.commentThreads().list(videoId=video_id, part="snippet", maxResults=50,
															pageToken=next_page_token).execute()
		else:
			comment_results = youtube.commentThreads().list(videoId=video_id, part="snippet", maxResults=50).execute()
		return comment_results
	except:
		return None


def get_comments_by_video_id(video_id):
	comments = []
	next_page_token = None
	pages = 2  # Two Pages
	i = 0

	while i < pages:
		comment_results = get_comment(video_id, next_page_token)
		if comment_results is not None:
			comments.extend(
				[item['snippet']['topLevelComment']['snippet']['textOriginal'] for item in comment_results['items']])

			next_page_token = comment_results.get('nextPageToken')
			
		else:
			break

		i += 1

	return comments


def get_video_id(video_res):
	return video_res['snippet']['resourceId']['videoId']

def get_transcripts(video_id):
	try:
		transcript = YouTubeTranscriptApi.get_transcript(video_id)
	except:
		return {}

	return transcript


def get_transcript_text(transcript):
	if transcript is not None:
		return [x['text'] for x in transcript]
	else:
		return ""


def construct_url(id):
	base_url = "https://www.youtube.com/watch?v="
	return base_url + id

def filter_based_on_keywords(title, keywords):
	return any(word in title.lower() for word in keywords) # Added lower case to improve searching

def fetch_all_videos_by_channel_with_search(channel_id, keywords):
	res = youtube.channels().list(id=channel_id, part='contentDetails').execute()
	uploads_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']  # Get uploaded playlist ids

	videos = []
	next_page_token = None
	pages = 20  # 6 Pages
	i = 0

	while i < pages:	  		
		res = youtube.playlistItems().list(playlistId=uploads_id, part="snippet", maxResults=50,
										   pageToken=next_page_token).execute()

		# Filter by keywords here 		
		videos_to_add = list(filter(lambda video: filter_based_on_keywords(video['snippet']['title'], keywords), res['items']))
		videos += videos_to_add

		next_page_token = res['nextPageToken']

		if next_page_token is None:
			break

		i += 1


	return videos  # return list of videos	

def get_channel_id(youtube, channel):
	res_channels = youtube.search().list(q=channel, part='snippet', type='channel',
								maxResults=5).execute()	
	channel_id = res_channels['items'][0]['snippet']['channelId']
	return channel_id

def get_user_keywords(path, file_name):
	user_keywords = open(path, "r+")
	keywords_string = user_keywords.readlines()
	keywords_string = [x.lower().rstrip() for x in keywords_string]
	return keywords_string

def write_to_json_one_video(title, URL, transcript,file_name):
	data = {}
	data['videos'] = []
	data['videos'].append({
		'title': title,
		'URL' : URL,
		'transcript': transcript,
		'comments': comments
	})

	with open(file_name, 'w') as outfile:
		json.dump(data, outfile)

	return data	

def write_to_json_batch(zip_data, file_name):
	data = {}
	data['videos'] = []
	for video_data in zip_data:
		if comments != [] or transcript != []:
			data['videos'].append({
				'title': video_data[0],
				'URL' : video_data[1],
				'transcript': video_data[2],
				'comments': video_data[3]
			})

	with open(file_name, 'w') as outfile:
		json.dump(data, outfile)

	return data		

def main():
	# 10 Videos Per 2 Channels, 100 Comments / video , Transcripts For Each Video
	# Fox News + CNN
	# Transcript - Time stamp + language at time

	parser = argparse.ArgumentParser()
	parser.add_argument("-c1", "--first_channel", required=False,
	help="first channel to retrieve data")
	parser.add_argument("-c2", "--second_channel", required=False,
	help="second channel to retrieve data")	
	parser.add_argument("-k", "--keywords_path", required=False, help = ".txt file containing keywords for searching")
	parser.add_argument("-api", "--api_key", required=False, help = "your api key")
	
	args = vars(parser.parse_args())

	# Getting User Input Args
	keywords_path = str(args["keywords_path"]) if args["keywords_path"] else ""
	channel_1 = str(args["first_channel"]) if args["first_channel"] else "fox news"
	channel_2 = str(args["second_channel"]) if args["second_channel"] else "CNN"
	default_keywords = ["riot", "george floyd", "protest", "crowd", "police", "black", "officer", "violent", "cop", "policing", "floyd"]
	keywords =  get_user_keywords(keywords_path) if keywords_path is not "" else default_keywords
	# Retrieving Channel Ids
	api_key =  str(args["api_key"]) if args["api_key"] else "AIzaSyCsCfOEng2WhtMHQoCi0FX48OPB5tw-F5g"
	youtube = build("youtube", "v3", developerKey=api_key)

	print("Searching For Channles ... ")
	fox_news_channel_id = get_channel_id(youtube, channel_1)
	cnn_channel_id = get_channel_id(youtube, channel_2)
	print("Search Completed ... ")
	
	print("Searching For Videos ... ")
	videos_fox_news = fetch_all_videos_by_channel_with_search(fox_news_channel_id, keywords)
	videos_cnn = fetch_all_videos_by_channel_with_search(cnn_channel_id, keywords)	
	print("Search Completed ... ")

	# Fetch Title Of Searched Videos
	title_fox_news = [video['snippet']['title'] for video in videos_fox_news]
	title_cnn = [video['snippet']['title'] for video in videos_cnn] 

	# Fetch ID of Searched Videos
	video_id_fox_news = [get_video_id(video) for video in videos_fox_news]
	video_id_cnn = [get_video_id(video) for video in videos_cnn]

	# Construct URL of Searched Videos
	video_url_fox_news = [construct_url(x) for x in video_id_fox_news]
	video_url_cnn = [construct_url(x) for x in video_id_cnn]

	# Fetch Comments By ID (100 Comments Per Video)
	comments_fox_news = [get_comments_by_video_id(video_id) for video_id in video_id_fox_news]
	comments_cnn = [get_comments_by_video_id(video_id) for video_id in video_id_cnn]

	# Fetch Transcripts With Time Stamp
	transcript_fox_news =  [get_transcripts(video_id) for video_id in video_id_fox_news]
	transcript_cnn =  [get_transcripts(video_id) for video_id in video_id_cnn]

	# Fetch Transcripts W/o Time Stamp
	transcript_fox_news_no_time_stamp =  [get_transcript_text(transcript) for transcript in transcript_fox_news]
	transcript_cnn_no_time_stamp =  [get_transcript_text(transcript) for transcript in transcript_cnn]
	
	# After this pre-processing phase, we have:
	# Title 
	# Video URL
	# Video ID
	# Transcript w/ Time Stamp	
	# Comments

	# Moving To JSON
	print("Writing To JSON Files .... ")	
	data_zip_fox_news = list(zip(title_fox_news, video_url_fox_news, transcript_fox_news, comments_fox_news))
	data_zip_cnn = list(zip(title_cnn, video_url_cnn, transcript_cnn, comments_cnn))
	data_fox_news = write_to_json_batch(data_zip_fox_news, "fox_news_data.json")
	data_cnn = write_to_json_batch(data_zip_cnn, "cnn_data.json")
	print("Finishing Writing To JSON Files .... ")


if __name__ == '__main__':
	main()