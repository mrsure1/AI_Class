import os
import sys
import time
import json
import logging
import asyncio
import re
from pathlib import Path
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()

# 전역 설정 및 폰트 검색 경로
SYSTEM_FONTS = [
    r"C:\Windows\Fonts\malgunbd.ttf",  # 맑은 고딕 Bold
    r"C:\Windows\Fonts\malgun.ttf",    # 맑은 고딕 Regular
    r"C:\Windows\Fonts\Arial.ttf",     # 영문 기본 (한글 깨질 수 있음)
]

def get_font_path():
    """시스템에서 사용 가능한 맑은 고딕 폰트 경로를 반환합니다."""
    for font_path in SYSTEM_FONTS:
        if os.path.exists(font_path):
            return font_path
    return None

def clean_text_for_image(text: str) -> str:
    """이미지 렌더링 시 깨짐을 방지하기 위해 이모지 및 특수 유니코드 기호를 제거합니다."""
    if not text:
        return ""
    # BMP 바깥의 유니코드 문자(이모지 등) 및 특정 기호 범위 제거
    # \U00010000-\U0010FFFF : 대부분의 컬러 이모지
    # \u2600-\u27BF : Miscellaneous Symbols & Dingbats (흑백 이모지, 별, 하트 등)
    # \u2300-\u23FF : Miscellaneous Technical
    pattern = re.compile(r'[\U00010000-\U0010FFFF\u2600-\u27BF\u2300-\u23FF]')
    cleaned = pattern.sub('', text)
    # 불필요하게 두 번 들어간 공백 제거 및 앞뒤 공백 정리
    cleaned = re.sub(r' +', ' ', cleaned).strip()
    return cleaned

# 필요한 폴더 생성
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------
# 1. AI 콘텐츠 생성 모듈 (Gemini API)
# ----------------------------------------------------
import google.generativeai as genai

