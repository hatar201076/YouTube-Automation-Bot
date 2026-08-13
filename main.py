import sys
sys.dont_write_bytecode = True
import json
import os
from lib.content_handler import search_and_download_meditation_video, search_and_download_music, load_used_content, save_used_content
from lib.video_processing import combine_audio_video
from lib.youtube_upload import upload_to_youtube, refresh_token
from lib.metadata import generate_metadata
from lib.config import load_config

def main():
    used_content = load_used_content()

    # --- MODE 1: OTO-MODE VIA FILE auto.json (--auto) ---
    if '--auto' in sys.argv:
        with open('auto.json', 'r') as f:
            config = json.load(f)

        video_created = False 

        while config['videos'] and not video_created:
            video_config = config['videos'].pop(0)
            video_query = video_config['video_query']
            audio_query = video_config['audio_query']
            should_upload_to_youtube = video_config['upload_to_youtube']
            video_type = video_config['video_type']
            duration_minutes = video_config['duration_minutes']

            is_short = video_type == 'short'

            video_url = search_and_download_meditation_video(used_content['videos'], video_query)
            if not video_url:
                print(f"Retrying with next config: Could not find a video for '{video_query}'")
                continue  

            used_content['videos'].append(video_url)

            audio_url, attribution_text = search_and_download_music(audio_query, used_content['audios'])
            if not audio_url:
                print(f"Retrying with next config: Could not find audio for '{audio_query}'")
                continue  

            used_content['audios'].append(audio_url)

            save_used_content(used_content)

            metadata = generate_metadata(video_query, duration_minutes, attribution=attribution_text, is_short=is_short)
            combine_audio_video("video.mp4", "music.mp3", "final_video.mp4", duration_minutes=duration_minutes, is_short=is_short)

            if should_upload_to_youtube:
                refresh_token()
                upload_to_youtube("final_video.mp4", metadata, is_short=is_short)

            with open('auto.json', 'w') as f:
                json.dump(config, f, indent=4)

            print(f"Successfully processed and uploaded video for query: '{video_query}'")
            video_created = True

        else:
            if not video_created:
                print("All video configurations have been processed or none were successful.")

    # --- MODE 2: MODE NON-INTERAKTIF UNTUK RAILWAY (Membaca dari Environment Variables) ---
    else:
        print("Running in automated cloud mode (Railway/Non-interactive)...")
        
        # 1. Ambil variabel dari Environment Variable Railway (atau gunakan default)
        video_type = os.getenv("VIDEO_TYPE", "short").lower()
        
        try:
            duration_minutes = float(os.getenv("VIDEO_DURATION", "1.0"))
        except ValueError:
            duration_minutes = 1.0

        video_query = os.getenv("VIDEO_QUERY", "nature meditation")
        audio_query = os.getenv("AUDIO_QUERY", "relaxing rain")
        upload_choice = os.getenv("UPLOAD_YOUTUBE", "yes").lower()

        is_short = (video_type == 'short')

        print(f"Config: Type={video_type}, Duration={duration_minutes}m, Video Query='{video_query}', Audio Query='{audio_query}'")

        # 2. Download Video
        video_url = search_and_download_meditation_video(used_content['videos'], video_query)
        if video_url:
            used_content['videos'].append(video_url)
        else:
            print(f"Warning: Could not download video for query '{video_query}'")

        # 3. Download Audio
        audio_url, attribution_text = search_and_download_music(audio_query, used_content['audios'])
        if audio_url:
            used_content['audios'].append(audio_url)
        else:
            print(f"Warning: Could not download audio for query '{audio_query}'")

        # 4. Simpan history konten terpakai
        save_used_content(used_content)

        # 5. Generate Metadata & Proses Penggabungan Video
        metadata = generate_metadata(video_query, duration_minutes, attribution=attribution_text, is_short=is_short)
        combine_audio_video("video.mp4", "music.mp3", "final_video.mp4", duration_minutes=duration_minutes, is_short=is_short)

        # 6. Upload ke YouTube jika diizinkan
        if upload_choice in ['yes', 'true', '1']:
            print("Uploading final video to YouTube...")
            refresh_token()
            upload_to_youtube("final_video.mp4", metadata, is_short=is_short)
            print("Upload completed!")
        else:
            print("Skipping YouTube upload based on configuration.")

if __name__ == "__main__":
    main()
