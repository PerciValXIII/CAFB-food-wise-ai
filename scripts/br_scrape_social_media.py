import tweepy
import os
import json
import requests
import time 
import yt_dlp
from PIL import Image
from io import BytesIO
from selenium import webdriver
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from pytube import YouTube
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ScrapeX_tweepy:
    def __init__(self, username, api_key, api_secret_key, access_token, access_token_secret, max_tweets=100):
        """Initialize ScrapeX with Twitter API credentials and settings."""
        self.username = username
        self.max_tweets = max_tweets

        # Authenticate with Twitter API
        auth = tweepy.OAuth1UserHandler(api_key, api_secret_key, access_token, access_token_secret)
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "twitter_posts.jsonl")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")

        # Ensure directories exist
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)

    def download_media(self, url, save_path, prefix="media"):
        """Downloads an image or video from a URL and saves it."""
        try:
            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                filename = f"{prefix}_{os.path.basename(url.split('?')[0])}"  # Remove query params
                filepath = os.path.join(save_path, filename)

                # Detect file type (image or video)
                if "video" in url or "mp4" in url:
                    with open(filepath, "wb") as file:
                        file.write(response.content)
                    print(f"Downloaded Video: {filename}")
                else:
                    image = Image.open(BytesIO(response.content))
                    image.save(filepath)
                    print(f"Downloaded Image: {filename}")

                return filename
        except Exception as e:
            print(f"Failed to download {url}: {e}")
        return None

    def scrape_twitter(self):
        """Fetch tweets, extract media, and save data to JSONL."""
        print(f"Scraping tweets from @{self.username}...")

        try:
            tweets = self.api.user_timeline(screen_name=self.username, count=self.max_tweets, tweet_mode="extended")
        except tweepy.TweepyException as e:
            print(f"Error fetching tweets: {e}")
            return

        tweet_data = []
        for tweet in tweets:
            tweet_info = {
                "tweet_id": tweet.id_str,
                "created_at": str(tweet.created_at),
                "text": tweet.full_text,
                "media_files": []
            }

            # Check if tweet contains media
            if "media" in tweet.entities:
                for media in tweet.entities["media"]:
                    media_url = media["media_url_https"]
                    media_type = media["type"]  # Can be "photo" or "video"

                    # Download the media file
                    save_path = self.IMAGE_SAVE_PATH if media_type == "photo" else self.VIDEO_SAVE_PATH
                    filename = self.download_media(media_url, save_path)

                    if filename:
                        tweet_info["media_files"].append(filename)

            # Save tweet data
            tweet_data.append(tweet_info)

            # Save after every 10 tweets
            if len(tweet_data) % 10 == 0:
                print(f"Saving {len(tweet_data)} tweets so far...")
                self.save_to_jsonl(tweet_data, self.TEXT_SAVE_PATH)

        # Final save
        print(f"Finished scraping. Saving {len(tweet_data)} tweets.")
        self.save_to_jsonl(tweet_data, self.TEXT_SAVE_PATH)

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"Saved {len(data)} records to {file_path}")


