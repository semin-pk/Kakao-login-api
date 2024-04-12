from fastapi import FastAPI, Depends, Request
import urllib.parse
import requests
from datetime import datetime, timedelta
from fastapi.responses import RedirectResponse
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your_secret_key")
CLIENT_ID = "faa3869240e454c8a6be06fbc2974992"
CLIENT_SECRET = "Uy7PmKr8QOtG8PsC41i7G7PAo8GX6x96"
REDIRECT_URI = 'http://localhost:8000/callback'

AUTH_URL = 'https://kauth.kakao.com/oauth/authorize'
TOKEN_URL = 'https://kauth.kakao.com/oauth/token'
API_BASE_URL = 'https://kapi.kakao.com/v2/user/me'

@app.get('/')
async def login():

    params = {
        'client_id' : CLIENT_ID,
        'response_type' : 'code',
        'redirect_uri' : REDIRECT_URI

    } 

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return RedirectResponse(auth_url)

@app.get('/callback')
async def callback(request: Request):
    session = request.session
    if 'error' in request.query_params:
        return JSONResponse({"error": request.query_params['error']})
    if 'code' in request.query_params:
        req_body = {
            'code': request.query_params['code'],
            'grant_type': 'authorization_code',
            'redirect_uri':REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        headers = {
            'Content-type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        response = requests.post(TOKEN_URL, data=req_body, headers=headers)
        token_info = response.json()
        if 'access_token' not in token_info:
            return JSONResponse({"error": "Access token not found in response"})
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        return RedirectResponse('/me')

@app.get('/me')
async def get_playlist(request: Request):
    session = request.session
    if 'access_token' not in session:
        return RedirectResponse('login')
    if datetime.now().timestamp() > session['expires_at']:
        return RedirectResponse('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL, headers=headers)
    playlist = response.json()
    return JSONResponse(playlist)

@app.get('/refresh-token')
def refresh_token(request: Request):
    session = request.session
    if 'refresh_token' not in session:
        return RedirectResponse('/login')
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        response = requests.post(TOKEN_URL, data=req_body)
        new_token_info = response.json()

        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return RedirectResponse('/me')
