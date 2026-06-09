import os
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import instagram_bot

app = FastAPI(title="Instagram Content Auto Studio")

# 아웃풋 폴더 마운트 (생성된 카드뉴스 및 릴스를 브라우저에 표시하기 위함)
output_dir = "output"
os.makedirs(output_dir, exist_ok=True)
app.mount("/output", StaticFiles(directory=output_dir), name="output")

# 임시 메모리 저장소 (생성된 콘텐츠 저장용)
generated_cache = {}

class GenerateRequest(BaseModel):
    topic: str

class PublishRequest(BaseModel):
    content_type: str # 'feed' 또는 'reels'
    caption: str
    file_paths: list

@app.get("/", response_class=HTMLResponse)
def read_root():
    """메인 HTML 대시보드 페이지를 반환합니다."""
    # 단일 파일 구성을 위해 dashboard.html을 로드하여 응답
    html_path = "dashboard.html"
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=404, detail="dashboard.html 파일을 찾을 수 없습니다.")

@app.post("/api/generate")
def api_generate(req: GenerateRequest):
    """주제를 받아 AI 텍스트 생성, 카드뉴스 생성, 릴스 영상 제작을 한 번에 처리합니다."""
    if not req.topic.strip():
        raise HTTPException(status_code=400, detail="주제를 입력해 주세요.")
        
    try:
        # 1. AI 콘텐츠 생성
        content = instagram_bot.generate_instagram_content(req.topic)
        
        # 2. 미디어 파일 생성 (로컬 output 디렉토리에 저장)
        feed_paths = instagram_bot.create_card_news(content["feed"])
        
        reels_path = None
        try:
            reels_path = instagram_bot.create_reels_video(content["reels"])
        except Exception as video_err:
            instagram_bot.logger.error(f"릴스 영상 생성 중 오류(일부 자막 라이브러리 부재 등): {video_err}")
            # 비디오 생성 실패하더라도 카드뉴스 성공 시 진행할 수 있도록 처리
            
        # 브라우저 전송을 위해 상대 경로로 변환
        relative_feed_paths = [os.path.basename(p) for p in feed_paths]
        relative_reels_path = os.path.basename(reels_path) if reels_path else None
        
        result = {
            "topic": req.topic,
            "feed": {
                "title": content["feed"]["title"],
                "cards": content["feed"]["cards"],
                "caption": content["feed"]["caption"],
                "hashtags": content["feed"]["hashtags"],
                "images": relative_feed_paths,
                "absolute_images": feed_paths
            },
            "reels": {
                "title": content["reels"]["title"],
                "script": content["reels"]["script"],
                "caption": content["reels"]["caption"],
                "hashtags": content["reels"]["hashtags"],
                "video": relative_reels_path,
                "absolute_video": reels_path
            }
        }
        
        # 임시 캐시에 저장 (업로드 시 참조하기 위함)
        generated_cache["current"] = result
        return result
        
    except Exception as e:
        instagram_bot.logger.exception("콘텐츠 생성 오류 발생")
        raise HTTPException(status_code=500, detail=f"생성 실패: {str(e)}")

@app.post("/api/publish")
def api_publish(req: PublishRequest):
    """지정된 콘텐츠를 사용자의 인스타그램 계정으로 즉시 업로드합니다."""
    try:
        # 환경 변수 유효성 체크
        username = os.getenv("INSTAGRAM_USERNAME")
        password = os.getenv("INSTAGRAM_PASSWORD")
        if not username or not password:
            raise HTTPException(
                status_code=400, 
                detail=".env 파일에 INSTAGRAM_USERNAME 및 INSTAGRAM_PASSWORD가 설정되어 있지 않습니다."
            )
            
        # 실제 미디어 파일 목록 및 캡션 매핑
        media_id = instagram_bot.upload_to_instagram(
            content_type=req.content_type,
            caption=req.caption,
            file_paths=req.file_paths
        )
        return {"status": "success", "media_id": media_id}
    except Exception as e:
        instagram_bot.logger.exception("인스타그램 업로드 오류 발생")
        raise HTTPException(status_code=500, detail=f"업로드 실패: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"인스타그램 자동화 스튜디오 대시보드가 http://{host}:{port} 에서 실행됩니다.")
    uvicorn.run("dashboard:app", host=host, port=port, reload=True)
