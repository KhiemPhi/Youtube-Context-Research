from apiclient.discovery import build
from datetime import datetime
import io
import pickle

from googleapiclient.http import MediaIoBaseDownload
from youtube_transcript_api import YouTubeTranscriptApi

api_key = ""
youtube = build("youtube" , "v3" , developerKey=api_key)
channel_id = "UCupvZG-5ko_eiXAupbDfxWw" #CNN

def print_title_from_search_results_video(res):
	for item in res['items']:
		print(item['snippet']['title'])

def print_channel_data(res):
	for item in res['items']:
		print(item['snippet'])

def search_videos(query):
	req = youtube.search().list(q=query, part='snippet' , type='video' , maxResults=5) # Max 5 results, highest is 50 results, Searching for videos
	res = req.execute() #JSON Format
	return res

def search_channels(query):
	req = youtube.search().list(q=query, part='snippet' , type='channel' , maxResults=5) # Max 5 results, highest is 50 results, Searching for videos
	res = req.execute() #JSON Format
	return res

def search_videos_by_dates(query, start_date, end_date):
	req = youtube.search().list(q=query, part='snippet' , type='video' , publishedAfter=start_date , publishedBefore=end_date, maxResults=5) # Max 5 results, highest is 50 results, Searching for videos
	res = req.execute() #JSON Format
	return res

def fetch_all_videos_by_channel(channel_id):
	res = youtube.channels().list(id=channel_id , part='contentDetails').execute()
	uploads_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads'] # Get uploaded playlist ids
	 
	videos = []
	next_page_token = None
	pages = 6 # Two Pages
	i = 0

	while i < pages:
		res = youtube.playlistItems().list(playlistId = uploads_id, part="snippet" , maxResults=5 , pageToken = next_page_token).execute()
		videos += res['items']
		next_page_token = res['nextPageToken']

		if next_page_token is None:
			break

		i += 1	

	return videos # return list of videos

def print_title_from_videos_json(video):
	print(video['snippet']['title'])

def get_comment(video_id , next_page_token):
	try:
		if(next_page_token is not None):
			comment_results = youtube.commentThreads().list(videoId=video_id , part="snippet" , maxResults=50, nextPageToken=next_page_token).execute()
		else:
			comment_results = youtube.commentThreads().list(videoId=video_id , part="snippet" , maxResults=50).execute()
		return comment_results
	except:
		return None


def get_comments_by_video_id(video_id):	
	comments = []
	next_page_token = None
	pages = 2 # Two Pages
	i = 0

	while i < pages:
		comment_results = get_comment(video_id, next_page_token)
		if (comment_results is not None):			
			comments.extend([item['snippet']['topLevelComment']['snippet']['textOriginal'] for item in comment_results['items']])

			next_page_token = comment_results.get('nextPageToken')

		else:
			break

		i+= 1

	return comments 

def get_channel_id(channel_res):
	return channel_res['snippet']['channelId']

def get_video_id(video_res):
	return video_res['snippet']['resourceId']['videoId']

def filter_based_on_keywords(title, keywords):
	return any(word in title for word in keywords)

def get_transcripts(video_id):
	try:
		transcript = YouTubeTranscriptApi.get_transcript(video_id)
		return transcript
	except:
		return None

def get_transcript_text(transcript):
	return [x['text'] for x in transcript]


