from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Somincola News Center")


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Somincola News Center</title>
        <meta charset="utf-8">
    </head>
    <body>
        <h1>Somincola News Center</h1>
        <p>Welcome to Somincola News Center</p>
    </body>
    </html>
    """