class ScrapeTwitterSelenium:
    def __init__(self, username, max_tweets=10000, cookies_file="cookies/x_cookies.json"):
        """Initialize ScrapeTwitterSelenium with Twitter handle and scraping settings."""
        self.username = username
        self.max_tweets = max_tweets
        self.cookies_file = cookies_file

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "twitter_posts.jsonl")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")

        # Ensure directories exist
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)

        # # Configure Selenium WebDriver
        # chrome_options = Options()
        # chrome_options.add_argument("--headless=new")  # Keeps headless mode enabled
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Prevent detection
        # chrome_options.add_argument("--no-sandbox")
        # chrome_options.add_argument("--disable-dev-shm-usage")
        # chrome_options.add_argument("--disable-gpu")
        # chrome_options.add_argument("--window-size=1920x1080")
        # chrome_options.add_argument("--use-gl=desktop")  # Force GPU acceleration


        # # Spoof a real browser user agent
        # chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")

        # # **Add these settings to bypass detection**
        # chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Bypass bot detection
        # chrome_options.add_argument("--disable-infobars")  # Remove automation alert
        # chrome_options.add_argument("--disable-popup-blocking")  # Allow popups
        # chrome_options.add_argument("--ignore-certificate-errors")  # Ignore SSL issues
        # chrome_options.add_argument("--allow-running-insecure-content")  # Allow mixed content
        # chrome_options.add_argument("--enable-features=NetworkService,NetworkServiceInProcess")  # Enable network optimizations
        
        # # **Set a Realistic User-Agent**
        # chrome_options.add_argument(
        #     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        # )

        # chrome_options.add_experimental_option(
        #     "prefs",
        #         {
        #             "profile.managed_default_content_settings.fonts": 2,  # Disable fonts
        #             "profile.managed_default_content_settings.stylesheets": 2,  # Disable CSS
        #             "profile.managed_default_content_settings.plugins": 2,  # Disable plugins
        #             "profile.managed_default_content_settings.popups": 2,  # Disable popups
        #             "profile.managed_default_content_settings.geolocation": 2,  # Disable location tracking
        #             "profile.default_content_setting_values.notifications": 2,  # Disable notifications
        #         },
        # )


        # # **Run in visible mode for debugging**
        # # Remove headless mode for testing, then re-enable once working
        # # chrome_options.add_argument("--headless=new")  # Comment this out for debugging

        # chromedriver_path = "/opt/homebrew/bin/chromedriver"  # Adjust path if needed
        # service = Service(chromedriver_path)
        # self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # # **Remove Automation Flags**
        # self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        # Configure Selenium WebDriver
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920x1080")

        # FIX: Use a temporary Chrome profile to avoid "already in use" error
        chrome_options.add_argument(f"--user-data-dir=/tmp/chrome_user_{os.getpid()}")

        # USE YOUR REAL CHROME PROFILE (Ensure you're logged in to X)
        # chrome_options.add_argument("--user-data-dir=/Users/coleloughbc/Library/Application Support/Google/Chrome")  # Mac
        # chrome_options.add_argument("--profile-directory=Default")  # Use Default Profile
        # chrome_options.add_argument(r"--user-data-dir=C:\Users\YOUR_USERNAME\AppData\Local\Google\Chrome\User Data")  # Windows

        # USE YOUR REAL CHROME BROWSER
        chrome_options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"  # Mac
        # chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"  # Windows

        # REMOVE SELENIUM DETECTION
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option("useAutomationExtension", False)

        # REMOVE HEADLESS MODE (Make Chrome Visible)
        # REMOVE: chrome_options.add_argument("--headless=new")

        # Start WebDriver
        chromedriver_path = "/opt/homebrew/bin/chromedriver"  # Adjust for Mac/Linux
        # chromedriver_path = "C:\\path\\to\\chromedriver.exe"  # Windows
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove Automation Flag (Makes bot detection harder)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")


        # Wait to ensure Chrome loads properly
        time.sleep(5)

        # Open Twitter (X)
        self.driver.get("https://x.com/foodbankmetrodc")

        # Load Cookies
        self.load_cookies()

    def load_cookies(self):
        """Loads stored Facebook cookies into Selenium."""
        self.driver.get("https://www.x.com/")  # Open Facebook login page
        time.sleep(5)  # Wait for page to load

        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                # Add each cookie to the browser
                for cookie in cookies:
                    cookie_dict = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"],
                        "secure": cookie.get("secure", False),
                        "httpOnly": cookie.get("httpOnly", False),
                    }
                    self.driver.add_cookie(cookie_dict)

                print(f"[INFO] Loaded {len(cookies)} cookies from {self.cookies_file}")
                self.driver.refresh()  # Refresh to apply cookies
                time.sleep(5)  # Allow time for authentication
            except Exception as e:
                print(f"[ERROR] Failed to load cookies: {e}")
        else:
            print(f"[WARNING] No cookie file found. Login may be required.")



    def scrape_twitter(self):
        """Fetch tweets, extract media, and save data to JSONL."""
        print(f"[INFO] Scraping tweets from @{self.username}...")

        # Open Twitter profile
        self.driver.get(f"https://x.com/{self.username}")  # Use X.com instead of Twitter.com
        # Wait up to 15 seconds for tweets to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']"))
            )
            print("[INFO] Twitter page loaded successfully.")
        except TimeoutException:
            print("[WARNING] Initial tweets did not load. Retrying...")
            time.sleep(10)  # Give it more time
            self.driver.save_screenshot("twitter_debug_1.png")
            self.driver.refresh()
            time.sleep(10)  # Another wait after refresh
            self.driver.save_screenshot("twitter_debug_2.png")

            # Try again
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "article[data-testid='tweet']"))
                )
                print("[INFO] Tweets loaded after retry.")
            except TimeoutException:
                print("[ERROR] Tweets still not loaded. Twitter/X may have changed its structure.")
                self.driver.quit()
                return

        # Take a debug screenshot
        self.driver.save_screenshot("twitter_debug_3.png")
        print("[DEBUG] Screenshot saved as 'debug_twitter.png'")

        # Wait for tweets to load
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "article"))
            )
            print("[INFO] Twitter page loaded successfully.")
        except TimeoutException:
            print("[ERROR] Tweets did not load. Twitter/X may have changed its structure.")
            self.driver.save_screenshot("twitter_debug_4.png")
            print("[DEBUG] Screenshot saved as 'twitter_debug.png'")
            self.driver.quit()
            return


        tweet_data = []
        tweet_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        seen_tweets = set()  # To track duplicate tweets

        while tweet_count < self.max_tweets:
            print(f"[INFO] Scanning for tweets... (current count: {tweet_count})")

            # Try finding tweets
            tweets = self.driver.find_elements(By.CSS_SELECTOR, "article")

            if not tweets:
                print("[WARNING] No tweets found. Retrying after scroll.")
                time.sleep(2)
                continue

            for tweet in tweets:
                if tweet_count >= self.max_tweets:
                    break  # Stop when max tweets reached

                # Extract tweet text
                try:
                    tweet_text = tweet.find_element(By.CSS_SELECTOR, "div[lang]").text.strip()
                except NoSuchElementException:
                    print("[WARNING] No tweet text found.")
                    continue


                tweet_id = tweet.get_attribute("data-tweet-id")  # Get tweet ID
                if not tweet_text or tweet_id in seen_tweets:
                    continue  # Skip empty or duplicate tweets
                seen_tweets.add(tweet_id)


                seen_tweets.add(tweet_text)  # Track tweet to prevent duplicates

                # Extract media links
                media_files = []
                try:
                    media_elements = tweet.find_elements(By.CSS_SELECTOR, "img[src^='https://pbs.twimg.com/media/'], video source")
                    for media in media_elements:
                        media_url = media.get_attribute("src")
                        if media_url:
                            media_type = "photo" if "twimg" in media_url else "video"
                            save_path = self.IMAGE_SAVE_PATH if media_type == "photo" else self.VIDEO_SAVE_PATH
                            filename = self.download_media(media_url, save_path)
                            if filename:
                                media_files.append(filename)
                except Exception as e:
                    print(f"[WARNING] Error extracting media: {e}")

                # Save tweet info
                tweet_data.append({
                    "tweet_id": f"{self.username}_{tweet_count}",
                    "text": tweet_text,
                    "media_files": media_files
                })
                tweet_count += 1

            # Scroll down and wait for more tweets to load
            print("[INFO] Scrolling for more tweets...")
            self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
            time.sleep(3)  # Increase wait time to let tweets load


            # Break if no new tweets are loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] No new tweets loaded. Stopping scrape.")
                break
            last_height = new_height

        print(f"[INFO] Finished scraping {tweet_count} tweets. Saving data...")
        self.save_to_jsonl(tweet_data, self.TEXT_SAVE_PATH)

        # Close WebDriver
        self.driver.quit()

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Saved {len(data)} records to {file_path}")


