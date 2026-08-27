from starlette.middleware.cors import CORSMiddleware

class CORSMiddlewareWrapper(CORSMiddleware):
    def __init__(self, app):
        super().__init__(
            app,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["GET","POST","PUT","PATCH","DELETE","OPTIONS"],
            allow_headers=["Authorization","Content-Type","X-Request-ID"]
        )