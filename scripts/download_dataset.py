import os
import urllib.request

def download_data():
    url = "https://huggingface.co/datasets/0xmarvel/student-stress-survey/resolve/main/student-stress-data.jsonl"
    dest_dir = r"c:\Users\Tejendra Singh\Desktop\Sarthi_Summer_Intern\Wellmate-Web\backend\Engines\PIE\data"
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, "student-stress-data.jsonl")
    
    print(f"Downloading dataset from {url} to {dest_path}...")
    try:
        # Use User-Agent header to prevent 403 Forbidden responses from Hugging Face CDN
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            data = response.read()
            out_file.write(data)
        print("Download completed successfully!")
    except Exception as e:
        print(f"Error downloading dataset: {e}")

if __name__ == "__main__":
    download_data()