import os
import json
import requests
from facebook_scraper import get_posts, set_cookies
from PIL import Image
from io import BytesIO

class ScrapeFacebook:
    def __init__(self, page_id="145563868868546", max_pages=10, cookies_file="cookies/facebook_cookies.json"):
        """Initialize ScrapeFacebook with a Facebook page name and scraping settings."""
        self.page_id = page_id
        self.max_pages = max_pages
        self.cookies_file = cookies_file

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "facebook_posts.jsonl")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.TEXT_SAVE_PATH), exist_ok=True)
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)

        print(f"[INFO] ScrapeFacebook initialized for page: {self.page_id}")

        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                # Convert list of dicts into a {name: value} dictionary
                formatted_cookies = {cookie["name"]: cookie["value"] for cookie in cookies}

                print(f"[DEBUG] Cookies Loaded: {formatted_cookies}")  # <-- Add this line

                set_cookies(formatted_cookies)
                print(f"[INFO] Using session cookies from {self.cookies_file}")
            except Exception as e:
                print(f"[ERROR] Failed to load cookies: {e}")
        else:
            print(f"[WARNING] No cookie file found! Scraper may fail on private pages.")


    def download_media(self, url, save_path, prefix="fb_media"):
        """Downloads an image or video from a URL and saves it."""
        if not url:
            print(f"[WARNING] No media URL provided. Skipping download.")
            return None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers, timeout=10)
            if response.status_code == 200:
                filename = f"{prefix}_{os.path.basename(url.split('?')[0])}"
                filepath = os.path.join(save_path, filename)

                # Detect file type (image or video)
                if url.endswith(".mp4"):
                    with open(filepath, "wb") as file:
                        file.write(response.content)
                    print(f"[INFO] Downloaded Video: {filename}")
                else:
                    image = Image.open(BytesIO(response.content))
                    image.save(filepath)
                    print(f"[INFO] Downloaded Image: {filename}")

                return filename
            else:
                print(f"[ERROR] Failed to download media: {url} - HTTP {response.status_code}")
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
        return None

    def scrape_facebook(self):
        """Fetch posts, extract media, and save data to JSONL."""
        print(f"[INFO] Scraping posts from Facebook page: {self.page_id}...")
        post_data = []
        post_count = 0

        try:
            print(f"[DEBUG] Fetching posts for {self.page_id}...")
            posts = list(get_posts(self.page_id, pages=self.max_pages, options={"progress": True, "allow_extra_requests": True}))
            print(f"[INFO] Retrieved {len(posts)} posts.")
        except Exception as e:
            print(f"[ERROR] Failed to retrieve posts: {e}")
            return

        if not posts:
            print(f"[WARNING] No posts found for {self.page_id}. Check if the page is public or requires login.")
            return

        for post in posts:
            post_text = post.get("post_text", "").strip()
            post_images = post.get("images", [])
            post_video = post.get("video", "")
            post_url = post.get("post_url", "")

            # Log each post's details
            print(f"[DEBUG] Processing post {post_count}: {post_text[:50]}... (URL: {post_url})")

            # Download images and videos
            image_files = [self.download_media(img, self.IMAGE_SAVE_PATH, "fb_img") for img in post_images if img]
            video_file = self.download_media(post_video, self.VIDEO_SAVE_PATH, "fb_vid") if post_video else None

            post_entry = {
                "post_id": f"{self.page_id}_{post_count}",
                "text": post_text,
                "images": [img for img in image_files if img],
                "video": video_file if video_file else None,
                "post_url": post_url
            }
            post_data.append(post_entry)
            post_count += 1

            # Save after every 5 posts
            if len(post_data) % 5 == 0:
                print(f"[INFO] Saving {len(post_data)} posts so far...")
                self.save_to_jsonl(post_data, self.TEXT_SAVE_PATH)

        # Final save
        print(f"[INFO] Finished scraping {post_count} posts. Saving data...")
        self.save_to_jsonl(post_data, self.TEXT_SAVE_PATH)

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                for entry in data:
                    file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            print(f"[INFO] Saved {len(data)} records to {file_path}")
        except Exception as e:
            print(f"[ERROR] Failed to save data: {e}")


