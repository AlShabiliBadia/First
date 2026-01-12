from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def setup_cors(app: FastAPI) -> None:
    """
    configure CORS middleware
    """

    origins = [
        "http://localhost:3000",
        "https://first.alshabili.site",
        "https://www.first.alshabili.site",
        "https://id-preview--ec733999-017a-435b-85d1-f4b0eec70b6f.lovable.app",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
