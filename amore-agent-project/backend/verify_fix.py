import requests
import json

def verify():
    url = "http://localhost:8000/chat"
    payload = {
        "message": "상품을 구경만 하고 아직 구매하지 않은 신규 고객에게 첫 구매를 제안하는 메시지 작성",
        "history": []
    }
    
    print(f"Sending request to {url}...")
    try:
        with requests.post(url, json=payload, stream=True) as response:
            if response.status_code == 200:
                print("Connection successful. Reading stream...")
                candidates_found = False
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        if decoded_line.startswith("data: "):
                            json_str = decoded_line[6:]
                            try:
                                event = json.loads(json_str)
                                if event.get("type") == "data" and event.get("key") == "candidates":
                                    val = event.get("value")
                                    purposes = val.get("purposes", [])
                                    print(f"Received Candidates Purposes: {purposes}")
                                    
                                    # Verification Logic
                                    # Expected: "첫 구매 유도 (Welcome)"
                                    # NOT: "[G01_WELCOME]: ..."
                                    
                                    clean_format = True
                                    for p in purposes:
                                        if "[" in p and "]" in p:
                                            print(f"FAIL: Purpose string still contains ID: {p}")
                                            clean_format = False
                                        else:
                                            print(f"PASS: Purpose string is clean: {p}")
                                            
                                    candidates_found = True
                                    break # Found candidates, that's enough
                            except:
                                continue
                if not candidates_found:
                    print("FAIL: Did not receive candidates data.")
            else:
                print(f"FAIL: Status Code {response.status_code}")
    except Exception as e:
        print(f"FAIL: Exception {e}")

if __name__ == "__main__":
    verify()