class ScrapeFacebookSelenium:
    def __init__(self, page_url="https://www.facebook.com/CapitalAreaFoodBank", max_posts=20, cookies_file="cookies/facebook_cookies.json"):
        """Initialize Selenium scraper for Facebook with stored cookies."""
        self.page_url = page_url
        self.max_posts = max_posts
        self.cookies_file = cookies_file

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "facebook_posts.jsonl")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.TEXT_SAVE_PATH), exist_ok=True)
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)

        print(f"[INFO] ScrapeFacebookSelenium initialized for page: {self.page_url}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Maximize window
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # Use a different user-data-dir to avoid profile conflicts
        chrome_options.add_argument("--user-data-dir=" + os.path.expanduser("~/Library/Application Support/Google/Chrome/SeleniumProfile"))

        # Set Chrome Driver Path (Adjust path if necessary)
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load Cookies
        self.load_cookies()

    def load_cookies(self):
        """Loads stored Facebook cookies into Selenium."""
        self.driver.get("https://www.facebook.com/")  # Open Facebook login page
        time.sleep(5)  # Wait for page to load

        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                # Add each cookie to the browser
                for cookie in cookies:
                    cookie_dict = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"],
                        "secure": cookie.get("secure", False),
                        "httpOnly": cookie.get("httpOnly", False),
                    }
                    self.driver.add_cookie(cookie_dict)

                print(f"[INFO] Loaded {len(cookies)} cookies from {self.cookies_file}")
                self.driver.refresh()  # Refresh to apply cookies
                time.sleep(5)  # Allow time for authentication
            except Exception as e:
                print(f"[ERROR] Failed to load cookies: {e}")
        else:
            print(f"[WARNING] No cookie file found. Login may be required.")

    def scrape_facebook(self):
        """Scrape posts from Facebook page using Selenium."""
        print(f"[INFO] Scraping posts from Facebook page: {self.page_url}")
        self.driver.get(self.page_url)
        time.sleep(5)

        post_data = []
        post_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while post_count < self.max_posts:
            print(f"[INFO] Scanning for posts... (current count: {post_count})")

            # Find posts on the page
            posts = self.driver.find_elements(By.XPATH, "//div[@role='article']")
            if not posts:
                print("[WARNING] No posts found. Retrying after scroll.")
                time.sleep(2)
                continue

            for post in posts:
                if post_count >= self.max_posts:
                    break  # Stop when max posts reached

                # Extract post text
                try:
                    post_text = post.find_element(By.XPATH, ".//div[contains(@class, 'ecm0bbzt')]").text.strip()
                except:
                    post_text = ""

                # Extract media links
                image_files = []
                try:
                    media_elements = post.find_elements(By.XPATH, ".//img")
                    for media in media_elements:
                        media_url = media.get_attribute("src")
                        if media_url:
                            filename = self.download_media(media_url, self.IMAGE_SAVE_PATH, "fb_img")
                            if filename:
                                image_files.append(filename)
                except Exception as e:
                    print(f"[WARNING] Error extracting media: {e}")

                # Save post info
                post_entry = {
                    "post_id": f"{self.page_url}_{post_count}",
                    "text": post_text,
                    "images": image_files,
                }
                post_data.append(post_entry)
                post_count += 1

            # Scroll down and wait for more posts to load
            print("[INFO] Scrolling for more posts...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Break if no new posts are loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] No new posts loaded. Stopping scrape.")
                break
            last_height = new_height

        print(f"[INFO] Finished scraping {post_count} posts. Saving data...")
        self.save_to_jsonl(post_data, self.TEXT_SAVE_PATH)

        # Close WebDriver
        self.driver.quit()

    def download_media(self, url, save_path, prefix="fb_media"):
        """Downloads an image or video from a URL and saves it."""
        if not url:
            return None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers, timeout=10)
            if response.status_code == 200:
                filename = f"{prefix}_{os.path.basename(url.split('?')[0])}"
                filepath = os.path.join(save_path, filename)

                image = Image.open(BytesIO(response.content))
                image.save(filepath)
                return filename
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
        return None

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Saved {len(data)} records to {file_path}")


