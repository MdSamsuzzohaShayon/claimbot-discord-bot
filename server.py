from fastapi import FastAPI, Request, status

from routers.webhookListenerRouter import router as webhookRouter

app = FastAPI(debug=True)


@app.get('/api')
def api_root(request: Request):
    return {"detail": "API is working"}


# Create route
app.include_router(webhookRouter, prefix="/api/webhook", tags=['Webhook'])