def init_gemini():
    """Gemini API를 초기화합니다."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY가 환경 변수에 설정되어 있지 않습니다.")
        return False
    genai.configure(api_key=api_key)
    return True

def generate_instagram_content(topic: str, content_type: str = "both", keywords: str = ""):
    """
    주제에 기반하여 인스타그램 피드 및 릴스 대본을 생성합니다.
    content_type: 'feed', 'reels', 또는 'both'
    keywords: 꼭 포함하고 싶은 핵심 단어 또는 요구사항 문장
    """
    if not init_gemini():
        raise ValueError("Gemini API 초기화 실패. API 키를 확인하세요.")
    
    profile_link = os.getenv("PROFILE_LINK", "프로필 링크")
    
    # 최신 Gemini 2.5 Flash 모델 사용
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    prompt = f"""
    당신은 전문적인 인스타그램 크리에이터이자 마케터입니다.
    다음 주제에 대해 인스타그램 게시글과 릴스 콘텐츠를 한 번에 생성해 주세요.
    
    주제: "{topic}"
    실제 연동되는 프로필 링크 주소 정보: "{profile_link}"
    추가로 꼭 언급 및 포함할 내용(키워드/문장): "{keywords}"
    
    콘텐츠 생성 가이드:
    1. 피드 본문 캡션(caption)과 릴스 캡션, 릴스 대본(script)의 맨 마지막 행동 유도 문구(CTA)에서는 반드시 사용자가 설정한 프로필 링크 정보("{profile_link}")를 구체적으로 언급해 주세요.
       예: "자세한 설명과 강의 신청은 제 프로필 링크({profile_link})를 클릭해서 확인해보세요!" 또는 "지금 프로필 링크({profile_link})에서 'AI 6시간 과정 신청서'를 접수 중입니다!"
    2. 만약 프로필 링크 정보가 단순히 "프로필 링크"로 넘어왔을 경우에만 주소 없이 "프로필 링크에서 지금 바로 확인해보세요!" 형태로 작성하세요.
    3. 만약 추가로 언급 및 포함할 내용("{keywords}")이 입력되어 있다면, 해당 단어나 정보들을 문맥에 맞게 매끄럽게 다듬어서 카드뉴스 본문 슬라이드(cards), 피드 본문 캡션, 릴스 대본(script) 중 적절한 위치에 자연스럽게 녹여내어 삽입해 주세요. (가장 실용적이고 실제 정보처럼 매끄럽게 다듬어야 합니다.)
    4. 카드뉴스의 메인 제목("title")과 카드 내용("cards") 리스트에는 어떠한 이모지(Emoji)나 특수 기호도 절대 포함하지 마세요. (이미지 생성 폰트가 이모지를 지원하지 않아 깨지기 때문입니다.) 오직 한글, 영어, 숫자, 기본적인 문장 부호(., !? 등)만 사용해야 합니다. 반면 본문 캡션("caption")에는 이모지를 적극적으로 사용해도 괜찮습니다.
    
    결과는 반드시 아래의 JSON 형식으로만 반환해 주세요. 코드 블록(```json ... ```)을 사용해 주시고, 다른 설명 텍스트는 추가하지 마십시오.
    
    JSON 형식:
    {{
      "feed": {{
        "title": "피드 카드뉴스 메인 제목 (15자 이내)",
        "cards": [
          "카드 1 내용 (소개 및 흥미 유발, 2-3문장)",
          "카드 2 내용 (핵심 정보 1, 2-3문장)",
          "카드 3 내용 (핵심 정보 2, 2-3문장)",
          "카드 4 내용 (실행 방안/팁, 2-3문장)",
          "카드 5 내용 (마무리 및 행동 유도, 2-3문장)"
        ],
        "caption": "인스타그램 업로드용 본문 캡션 (풍부한 이모지와 적절한 줄바꿈 포함)",
        "hashtags": "#태그1 #태그2 #태그3 #태그4 #AI교육"
      }},
      "reels": {{
        "title": "릴스 영상 제목 (10자 이내)",
        "script": [
          "안녕하세요! 오늘은 인상적인 주제에 대해 알아볼게요.",
          "첫 번째로 중요한 사실은 이겁니다.",
          "두 번째는 바로 이 부분인데요, 놓치기 쉽습니다.",
          "이 팁만 알고 계셔도 훨씬 앞서갈 수 있습니다.",
          "더 자세한 팁은 제 프로필 링크를 확인해 보세요!"
        ],
        "caption": "릴스 업로드용 본문 캡션 (풍부한 이모지 포함)",
        "hashtags": "#릴스 #릴스추천 #주제해시태그 #정보공유"
      }}
    }}
    
    한국어로 작성하되, MZ세대와 일반 대중에게 어필할 수 있도록 친근하고 명확하게 작성해 주세요.
    """
    
    logger.info(f"'{topic}' 주제에 대한 AI 콘텐츠 생성 중...")
    response = model.generate_content(prompt)
    
    # JSON 파싱
    text = response.text.strip()
    try:
        # 마크다운 코드 블록 제거
        if text.startswith("```json"):
            text = text.split("```json")[1].split("```")[0].strip()
        elif text.startswith("```"):
            text = text.split("```")[1].split("```")[0].strip()
            
        data = json.loads(text)
        logger.info("AI 콘텐츠 생성 완료!")
        return data
    except Exception as e:
        logger.error(f"JSON 파싱 실패: {e}")
        logger.debug(f"응답 텍스트: {text}")
        raise ValueError("AI 응답을 JSON으로 변환하는 데 실패했습니다.")

# ----------------------------------------------------
# 2. 카드뉴스 이미지 생성 모듈 (Pillow)
# ----------------------------------------------------
from PIL import Image, ImageDraw, ImageFont

def draw_wrapped_text(draw, text, font, color, max_width, start_y, line_spacing=10):
    """지정된 너비를 초과하지 않도록 텍스트를 줄바꿈하여 그립니다."""
    words = text.split(' ')
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        test_line = ' '.join(current_line)
        # 폰트별 텍스트 경계 상자 획득
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]
        if width > max_width:
            current_line.pop()
            lines.append(' '.join(current_line))
            current_line = [word]
            
    if current_line:
        lines.append(' '.join(current_line))
        
    y = start_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        # 중앙 정렬
        x = (1080 - w) / 2
        draw.text((x, y), line, font=font, fill=color)
        y += h + line_spacing
        
    return y

def create_card_news(feed_data: dict):
    """피드 데이터를 활용해 1080x1080 카드뉴스 이미지들을 생성합니다."""
    font_path = get_font_path()
    if not font_path:
        logger.error("시스템에서 맑은 고딕 폰트를 찾을 수 없어 텍스트를 그릴 수 없습니다.")
        return []
        
    title_font = ImageFont.truetype(font_path, 60)
    body_font = ImageFont.truetype(font_path, 36)
    footer_font = ImageFont.truetype(font_path, 28)
    
    cards_paths = []
    title = clean_text_for_image(feed_data["title"])
    cards = [clean_text_for_image(c) for c in feed_data["cards"]]
    
    # 테마 색상 (그라데이션 또는 세련된 어두운 배경)
    bg_color = (26, 23, 20)      # Sleek Dark
    text_color = (235, 232, 227) # Off-white
    point_color = (196, 137, 74) # Gold/Bronze
    tag_color = (90, 143, 110)   # Greenish Sage
    
    # 1. 타이틀 카드 (첫 페이지)
    img = Image.new("RGB", (1080, 1080), color=bg_color)
    draw = ImageDraw.Draw(img)
    
    # 테두리 디자인
    draw.rectangle([40, 40, 1040, 1040], outline=point_color, width=4)
    
    # 상단 태그
    draw.text((540, 150), "@ai.make.learn", font=footer_font, fill=tag_color, anchor="mm")
    
    # 메인 타이틀 그리기
    draw_wrapped_text(draw, title, title_font, text_color, 850, 400)
    
    # 하단 풋터
    draw.text((540, 930), "ChatGPT · Gemini 활용 꿀팁", font=footer_font, fill=point_color, anchor="mm")
    
    first_card_path = OUTPUT_DIR / "card_0.png"
    img.save(first_card_path)
    cards_paths.append(str(first_card_path))
    
    # 2. 본문 카드들 (2 ~ N 페이지)
    for idx, card_content in enumerate(cards):
        img = Image.new("RGB", (1080, 1080), color=bg_color)
        draw = ImageDraw.Draw(img)
        
        # 테두리
        draw.rectangle([40, 40, 1040, 1040], outline=tag_color, width=3)
        
        # 상단 페이지 번호
        draw.text((540, 100), f"{idx + 1} / {len(cards)}", font=footer_font, fill=point_color, anchor="mm")
        
        # 본문 내용
        draw_wrapped_text(draw, card_content, body_font, text_color, 850, 380, line_spacing=20)
        
        # 하단 핸들
        draw.text((540, 980), "@ai.make.learn", font=footer_font, fill=tag_color, anchor="mm")
        
        card_path = OUTPUT_DIR / f"card_{idx + 1}.png"
        img.save(card_path)
        cards_paths.append(str(card_path))
        
    logger.info(f"총 {len(cards_paths)}장의 카드뉴스 이미지 생성 완료.")
    return cards_paths

# ----------------------------------------------------
# 3. 릴스 동영상 생성 모듈 (edge-tts + MoviePy)
# ----------------------------------------------------
import edge_tts
from moviepy.editor import ImageClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

async def generate_tts(text_list: list, output_audio_path: str):
    """edge-tts를 이용해 텍스트 리스트를 하나의 음성 파일로 변환하고 각 구간의 재생 시간을 계산합니다."""
    # 문장 사이에 살짝의 공백을 주기 위해 마침표 뒤에 0.5초의 공백 추가를 위한 작업
    full_text = " ... ".join(text_list)
    communicate = edge_tts.Communicate(full_text, voice="ko-KR-SunHiNeural")
    
    # 음성 파일 저장
    await communicate.save(output_audio_path)
    logger.info(f"TTS 음성 파일 저장 완료: {output_audio_path}")

def create_reels_video(reels_data: dict):
    """릴스 데이터를 바탕으로 9:16 비율의 동영상을 자동 제작합니다."""
    script_lines = reels_data["script"]
    title = reels_data["title"]
    
    audio_path = OUTPUT_DIR / "reels_voice.mp3"
    video_output_path = OUTPUT_DIR / "reels_output.mp4"
    
    # 1. TTS 생성 (비동기 함수를 동기식으로 실행)
    asyncio.run(generate_tts(script_lines, str(audio_path)))
    
    # 2. 오디오 로드 및 전체 재생 시간 확인
    audio_clip = AudioFileClip(str(audio_path))
    duration = audio_clip.duration
    
    # 3. 비디오 배경 이미지 생성 (9:16 비율인 1080x1920 크기)
    font_path = get_font_path()
    bg_image_path = OUTPUT_DIR / "reels_bg.png"
    
    bg_img = Image.new("RGB", (1080, 1920), color=(26, 23, 20))
    draw = ImageDraw.Draw(bg_img)
    
    # 배경 디자인 (그라데이션 대용으로 프레임 그리기)
    draw.rectangle([50, 50, 1030, 1870], outline=(196, 137, 74), width=4)
    if font_path:
        title_font = ImageFont.truetype(font_path, 50)
        cleaned_title = clean_text_for_image(title)
        draw.text((540, 300), cleaned_title, font=title_font, fill=(235, 232, 227), anchor="mm")
        draw.text((540, 1750), "@ai.make.learn", font=ImageFont.truetype(font_path, 30), fill=(90, 143, 110), anchor="mm")
        
    bg_img.save(bg_image_path)
    
    # 4. 이미지 클립을 오디오 길이에 맞추어 비디오 클립으로 변환
    bg_clip = ImageClip(str(bg_image_path)).set_duration(duration)
    
    # 5. 자막(Text) 생성 및 합성
    # MoviePy의 TextClip은 시스템에 ImageMagick이 설치되어 있어야 잘 동작합니다.
    # 만약 설치되어 있지 않을 경우를 대비해, 예외 처리를 하고 자막 없이 배경만 출력되거나,
    # Pillow를 이용해 프레임별로 자막을 합성하는 커스텀 방식을 쓰도록 백업을 둡니다.
    clips = [bg_clip]
    
    try:
        # 문장 개수대로 자막의 표출 시간을 균등 분할
        num_sentences = len(script_lines)
        segment_duration = duration / num_sentences
        
        for idx, line in enumerate(script_lines):
            # 자막 텍스트 클립 생성
            cleaned_line = clean_text_for_image(line)
            txt_clip = TextClip(
                cleaned_line, 
                fontsize=40, 
                color='white', 
                font=font_path if font_path else 'Arial',
                size=(900, None), 
                method='caption'
            )
            txt_clip = txt_clip.set_start(idx * segment_duration)
            txt_clip = txt_clip.set_duration(segment_duration)
            txt_clip = txt_clip.set_position(('center', 960))  # 화면 중앙 하단
            clips.append(txt_clip)
            
        logger.info("MoviePy TextClip 자막 합성 완료.")
    except Exception as e:
        logger.warning(f"MoviePy TextClip 생성 실패(ImageMagick 미설치 등의 이유): {e}")
        logger.info("자막 없이 음성만 포함하여 릴스 비디오를 생성합니다.")
        # 이 경우 대시보드에서 비디오가 생성되지 않는 것을 막기 위해 clips에는 bg_clip만 남겨둡니다.
        clips = [bg_clip]
        
    # 6. 비디오와 오디오 합성
    final_video = CompositeVideoClip(clips).set_audio(audio_clip)
    
    # 코덱 설정
    final_video.write_videofile(
        str(video_output_path),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )
    
    # 리소스 해제
    audio_clip.close()
    final_video.close()
    
    logger.info(f"릴스 비디오 생성 완료: {video_output_path}")
    return str(video_output_path)

# ----------------------------------------------------
# 4. 인스타그램 게시 모듈 (instagrapi)
# ----------------------------------------------------
from instagrapi import Client

def get_instagram_client():
    """인스타그램 클라이언트를 초기화하고 로그인을 수행합니다."""
    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    two_factor_seed = os.getenv("INSTAGRAM_2FA_SEED")
    
    if not username or not password or username == "your_instagram_username" or password == "your_instagram_password":
        raise ValueError("'.env' 파일에 실제 인스타그램 아이디(INSTAGRAM_USERNAME)와 비밀번호(INSTAGRAM_PASSWORD)를 설정해 주세요.")
        
    cl = Client()
    session_file = Path("instagram_session.json")
    
    # 로그인 세션이 존재하면 로드하여 계정 잠김 위험 최소화
    if session_file.exists():
        try:
            cl.load_settings(session_file)
            logger.info("기존 인스타그램 세션 로드 성공.")
        except Exception as e:
            logger.warning(f"세션 로드 실패, 새로 로그인을 시도합니다: {e}")
            
    # 로그인 상태 체크
    session_valid = False
    try:
        cl.get_timeline_feed()
        logger.info("이미 기존 세션으로 로그인되어 있는 상태입니다.")
        session_valid = True
    except Exception:
        logger.info("기존 세션이 만료되어 새로 로그인을 시도합니다.")
        
    if not session_valid:
        try:
            # 2FA 시드가 존재할 경우 OTP 코드 자동 생성 로그인 시도
            if two_factor_seed:
                try:
                    import pyotp
                    totp = pyotp.TOTP(two_factor_seed.replace(" ", ""))
                    otp_code = totp.now()
                    logger.info(f"2단계 인증 OTP 코드를 자동으로 생성하여 로그인합니다: {otp_code}")
                    cl.login(username, password, verification_code=otp_code)
                except ImportError:
                    logger.warning("pyotp 라이브러리가 설치되어 있지 않아 2FA 코드 자동 입력 없이 로그인을 시도합니다.")
                    cl.login(username, password)
            else:
                cl.login(username, password)
                
            cl.dump_settings(session_file)
            logger.info("인스타그램 로그인 성공 및 세션 저장 완료.")
        except Exception as e:
            err_msg = str(e).lower()
            if "challenge_required" in err_msg or "checkpoint_required" in err_msg or "challenge" in err_msg:
                raise ConnectionError(
                    "인스타그램 로그인 차단(Challenge Required) 발생! 인스타그램 공식 앱을 켜서 '본인 로그인 확인'을 직접 눌러주시거나, "
                    "또는 계정의 2단계 인증(2FA) 보안 설정을 마친 후 발급받은 백업 시드를 .env의 INSTAGRAM_2FA_SEED에 등록해 주세요."
                )
            elif "bad_password" in err_msg or "invalid_user" in err_msg:
                raise ConnectionError("비밀번호 또는 아이디가 일치하지 않습니다. .env 설정을 다시 확인해 주세요.")
            else:
                raise ConnectionError(f"인스타그램 로그인 실패: {e}")
            
    return cl

def upload_to_instagram(content_type: str, caption: str, file_paths: list):
    """
    인스타그램에 실제 업로드를 수행합니다.
    content_type: 'feed' 또는 'reels'
    file_paths: 업로드할 파일 경로의 리스트 (피드는 복수 이미지, 릴스는 단일 비디오)
    """
    cl = get_instagram_client()
    if not cl:
        raise ConnectionError("인스타그램 클라이언트를 초기화할 수 없어 업로드에 실패했습니다.")
        
    logger.info(f"인스타그램 업로드 진행 중 ({content_type})...")
    
    if content_type == "feed":
        if len(file_paths) == 1:
            # 단일 이미지 업로드
            media = cl.photo_upload(file_paths[0], caption)
        else:
            # 복수 이미지(슬라이드) 업로드
            media = cl.album_upload(file_paths, caption)
        logger.info(f"피드 게시 완료. Media ID: {media.pk}")
        return media.pk
        
    elif content_type == "reels":
        video_path = file_paths[0]
        # 릴스 업로드
        media = cl.clip_upload(video_path, caption)
        logger.info(f"릴스 게시 완료. Media ID: {media.pk}")
        return media.pk
        
    else:
        raise ValueError(f"지원하지 않는 콘텐츠 타입입니다: {content_type}")

# ----------------------------------------------------
# 5. CLI 실행 진입점 (단독 실행용)
# ----------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python instagram_bot.py [주제] [게시타입: feed/reels/both/none]")
        sys.exit(1)
        
    topic = sys.argv[1]
    publish_type = sys.argv[2] if len(sys.argv) > 2 else "none"
    
    try:
        # 1. 콘텐츠 생성
        content = generate_instagram_content(topic)
        
        # 2. 미디어 제작
        feed_paths = []
        reels_path = None
        
        if publish_type in ["feed", "both", "none"]:
            feed_paths = create_card_news(content["feed"])
            
        if publish_type in ["reels", "both", "none"]:
            reels_path = create_reels_video(content["reels"])
            
        # 3. 인스타그램 게시
        if publish_type != "none":
            if publish_type in ["feed", "both"] and feed_paths:
                caption = f"{content['feed']['caption']}\n\n{content['feed']['hashtags']}"
                upload_to_instagram("feed", caption, feed_paths)
                
            if publish_type in ["reels", "both"] and reels_path:
                caption = f"{content['reels']['caption']}\n\n{content['reels']['hashtags']}"
                upload_to_instagram("reels", caption, [reels_path])
                
        print("\n=== 처리 결과 ===")
        print(f"주제: {topic}")
        print(f"카드뉴스 경로: {feed_paths}")
        print(f"릴스영상 경로: {reels_path}")
        print("성공적으로 작업이 완료되었습니다!")
        
    except Exception as e:
        print(f"\n[오류 발생] {e}")
        sys.exit(1)