class ScrapeInstagramSelenium:
    def __init__(self, page_url="https://www.instagram.com/capitalareafoodbank/", max_posts=20, cookies_file="cookies/instagram_cookies.json"):
        """Initialize Selenium scraper for Instagram with stored cookies."""
        self.page_url = page_url
        self.max_posts = max_posts
        self.cookies_file = cookies_file

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "instagram_posts.jsonl")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.TEXT_SAVE_PATH), exist_ok=True)
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)

        print(f"[INFO] ScrapeInstagramSelenium initialized for page: {self.page_url}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Maximize window
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # Use a different user-data-dir to avoid profile conflicts
        chrome_options.add_argument("--user-data-dir=" + os.path.expanduser("~/Library/Application Support/Google/Chrome/SeleniumProfile"))

        # Set Chrome Driver Path (Adjust path if necessary)
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load Cookies
        self.load_cookies()

    def load_cookies(self):
        """Loads stored Instagram cookies into Selenium."""
        self.driver.get("https://www.instagram.com/")  # Open Instagram login page
        time.sleep(5)  # Wait for page to load

        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                # Add each cookie to the browser
                for cookie in cookies:
                    cookie_dict = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"],
                        "secure": cookie.get("secure", False),
                        "httpOnly": cookie.get("httpOnly", False),
                    }
                    self.driver.add_cookie(cookie_dict)

                print(f"[INFO] Loaded {len(cookies)} cookies from {self.cookies_file}")
                self.driver.refresh()  # Refresh to apply cookies
                time.sleep(5)  # Allow time for authentication
            except Exception as e:
                print(f"[ERROR] Failed to load cookies: {e}")
        else:
            print(f"[WARNING] No cookie file found. Login may be required.")

    def scrape_instagram(self):
        """Scrape posts from Instagram page using Selenium."""
        print(f"[INFO] Scraping posts from Instagram page: {self.page_url}")
        self.driver.get(self.page_url)
        time.sleep(5)

        post_data = []
        post_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while post_count < self.max_posts:
            print(f"[INFO] Scanning for posts... (current count: {post_count})")

            # Find posts on the page
            posts = self.driver.find_elements(By.XPATH, "//article//a[contains(@href, '/p/')]")
            if not posts:
                print("[WARNING] No posts found. Retrying after scroll.")
                time.sleep(2)
                continue

            for post in posts:
                if post_count >= self.max_posts:
                    break  # Stop when max posts reached

                # Click on the post to open it
                post.click()
                time.sleep(3)

                # Extract post text
                try:
                    post_text = self.driver.find_element(By.XPATH, "//div[@role='dialog']//div[@class='C4VMK']//span").text.strip()
                except:
                    post_text = ""

                # Extract media links
                image_files = []
                video_file = None
                try:
                    media_elements = self.driver.find_elements(By.XPATH, "//div[@role='dialog']//img | //div[@role='dialog']//video/source")
                    for media in media_elements:
                        media_url = media.get_attribute("src")
                        if media_url:
                            filename = self.download_media(media_url, self.IMAGE_SAVE_PATH, "ig_img")
                            if filename:
                                image_files.append(filename)
                except Exception as e:
                    print(f"[WARNING] Error extracting media: {e}")

                # Save post info
                post_entry = {
                    "post_id": f"{self.page_url}_{post_count}",
                    "text": post_text,
                    "images": image_files,
                    "video": video_file,
                }
                post_data.append(post_entry)
                post_count += 1

                # Close the post dialog
                self.driver.find_element(By.XPATH, "//button[contains(@aria-label, 'Close')]").click()
                time.sleep(2)

            # Scroll down and wait for more posts to load
            print("[INFO] Scrolling for more posts...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Break if no new posts are loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] No new posts loaded. Stopping scrape.")
                break
            last_height = new_height

        print(f"[INFO] Finished scraping {post_count} posts. Saving data...")
        self.save_to_jsonl(post_data, self.TEXT_SAVE_PATH)

        # Close WebDriver
        self.driver.quit()

    def download_media(self, url, save_path, prefix="ig_media"):
        """Downloads an image or video from a URL and saves it."""
        if not url:
            return None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers, timeout=10)
            if response.status_code == 200:
                filename = f"{prefix}_{os.path.basename(url.split('?')[0])}"
                filepath = os.path.join(save_path, filename)

                image = Image.open(BytesIO(response.content))
                image.save(filepath)
                return filename
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
        return None

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Saved {len(data)} records to {file_path}")