def main():
	
	# Basic Demo To Make Simple Search Queries
	#res_vids = search_videos('avengers')
	#print_title_from_search_results_video(res_vids)	
	
	'''
	# Search by Restricted Series of Dates
	start_date = datetime(year=2016, month=12 , day = 1).strftime('%Y-%m-%dT%H:%M:%SZ')
	end_date = datetime(year=2017, month=2 , day = 1).strftime('%Y-%m-%dT%H:%M:%SZ')
	res_travel_ban = search_videos_by_dates('trump travel ban', start_date , end_date)
	print_title_from_search_results_video(res_travel_ban) # Print Video Titles Based On Topic, Can Increase Query or Make Channel Specific	
	
	# Getting All The Videos Of A Channel
	# Fetching from Upload Playlist : Get Details of Channel, Call Operation Over Playlist Item
	res_CNN = fetch_all_videos_by_channel(channel_id) 

	# Getting the comments on a video
	video_1_CNN_id = res_CNN[0]['snippet']['resourceId']['videoId'] 
	video_1_CNN_title = res_CNN[0]['snippet']['title']
	comments = get_comments_by_video_id(video_1_CNN_id)


	# Getting the captions on a video  (Hillbilly HotDogs Example)
	transcript = YouTubeTranscriptApi.get_transcript("KySLSYSTbcE")
	transcript_text = [x['text'] for x in transcript]
	print(transcript_text)
	'''

	# 10 Videos Per 2 Channels, 100 Comments / video , Transcripts For Each Video 
	# Fox News + CNN 
	# Transcript - Time stamp + language at time 

	res_channels_fox_news = search_channels('fox news')
	res_channels_CNN = search_channels('CNN')
	
	fox_news_channel_id = get_channel_id(res_channels_fox_news['items'][0])
	CNN_channel_id = get_channel_id(res_channels_CNN['items'][0])

	videos_fox_news = fetch_all_videos_by_channel(fox_news_channel_id)
	videos_CNN = fetch_all_videos_by_channel(CNN_channel_id)

	title_fox_news = [ video['snippet']['title'] for video in videos_fox_news]
	title_CNN = [ video['snippet']['title'] for video in videos_CNN]

	video_id_fox_news = [ get_video_id(video) for video in videos_fox_news]
	video_id_CNN      = [ get_video_id(video) for video in videos_CNN]

	title_to_id_dict_fox_news = dict(zip(title_fox_news , video_id_fox_news))
	title_to_id_dict_CNN = dict(zip(title_CNN, video_id_CNN))


	#Filter out based on keywords
	# Keywords: riot , george floyd, riot, protest, crowd, police, black people, officer, police
	keywords = ["riot", "george floyd", "protest", "crowd", "police", "black people", "officer", "police", "violent"]
	keywords_dict_fox_news = dict(filter(lambda x: filter_based_on_keywords(x[0], keywords)    , title_to_id_dict_fox_news.items()))
	keywords_dict_CNN = dict(filter(lambda x: filter_based_on_keywords(x[0], keywords)    , title_to_id_dict_CNN.items()))
	
	#With the proper keywords filter out -> go directly to transcript + comments
	transcript_fox_news = list(map(lambda x: get_transcripts(x[1])  , keywords_dict_fox_news.items()))
	transcript_CNN = list(map(lambda x: get_transcripts(x[1])  , keywords_dict_CNN.items()))

	#Creating title to transcript dict
	title_to_transcript_fox_news =  dict(zip(title_fox_news , transcript_fox_news)) 
	title_to_transcript_CNN      =  dict(zip(title_CNN, transcript_CNN))

	#Filter out None:
	title_to_transcript_fox_news = dict(filter(lambda x: x[1] is not None ,  title_to_transcript_fox_news.items()))
	title_to_transcript_CNN = dict(filter(lambda x: x[1] is not None ,  title_to_transcript_CNN.items()))

	#Text For Banerjee Ease of Access
	transcript_fox_news_text = list(map(lambda x: get_transcript_text(x[1])  ,   title_to_transcript_fox_news.items()))
	transcript_CNN_text      = list(map(lambda x: get_transcript_text(x[1]) , title_to_transcript_CNN.items()))
	title_to_transcript_fox_news_text = dict(zip(title_fox_news , transcript_fox_news_text))
	title_to_transcript_CNN_text     = dict(zip(title_CNN , transcript_CNN_text))

	#Pkl Pure Text
	pkl_title_to_text_fox_news = open("title_to_text_fox_news.pkl","wb")
	pickle.dump(title_to_transcript_fox_news_text , pkl_title_to_text_fox_news)
	pkl_title_to_text_fox_news.close()

	pkl_title_to_text_CNN = open("title_to_text_CNN.pkl","wb")
	pickle.dump(title_to_transcript_CNN_text , pkl_title_to_text_CNN)
	pkl_title_to_text_CNN.close()

	#Pkl Text With Time Stamps
	pkl_title_to_transcript_fox_news = open("title_to_transcript_fox_news.pkl","wb")
	pickle.dump(title_to_transcript_fox_news , pkl_title_to_transcript_fox_news)
	pkl_title_to_transcript_fox_news.close()

	pkl_title_to_transcript_CNN = open("title_to_transcript_CNN.pkl","wb")
	pickle.dump(title_to_transcript_CNN , pkl_title_to_transcript_CNN)
	pkl_title_to_transcript_CNN.close()

	#Getting The Comments
	fox_news_comments =  [get_comments_by_video_id(video_id) for video_id in video_id_fox_news]
	CNN_comments = [get_comments_by_video_id(video_id)  for video_id in video_id_CNN]

	#Zip Into Dict
	title_to_comments_fox_news = dict(zip(title_fox_news , fox_news_comments))
	title_to_comments_CNN = dict(zip(title_CNN , CNN_comments))

	#Pkl title_to_comment Dict
	pkl_title_to_comments_fox_news = open("title_to_comments_fox_news.pkl" , "wb")
	pickle.dump(title_to_comments_fox_news , pkl_title_to_comments_fox_news)
	pkl_title_to_comments_fox_news.close()

	pkl_title_to_comments_CNN = open("title_to_comments_CNN.pkl" , "wb")
	pickle.dump(title_to_comments_CNN , pkl_title_to_comments_CNN)
	pkl_title_to_comments_CNN.close()






if __name__ == "__main__":
    main()