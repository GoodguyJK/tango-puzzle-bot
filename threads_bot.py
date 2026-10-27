import os
import sys
import time
import logging
import requests
from google import genai

# ==================================================
# 1. 기본 설정 및 환경변수
# ==================================================
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN", "").strip()
THREADS_API_BASE = "https://graph.threads.net/v1.0"

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 3
REQUEST_TIMEOUT = 30
DRY_RUN = False  # 실제 배포 모드

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

def validate_settings():
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    if not THREADS_ACCESS_TOKEN:
        raise ValueError("THREADS_ACCESS_TOKEN 환경변수가 설정되지 않았습니다.")

def generate_content():
    """Tango 로직 퍼즐 전용 스레드 홍보 글 생성"""
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = """
너는 중독성 있는 두뇌 퍼즐을 즐기고 직접 게임도 만드는 2030 인디게임 개발자이자 퍼즐 마니아다.
스레드(Threads)에 올릴 로직 퍼즐 게임 'Tango(탱고)' 홍보 꿀팁 글을 하나 써줘.

[게임 핵심 정보]
- 게임명: Tango (탱고 - 감성 로직 퍼즐)
- 핵심 3대 규칙: 
  1) 3연속 금지: 가로/세로 어느 줄이든 같은 기호(☀️/🌙) 3개 연속 배치 불가
  2) 절반 균등 배치: 모든 행/열에 해(☀️)와 달(🌙)이 딱 절반(6x6은 3개씩, 8x8은 4개씩) 균등 배치
  3) 연산자 제약: [=]는 같은 모양, [x]는 서로 다른 모양
- 특징: 찍기 없는 100% 논리 유일해, 답 대신 사고 과정을 짚어주는 '스마트 코칭 힌트', 1000개 스테이지, 요일별 데일리 챌린지, 눈 편한 다크모드

[작성 규칙]
1. 말투: 완전 스레드 감성의 찰진 반말 (~함, ~했음, ~임, ~하셈, ~더라 혼용). 딱딱한 존댓말 금지.
2. 분량: 160~220자 내외로 모바일 한 화면에 쏙 들어오게 작성.
3. 구성:
- 첫 줄: 스크롤을 멈추게 만드는 어그로/흥미 유발 한 줄
- 본문: 구체적인 공감 포인트나 논리적 재미 2~3줄 (줄바꿈과 이모지 적극 활용)
- 마지막 줄(필수 고정): 📌 퍼즐 무료로 풀고 뇌 스트레칭할 사람은 프로필 링크에 뒀음

4. 주제 풀 (아래 4가지 각도 중 매번 하나를 골라 완전히 새롭게 쓸 것):
- [유형 1: 스도쿠/노노그램 탈출] 스도쿠 숫자 계산이나 노노그램 노가다에 질린 사람들에게 기호(☀️🌙) 3대 룰만으로 풀리는 연역적 깔끔함 추천
- [유형 2: 출퇴근 숏폼 디톡스] 지하철에서 의미 없이 릴스/쇼츠 넘기다 멍해지는 대신 5분 동안 뇌 워밍업하고 도파민 채우는 갓생 루틴 강조
- [유형 3: 1인 개발 비하인드] 단순히 정답만 던져주는 힌트가 싫어서 "왜 여기가 해(☀️)인지" 논리를 설명해주는 코칭 엔진을 직접 갈아 넣었다는 개발 스토리
- [유형 4: 미니 퀴즈 유도] "= 표시는 같은 모양, x는 다른 모양인데, 3개 연속 못 놓으면 이 칸은 뭘까?" 식의 댓글 토론 유도

5. 주의사항:
- 본문에 웹사이트 URL 절대 포함 금지
- 제목, 따옴표, 해설 없이 오직 스레드에 업로드할 본문 텍스트만 출력할 것.
"""

    models_to_try = ["gemini-3.6-flash", "gemini-3.8-flash"]

    for attempt in range(1, MAX_RETRIES + 1):
        for model_name in models_to_try:
            try:
                logging.info("Gemini 글 생성 시도 (%s/%s) - 모델: %s", attempt, MAX_RETRIES, model_name)
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={"temperature": 1.0}
                )
                content = (response.text or "").strip()
                if not content:
                    raise ValueError("생성된 내용이 비어 있습니다.")
                if "http://" in content.lower() or "https://" in content.lower():
                    raise ValueError("URL이 포함되어 중단합니다.")
                logging.info("글 생성 성공 (%s자)", len(content))
                return content
            except Exception as exc:
                logging.warning("모델 %s 호출 실패: %s", model_name, exc)

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY_SECONDS * attempt)
        else:
            raise RuntimeError("Gemini 글 생성에 최종 실패했습니다.")

def threads_request(method, endpoint, payload=None):
    url = f"{THREADS_API_BASE}/{endpoint.lstrip('/')}"
    headers = {"Authorization": f"Bearer {THREADS_ACCESS_TOKEN}"}
    params = {}
    data = {}

    if method.upper() == "GET":
        params = dict(payload or {})
        params["access_token"] = THREADS_ACCESS_TOKEN
        params["fields"] = "id,username"
    else:
        data = dict(payload or {})
        data["access_token"] = THREADS_ACCESS_TOKEN

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params if method.upper() == "GET" else None,
                data=data if method.upper() == "POST" else None,
                timeout=REQUEST_TIMEOUT,
            )
            data_res = response.json()
            if not response.ok or "error" in data_res:
                raise RuntimeError(f"API 오류: {data_res}")
            return data_res
        except Exception as exc:
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS * attempt)
            else:
                raise RuntimeError(f"Threads API 요청 실패: {exc}") from exc

def post_to_threads(text):
    data = threads_request("GET", "/me")
    user_id = data.get("id")
    username = data.get("username", "")
    logging.info("계정 확인: @%s (ID: %s)", username, user_id)

    container = threads_request("POST", f"/{user_id}/threads", {"media_type": "TEXT", "text": text})
    creation_id = container.get("id")

    published = threads_request("POST", f"/{user_id}/threads_publish", {"creation_id": creation_id})
    post_id = published.get("id")
    logging.info("게시 성공! 게시물 ID: %s", post_id)
    return post_id

def main():
    try:
        validate_settings()
        content = generate_content()
        print("\n" + "=" * 40 + "\n" + content + "\n" + "=" * 40 + "\n")
        if not DRY_RUN:
            post_to_threads(content)
    except Exception as exc:
        logging.error("%s", exc)
        sys.exit(1)

if __name__ == "__main__":
    main()