class ScrapeLinkedInSelenium:
    def __init__(self, company_url="https://www.linkedin.com/company/capitalareafoodbank/", max_posts=20, cookies_file="cookies/linkedin_cookies.json"):
        """Initialize Selenium scraper for LinkedIn with stored cookies."""
        self.company_url = company_url
        self.max_posts = max_posts
        self.cookies_file = cookies_file

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "linkedin_posts.jsonl")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.TEXT_SAVE_PATH), exist_ok=True)
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)

        print(f"[INFO] ScrapeLinkedInSelenium initialized for company: {self.company_url}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Maximize window
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # Use a different user-data-dir to avoid profile conflicts
        chrome_options.add_argument("--user-data-dir=" + os.path.expanduser("~/Library/Application Support/Google/Chrome/SeleniumProfile"))

        # Set Chrome Driver Path (Adjust path if necessary)
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

        # Load Cookies
        self.load_cookies()

    def load_cookies(self):
        """Loads stored LinkedIn cookies into Selenium."""
        self.driver.get("https://www.linkedin.com/")  # Open LinkedIn login page
        time.sleep(5)  # Wait for page to load

        if os.path.exists(self.cookies_file):
            try:
                with open(self.cookies_file, "r", encoding="utf-8") as f:
                    cookies = json.load(f)

                # Add each cookie to the browser
                for cookie in cookies:
                    cookie_dict = {
                        "name": cookie["name"],
                        "value": cookie["value"],
                        "domain": cookie["domain"],
                        "path": cookie["path"],
                        "secure": cookie.get("secure", False),
                        "httpOnly": cookie.get("httpOnly", False),
                    }
                    self.driver.add_cookie(cookie_dict)

                print(f"[INFO] Loaded {len(cookies)} cookies from {self.cookies_file}")
                self.driver.refresh()  # Refresh to apply cookies
                time.sleep(5)  # Allow time for authentication
            except Exception as e:
                print(f"[ERROR] Failed to load cookies: {e}")
        else:
            print(f"[WARNING] No cookie file found. Login may be required.")

    def scrape_linkedin(self):
        """Scrape posts from LinkedIn company page using Selenium."""
        print(f"[INFO] Scraping posts from LinkedIn company page: {self.company_url}")
        self.driver.get(self.company_url)
        time.sleep(5)

        post_data = []
        post_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while post_count < self.max_posts:
            print(f"[INFO] Scanning for posts... (current count: {post_count})")

            # Find posts on the page
            posts = self.driver.find_elements(By.XPATH, "//div[contains(@class, 'update')]")
            if not posts:
                print("[WARNING] No posts found. Retrying after scroll.")
                time.sleep(2)
                continue

            for post in posts:
                if post_count >= self.max_posts:
                    break  # Stop when max posts reached

                # Extract post text
                try:
                    post_text = post.find_element(By.XPATH, ".//span[contains(@class, 'break-words')]").text.strip()
                except:
                    post_text = ""

                # Extract media links
                image_files = []
                video_file = None
                try:
                    media_elements = post.find_elements(By.XPATH, ".//img | .//video/source")
                    for media in media_elements:
                        media_url = media.get_attribute("src")
                        if media_url:
                            filename = self.download_media(media_url, self.IMAGE_SAVE_PATH, "li_img")
                            if filename:
                                image_files.append(filename)
                except Exception as e:
                    print(f"[WARNING] Error extracting media: {e}")

                # Save post info
                post_entry = {
                    "post_id": f"{self.company_url}_{post_count}",
                    "text": post_text,
                    "images": image_files,
                    "video": video_file,
                }
                post_data.append(post_entry)
                post_count += 1

            # Scroll down and wait for more posts to load
            print("[INFO] Scrolling for more posts...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Break if no new posts are loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] No new posts loaded. Stopping scrape.")
                break
            last_height = new_height

        print(f"[INFO] Finished scraping {post_count} posts. Saving data...")
        self.save_to_jsonl(post_data, self.TEXT_SAVE_PATH)

        # Close WebDriver
        self.driver.quit()

    def download_media(self, url, save_path, prefix="li_media"):
        """Downloads an image or video from a URL and saves it."""
        if not url:
            return None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers, timeout=10)
            if response.status_code == 200:
                filename = f"{prefix}_{os.path.basename(url.split('?')[0])}"
                filepath = os.path.join(save_path, filename)

                image = Image.open(BytesIO(response.content))
                image.save(filepath)
                return filename
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
        return None

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Saved {len(data)} records to {file_path}")


