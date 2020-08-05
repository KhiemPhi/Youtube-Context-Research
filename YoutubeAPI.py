from apiclient.discovery import build
from datetime import datetime
import io
from googleapiclient.http import MediaIoBaseDownload
from youtube_transcript_api import YouTubeTranscriptApi
import argparse
import json


api_key = "AIzaSyA3xjb6-8Vn2cqtLAi9i5PnnpwQTPusfkg"                               #"AIzaSyCsCfOEng2WhtMHQoCi0FX48OPB5tw-F5g" #"AIzaSyDmNm6s3IGZ7wgaAttggEuN606GzzoZMdQ"#"AIzaSyDmNm6s3IGZ7wgaAttggEuN606GzzoZMdQ" #"AIzaSyCsCfOEng2WhtMHQoCi0FX48OPB5tw-F5g"
youtube = build("youtube", "v3", developerKey=api_key)

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
	pages = 20  # Two Pages
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

def get_comment_replies(parent_id):
	replies = []
	next_page_token = None
	pages = 1
	i = 0

	while i < pages:
		replies_results = youtube.comments().list(parentId=parent_id, part="snippet", maxResults=100
															).execute()
		#Sort by most likes
		
		if replies_results is not None:

			replies.extend(
				[item['snippet']['textOriginal'] for item in replies_results['items']])
		else:
			break

		i += 1

	return replies	


def get_comments_by_video_id_with_replies(video_id):
	comments = []
	next_page_token = None
	pages = 1  # Two Pages
	i = 0
	comments_with_replies = {}

	while i < pages:
		comment_results = youtube.commentThreads().list(videoId=video_id, part="snippet", maxResults=100, order="relevance",
															pageToken=next_page_token).execute()
		if comment_results is not None:
			comments.extend(
				[  (item['snippet']['topLevelComment']['snippet']['textOriginal'], item['snippet']['topLevelComment']['snippet']['likeCount'] ) for item in comment_results['items']])
			parent_comments =	[item['snippet']['topLevelComment']['snippet']['textOriginal'] for item in comment_results['items']]
			parent_ids = [item['snippet']['topLevelComment']['id'] for item in comment_results['items']] 
			# With All Parent's IDS, we loop through them to get the children a.k.a the replies to each of these comments
			
			child_comments = [ get_comment_replies(parent_id) for parent_id in parent_ids ]


			parent_child_dict = dict(zip(parent_comments, child_comments))
			comments_with_replies.update(parent_child_dict)

			next_page_token = comment_results.get('nextPageToken')
			
		else:
			break

		i += 1

	return comments, comments_with_replies

