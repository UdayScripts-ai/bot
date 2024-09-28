import os
import telebot
import requests
from pydub import AudioSegment

# Initialize the bot with your bot token
API_TOKEN = '7866151294:AAFNGkgEmPruHySIcTFg7ZmPSpWNKDLYpjg'  # Set this token in a secure manner for production use
bot = telebot.TeleBot(API_TOKEN)

# Define the API URL
JIO_SAAVAN_API_URL = 'https://jiosaavan-seven.vercel.app/song/?query='

# Ensure the songs folder exists
if not os.path.exists('songs'):
    os.makedirs('songs')

# Function to fetch song data from the API
def get_song_info(query):
    try:
        response = requests.get(JIO_SAAVAN_API_URL + query)
        data = response.json()
        if data:
            song = data[0]
            song_name = song.get('song', 'Unknown Song')
            album = song.get('album', 'Unknown Album')
            singers = song.get('singers', 'Unknown Singers')
            media_url = song.get('media_url', None)
            image_url = song.get('image', None)
            return song_name, album, singers, media_url, image_url
        else:
            return None
    except Exception as e:
        print(f"Error fetching song: {e}")
        return None

# Convert m4a to mp3
def convert_m4a_to_mp3(m4a_path, mp3_path):
    try:
        audio = AudioSegment.from_file(m4a_path, format="m4a")
        audio.export(mp3_path, format="mp3")
        return True
    except Exception as e:
        print(f"Error converting file: {e}")
        return False

# Command handler for /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome! Send me the name of the song you want to download from Jio Saavn.")

# Message handler to search for and send the song
@bot.message_handler(func=lambda message: True)
def send_song(message):
    query = message.text
    song_info = get_song_info(query)

    if song_info:
        song_name, album, singers, media_url, image_url = song_info
        sanitized_song_name = "".join([c for c in song_name if c.isalnum() or c in (' ', '_')]).rstrip()
        mp3_file_path = f"songs/{sanitized_song_name}.mp3"

        response_message = f"🎵 *Song:* {song_name}\n\n💽 *Album:* {album}\n\n🎤 *Singers:* {singers}\n"

        # Check if the song is already downloaded
        if os.path.exists(mp3_file_path):
            bot.reply_to(message, f"{song_name} found in storage, sending now...")

            # Send the existing mp3 file
            with open(mp3_file_path, 'rb') as audio:
                bot.send_audio(message.chat.id, audio, caption=response_message, parse_mode="Markdown")
        else:
            if media_url:
                # Send a message indicating the download has started
                bot.reply_to(message, f"Downloading {song_name}...")

                # Download the m4a file
                m4a_file_path = f"{sanitized_song_name}.m4a"
                r = requests.get(media_url)

                # Save the m4a file locally
                with open(m4a_file_path, 'wb') as f:
                    f.write(r.content)

                # Convert m4a to mp3
                if convert_m4a_to_mp3(m4a_file_path, mp3_file_path):
                    # Send the converted mp3 file
                    with open(mp3_file_path, 'rb') as audio:
                        bot.send_audio(message.chat.id, audio, caption=response_message, parse_mode="Markdown")

                    # Clean up the m4a file after conversion
                    os.remove(m4a_file_path)
                else:
                    bot.reply_to(message, "Sorry, there was an issue converting the song to MP3.")
            else:
                bot.reply_to(message, "Sorry, this song is not available for download.")

        if image_url:
            bot.send_photo(message.chat.id, image_url)
    else:
        bot.reply_to(message, "Sorry, I couldn't find the song. Please try a different query.")

# Polling to keep the bot running and check for updates
if __name__ == "__main__":
    bot.infinity_polling()