class ScrapeYouTubeSelenium:
    def __init__(self, channel_url="https://www.youtube.com/channel/UCAYzcvJNH9imavDTTEpJYUw", max_videos=10):
        """Initialize Selenium scraper for YouTube channel."""
        self.channel_url = channel_url
        self.max_videos = max_videos

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "youtube_videos.jsonl")
        self.VIDEO_SAVE_PATH = os.path.join(self.BASE_PATH, "videos")
        self.IMAGE_SAVE_PATH = os.path.join(self.BASE_PATH, "images")

        # Ensure directories exist
        os.makedirs(os.path.dirname(self.TEXT_SAVE_PATH), exist_ok=True)
        os.makedirs(self.VIDEO_SAVE_PATH, exist_ok=True)
        os.makedirs(self.IMAGE_SAVE_PATH, exist_ok=True)

        print(f"[INFO] ScrapeYouTubeSelenium initialized for channel: {self.channel_url}")

        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--start-maximized")  # Maximize window
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Avoid bot detection
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-running-insecure-content")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")

        # Set Chrome Driver Path (Adjust path if necessary)
        chromedriver_path = "/opt/homebrew/bin/chromedriver"
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def scrape_youtube(self):
        """Scrape video links from the YouTube channel."""
        print(f"[INFO] Scraping videos from YouTube channel: {self.channel_url}")
        self.driver.get(self.channel_url)
        time.sleep(5)

        video_data = []
        video_count = 0
        last_height = self.driver.execute_script("return document.body.scrollHeight")

        while video_count < self.max_videos:
            print(f"[INFO] Scanning for videos... (current count: {video_count})")

            # Find video links on the page
            video_elements = self.driver.find_elements(By.XPATH, "//a[@id='thumbnail' and @href]")
            video_links = [video.get_attribute("href") for video in video_elements if video.get_attribute("href")]

            if not video_links:
                print("[WARNING] No videos found. Retrying after scroll.")
                time.sleep(2)
                continue

            for video_url in video_links:
                if video_count >= self.max_videos:
                    break  # Stop when max videos reached
                
                video_info = self.scrape_video_details(video_url)
                if video_info:
                    video_data.append(video_info)
                    video_count += 1

            # Scroll down and wait for more videos to load
            print("[INFO] Scrolling for more videos...")
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(5)

            # Break if no new videos are loaded
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("[INFO] No new videos loaded. Stopping scrape.")
                break
            last_height = new_height

        print(f"[INFO] Finished scraping {video_count} videos. Saving data...")
        self.save_to_jsonl(video_data, self.TEXT_SAVE_PATH)

        # Close WebDriver
        self.driver.quit()

    def scrape_video_details(self, video_url):
        """Scrape details for a single video."""
        print(f"[INFO] Scraping video: {video_url}")
        self.driver.get(video_url)
        time.sleep(5)

        # Extract video title
        try:
            title = self.driver.find_element(By.XPATH, "//h1").text.strip()
        except:
            title = "Unknown Title"

        # Extract video description
        try:
            desc = self.driver.find_element(By.XPATH, "//div[@id='description']//yt-formatted-string").text.strip()
        except:
            desc = "No description available."

        # Extract thumbnail image
        try:
            thumb_element = self.driver.find_element(By.XPATH, "//meta[@property='og:image']")
            thumb_url = thumb_element.get_attribute("content")
            thumbnail_path = self.download_media(thumb_url, self.IMAGE_SAVE_PATH, "yt_thumb")
        except:
            thumbnail_path = None

        # Download video
        video_filename = self.download_video(video_url)

        # Extract closed captions
        video_id = video_url.split("v=")[-1]
        captions = self.get_captions(video_id)

        # Store data
        return {
            "video_url": video_url,
            "title": title,
            "description": desc,
            "thumbnail": thumbnail_path,
            "video_file": video_filename,
            "captions": captions
        }

    def download_media(self, url, save_path, prefix="yt_media"):
        """Downloads an image from a URL and saves it."""
        if not url:
            return None

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, stream=True, headers=headers, timeout=10)
            if response.status_code == 200:
                filename = f"{prefix}_{os.path.basename(url.split('?')[0])}"
                filepath = os.path.join(save_path, filename)

                image = Image.open(BytesIO(response.content))
                image.save(filepath)
                return filename
        except Exception as e:
            print(f"[ERROR] Failed to download {url}: {e}")
        return None

    def download_video(self, video_url):
        """Download the YouTube video using pytube."""
        try:
            yt = YouTube(video_url)
            video_stream = yt.streams.filter(progressive=True, file_extension="mp4").first()
            filename = yt.title.replace(" ", "_") + ".mp4"
            video_path = os.path.join(self.VIDEO_SAVE_PATH, filename)
            video_stream.download(output_path=self.VIDEO_SAVE_PATH, filename=filename)
            print(f"[INFO] Downloaded video: {video_path}")
            return video_path
        except Exception as e:
            print(f"[ERROR] Failed to download video: {e}")
            return None

    def get_captions(self, video_id):
        """Retrieve closed captions (subtitles) for a YouTube video."""
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            captions = "\n".join([entry["text"] for entry in transcript])
            return captions
        except Exception as e:
            print(f"[WARNING] No captions found for video {video_id}: {e}")
            return None

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file."""
        with open(file_path, "w", encoding="utf-8") as file:
            for entry in data:
                file.write(json.dumps(entry, ensure_ascii=False) + "\n")
        print(f"[INFO] Saved {len(data)} records to {file_path}")



class ScrapeYouTube:
    def __init__(self, api_key, channel_id, max_videos=10):
        """Initialize YouTube scraper with API key."""
        self.api_key = api_key
        self.channel_id = channel_id
        self.max_videos = max_videos

        # Define storage paths
        self.BASE_PATH = "/"
        self.TEXT_SAVE_PATH = os.path.join(self.BASE_PATH, "text", "youtube_posts.jsonl")
        self.CAPTIONS_SAVE_PATH = os.path.join(self.BASE_PATH, "captions")

        # Ensure directories exist
        os.makedirs(self.CAPTIONS_SAVE_PATH, exist_ok=True)
        os.makedirs(os.path.dirname(self.TEXT_SAVE_PATH), exist_ok=True)

        print(f"[INFO] ScrapeYouTube initialized for channel: {self.channel_id}")

        # Initialize YouTube API
        self.youtube = build("youtube", "v3", developerKey=self.api_key)

    def get_video_metadata(self):
        """Fetch video metadata (ID, title, description) from YouTube channel."""
        print("[INFO] Fetching video metadata...")
        request = self.youtube.search().list(
            part="id,snippet",
            channelId=self.channel_id,
            maxResults=self.max_videos,
            order="date"
        )
        response = request.execute()

        video_data = []
        for item in response.get("items", []):
            if "videoId" in item["id"]:
                video_data.append({
                    "video_id": item["id"]["videoId"],
                    "title": item["snippet"]["title"],
                    "description": item["snippet"]["description"]
                })

        print(f"[INFO] Found {len(video_data)} videos.")
        return video_data

    def download_captions(self, video_id):
        """Download YouTube captions and save them as a .txt file."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        temp_srt_path = os.path.join(self.CAPTIONS_SAVE_PATH, f"{video_id}.srt")
        final_txt_path = os.path.join(self.CAPTIONS_SAVE_PATH, f"{video_id}.txt")

        ydl_opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "srt",
            "outtmpl": temp_srt_path.replace(".srt", ""),
            "quiet": False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find and rename SRT file (handling possible .vtt case)
            for file in os.listdir(self.CAPTIONS_SAVE_PATH):
                if file.startswith(video_id) and file.endswith(".srt"):
                    os.rename(os.path.join(self.CAPTIONS_SAVE_PATH, file), temp_srt_path)
                elif file.startswith(video_id) and file.endswith(".vtt"):
                    os.rename(os.path.join(self.CAPTIONS_SAVE_PATH, file), temp_srt_path)

            # Convert SRT to TXT
            if os.path.exists(temp_srt_path):
                with open(temp_srt_path, "r", encoding="utf-8") as srt_file:
                    lines = srt_file.readlines()

                captions = []
                for line in lines:
                    if not line.strip().isdigit() and "-->" not in line:
                        captions.append(line.strip())

                # Save cleaned captions as .txt
                with open(final_txt_path, "w", encoding="utf-8") as txt_file:
                    txt_file.write("\n".join(captions))

                os.remove(temp_srt_path)  # Delete SRT after conversion
                print(f"[INFO] Successfully saved captions as .txt for video: {video_id}")
                return final_txt_path

            else:
                print(f"[WARNING] No captions available for video {video_id}.")
                return None

        except Exception as e:
            print(f"[ERROR] Failed to download captions {video_id}: {e}")
            return None

    def scrape_youtube(self):
        """Main method to scrape YouTube captions, titles, and descriptions (no video downloads)."""
        print(f"[INFO] Scraping YouTube channel: {self.channel_id}")
        videos = self.get_video_metadata()

        video_data = []
        for idx, video in enumerate(videos):
            video_id = video["video_id"]
            print(f"[INFO] Processing video {idx+1}/{len(videos)}: {video_id}")

            # Download video and captions
            video_file = self.download_video(video_id)
            captions_file = self.download_captions(video_id)

            video_entry = {
                "video_id": video_id,
                "title": video["title"],
                "description": video["description"],
                "video_file": video_file,
                "captions_file": captions_file
            }
            video_data.append(video_entry)

            # Save progress every 5 videos
            if len(video_data) % 5 == 0:
                self.save_to_jsonl(video_data, self.TEXT_SAVE_PATH)

        print(f"[INFO] Finished scraping {len(videos)} videos. Saving data...")
        self.save_to_jsonl(video_data, self.TEXT_SAVE_PATH)

    def save_to_jsonl(self, data, file_path):
        """Saves data to a JSONL file ensuring correct format."""
        try:
            with open(file_path, "w", encoding="utf-8") as file:
                for entry in data:
                    json.dump(entry, file, ensure_ascii=False)
                    file.write("\n")

            print(f"[INFO] Saved {len(data)} records to {file_path} in proper JSONL format.")
        except Exception as e:
            print(f"[ERROR] Failed to save data: {e}")