def write_to_json_batch_with_replies(zip_data, file_name):
	data = {}
	data['videos'] = []
	for video_data in zip_data:
		data['videos'].append({
				'title': video_data[0],
				'URL' : video_data[1],
				'transcript': video_data[2],
				'comments': video_data[3],
				'comments_with_replies': video_data[4],
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
	default_keywords = ["Covid-19", "coronavirus", "open", "pandemic", "virus", "texas", "doctor", "patients", "vaccine", "fauci", "masks", 
	"cases", "sick" ]
	keywords =  get_user_keywords(keywords_path) if keywords_path is not "" else default_keywords
	api_key = str(args["api_key"]) if args["api_key"] else "AIzaSyA3xjb6-8Vn2cqtLAi9i5PnnpwQTPusfkg"
	
	#API_Keys:
	#"AIzaSyAzZrFfHWnwthIxKp9PBzmYNPgkpKuljb0" 
	#"AIzaSyBdf-Vcv9PQqTbhIuqEqFX9hR_JJV6LJa0" 
	#"AIzaSyB2H7mJ9AaCoesfLjD2SpFcib__VQI41Y8"  
	#"AIzaSyDmNm6s3IGZ7wgaAttggEuN606GzzoZMdQ" 
	#"AIzaSyA3xjb6-8Vn2cqtLAi9i5PnnpwQTPusfkg"
	#Testing With A Basic Corona Virus Video

	'''
	video_id1 = "CPIOkO2lJU8"
	video_id2 = "6NjCitwKJSQ"
	
	title = "Texas doctor: Patients are near death, coming in too late"
	URL = construct_url(video_id1)
	transcript = get_transcripts(video_id1)
	comments, comments_with_replies = get_comments_by_video_id_with_replies(video_id1)
	print("Writing To JSON Files .... ")	
	data_zip = list(zip([title], [URL], [transcript], [comments], [comments_with_replies] ))
	data = write_to_json_batch_with_replies(data_zip, "test_data_cnn_with_replies_large.json")
	print("Finish Writing To JSON_Files")

	title = "Tucker: What is the actual death rate of COVID-19?"
	URL = construct_url(video_id2)
	transcript = get_transcripts(video_id2)
	comments, comments_with_replies = get_comments_by_video_id_with_replies(video_id2)
	print("Writing To JSON Files .... ")	
	data_zip = list(zip([title], [URL], [transcript], [comments], [comments_with_replies] ))
	data = write_to_json_batch_with_replies(data_zip, "test_data_fox_news_with_replies_large.json")
	print("Finish Writing To JSON_Files")
	'''	

	print("Searching For Channels ... ")
	fox_news_channel_id = get_channel_id(youtube, channel_1)
	cnn_channel_id = get_channel_id(youtube, channel_2)
	print("Search Completed ... ")
	
	print("Searching For Videos ... ")
	videos_fox_news = fetch_all_videos_by_channel_with_search(fox_news_channel_id, keywords)[0:20]
	videos_cnn = fetch_all_videos_by_channel_with_search(cnn_channel_id, keywords)[0:20]	
	print("Search Completed ... ")

	# Fetch Title Of Searched Videos
	print ("Fetching Video Titles ... ")
	title_fox_news = [video['snippet']['title'] for video in videos_fox_news]
	title_cnn = [video['snippet']['title'] for video in videos_cnn] 
	print ("Finish Fetching Video Titles ... ")

	# Fetch ID of Searched Videos
	print ("Fetching Video-IDS ... ")
	video_id_fox_news = [get_video_id(video) for video in videos_fox_news]
	video_id_cnn = [get_video_id(video) for video in videos_cnn]
	print("Finish Fetching Video IDS ... ")

	# Construct URL of Searched Videos

	print("Generating URLs From IDS ... ")
	video_url_fox_news = [construct_url(x) for x in video_id_fox_news]
	video_url_cnn = [construct_url(x) for x in video_id_cnn]
	print("Finish Generating URLs from IDS ... ")

	print("Fetching Comments + Replies ... ")

	comments_fox_news = []
	comments_with_replies_fox_news = []
	for video_id in video_id_fox_news:
		comments, comments_with_replies = get_comments_by_video_id_with_replies(video_id)
		comments_fox_news.append(comments)
		comments_with_replies_fox_news.append(comments_with_replies)

	comments_cnn = []
	comments_with_replies_cnn = []
	for video_id in video_id_cnn:
		comments, comments_with_replies = get_comments_by_video_id_with_replies(video_id)
		comments_cnn.append(comments)
		comments_with_replies_cnn.append(comments_with_replies)	
	
	print("Finish Fetching Comments + Replies ... ")

	# Fetch Transcripts With Time Stamp
	print("Fetching Transcripts W/ Time Stamp ... ")
	transcript_fox_news =  [get_transcripts(video_id) for video_id in video_id_fox_news]
	transcript_cnn =  [get_transcripts(video_id) for video_id in video_id_cnn]
	print("Finish Fetching Transcripts W/ Time Stamp ... ")

	# Fetch Transcripts W/o Time Stamp
	#transcript_fox_news_no_time_stamp =  [get_transcript_text(transcript) for transcript in transcript_fox_news]
	#transcript_cnn_no_time_stamp =  [get_transcript_text(transcript) for transcript in transcript_cnn]
	
	# After this pre-processing phase, we have:
	# Title 
	# Video URL
	# Video ID
	# Transcript w/ Time Stamp	
	# Comments
	# Comments with Replies

	# Moving To JSON
	print("Writing To JSON Files .... ")	
	data_zip_fox_news = list(zip(title_fox_news, video_url_fox_news, transcript_fox_news, comments_fox_news, comments_with_replies_fox_news))
	data_zip_cnn = list(zip(title_cnn, video_url_cnn, transcript_cnn, comments_cnn, comments_with_replies_cnn))
	data_fox_news = write_to_json_batch_with_replies(data_zip_fox_news, "fox_news_data_with_replies_1.json")
	data_cnn = write_to_json_batch_with_replies(data_zip_cnn, "cnn_data_with_replies_1.json")
	print("Finishing Writing To JSON Files .... ")
	


if __name__ == '__main__':
	main()