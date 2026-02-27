print("Starting test_2.py...")
try:
    from dotenv import load_dotenv, find_dotenv
    print("Found dotenv module.")
    
    dotenv_path = find_dotenv()
    print(f"Dotenv path: {dotenv_path}")
    
    if dotenv_path:
        loaded = load_dotenv(dotenv_path)
        print(f"Loaded dotenv: {loaded}")
    else:
        print("No .env file found.")
    
    import os
    hf_token = os.environ.get('HF_TOKEN')
    print(f"HF_TOKEN: {hf_token[:4]}... (truncated)" if hf_token else "HF_TOKEN: None")
    
except Exception as e:
    print(f"Error: {e}")