# Example Usage:
if __name__ == "__main__":
    # Replace with your Twitter API credentials
    # API_KEY = "YOUR_API_KEY"
    # API_SECRET_KEY = "YOUR_API_SECRET_KEY"
    # ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
    # ACCESS_TOKEN_SECRET = "YOUR_ACCESS_TOKEN_SECRET"

    # scraper = ScrapeX_tweepy(username="foodbankmetrodc", 
    #                 api_key=API_KEY, 
    #                 api_secret_key=API_SECRET_KEY, 
    #                 access_token=ACCESS_TOKEN, 
    #                 access_token_secret=ACCESS_TOKEN_SECRET, 
    #                 max_tweets=100)

    # scraper.scrape_twitter()

    scraper = ScrapeFacebook(page_id="145563868868546", max_pages=10)
    # scraper = ScrapeFacebook(page_id="CapitalAreaFoodBank/#", max_pages=10)
    scraper.scrape_facebook()

    scraper = ScrapeTwitterSelenium(username="foodbankmetrodc", max_tweets=10)
    scraper.scrape_twitter()

    scraper = ScrapeFacebookSelenium(page_url="https://www.facebook.com/CapitalAreaFoodBank", max_posts=20)
    scraper.scrape_facebook()

    scraper = ScrapeInstagramSelenium(page_url="https://www.instagram.com/capitalareafoodbank/", max_posts=10)
    scraper.scrape_instagram()

    scraper = ScrapeLinkedInSelenium(company_url="https://www.linkedin.com/company/capitalareafoodbank/", max_posts=10)
    scraper.scrape_linkedin()

    scraper = ScrapeYouTubeSelenium(channel_url="https://www.youtube.com/channel/UCAYzcvJNH9imavDTTEpJYUw", max_videos=10)
    scraper.scrape_youtube()

    API_KEY = ""  # Replace with your actual API key
    CHANNEL_ID = "UCAYzcvJNH9imavDTTEpJYUw"  # Capital Area Food Bank's YouTube channel ID

    scraper = ScrapeYouTube(api_key=API_KEY, channel_id=CHANNEL_ID, max_videos=100)
    scraper.scrape_youtube()


