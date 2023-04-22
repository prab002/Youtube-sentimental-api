from googleapiclient.discovery import build
from nltk.sentiment import SentimentIntensityAnalyzer
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/search', methods=['POST'])
def search_videos():
    try:
        # Set up YouTube API client
        apikey = "AIzaSyDhuQjgP_jjeU_C62sY8dqJgXKzJp1L918"

        youtube = build('youtube', 'v3', developerKey=apikey)

        # Get search query from request
        search_query = request.form['search_query']

        # Call the YouTube API to search for videos based on the user's query
        search_response = youtube.search().list(
            q=search_query,
            type='video',
            part='id,snippet',
            maxResults=10
        ).execute()

        # Extract the video IDs and titles from the search results
        video_ids = [item['id']['videoId'] for item in search_response['items']]
        video_titles = [item['snippet']['title'] for item in search_response['items']]

        # Get the comments and perform sentiment analysis for each video
        analyzer = SentimentIntensityAnalyzer()
        videos = []

        for video_id, video_title in zip(video_ids, video_titles):
            comments = []
            next_page_token = None

            while True:
                response = youtube.commentThreads().list(
                    part='snippet',
                    videoId=video_id,
                    pageToken=next_page_token
                ).execute()

                for item in response['items']:
                    comment = item['snippet']['topLevelComment']['snippet']['textOriginal']
                    comments.append(comment)

                if 'nextPageToken' in response:
                    next_page_token = response['nextPageToken']
                else:
                    break

            # Check if there are comments for this video
            if len(comments) == 0:
                continue

            positive_count = 0
            negative_count = 0
            neutral_count = 0

            for comment in comments:
                scores = analyzer.polarity_scores(comment)
                sentiment = scores['compound']
                if sentiment > 0.5:
                    positive_count += 1
                elif sentiment < -0.5:
                    negative_count += 1
                else:
                    neutral_count += 1

            total_count = len(comments)
            sentiment_score = (positive_count - negative_count) / total_count if total_count > 0 else 0
            video = {
                'title': video_title,
                'id': video_id,
                'total_comments': total_count,
                'positive_comments': positive_count,
                'negative_comments': negative_count,
                'neutral_comments': neutral_count,
                'sentiment_score': sentiment_score
            }
            videos.append(video)

        # Sort the videos based on the sentiment score
        videos = sorted(videos, key=lambda x: x['sentiment_score'], reverse=True)

        # Prepare the response
        response = []
        for video in videos:
            response.append({
                'title': video['title'],
                'video_link': f"https://www.youtube.com/watch?v={video['id']}",
                'total_comments': video['total_comments'],
                'positive_comments': video['positive_comments'],
                'negative_comments': video['negative_comments'],
                'neutral_comments': video['neutral_comments'],
                'sentiment_score': video['sentiment_score']
            })

        return jsonify(response)
    
    except Exception as e:
        return jsonify({'error': str(e)})
        

if __name__ == '__main__':
    app.run(debug=True)
