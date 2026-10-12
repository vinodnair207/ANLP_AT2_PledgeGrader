"""HTTP API for the React frontend: wraps the same code paths as src.main.

Run from the repo root:  uv run uvicorn src.api:app --reload
Interactive docs:        http://localhost:8000/docs

When frontend/dist exists (after npm run build), the same server also serves the web app,
so the browser and the API share one address and no cross origin setting is needed.
"""
import json
import logging
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src import model, utils
from src.grading import METHOD_NAMES, grade_pledge, validate_text

logger = logging.getLogger(__name__)

# Keep in sync with the --method choices in src/main.py.
METHODS = ("rules", "climatebert", "llm")

# Holds the configuration and each method that loaded. A method that failed to load is absent.
state: dict = {"cfg": None, "arms": {}}
_arms_lock = threading.Lock()


def load_arm(method: str):
    """Builds one method and stores it, or logs the reason and returns None when it cannot load.

    The LLM arm is built in live mode, so it answers or fails within seconds instead of
    waiting out rate limits like the evaluation runs do.
    """
    try:
        arm = model.get_arms(state["cfg"], (method,), live=True).get(method)
    except Exception:
        logger.exception("Method %s could not be loaded", method)
        return None
    if arm is not None:
        state["arms"][method] = arm
    return arm


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Same setup as main(): logging, config and seed, then loads every method once at startup.

    A method that fails to load (for example a missing GEMINI_API_KEY) does not stop the app.
    The response then carries a warning and the remaining methods still grade the pledge.
    """
    utils.setup_logging()
    cfg = utils.load_config()
    utils.set_seed(cfg["seed"])
    state["cfg"] = cfg
    with _arms_lock:
        for method in METHODS:
            load_arm(method)
    logger.info("Methods ready: %s", list(state["arms"]))
    yield


app = FastAPI(title="PledgeGrader API", lifespan=lifespan)

# Only needed for local development, where the Vite server runs on its own port.
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_arm(method: str):
    """Returns a loaded method, so requests do not reload models."""
    if method not in METHODS:
        raise HTTPException(400, f"Unknown method '{method}'. Choose from {list(METHODS)}.")
    with _arms_lock:
        arm = state["arms"].get(method)
    if arm is None:
        raise HTTPException(503, f"Method '{method}' is not available right now.")
    return arm


def to_jsonable(obj):
    """Converts numpy scalars/arrays (common in model outputs) into plain Python types."""
    return json.loads(json.dumps(obj, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))


class PredictIn(BaseModel):
    text: str = Field(min_length=1)
    method: str = "rules"


class TextIn(BaseModel):
    text: str


@app.get("/api/health")
def health():
    """Reports that the server is running and which methods loaded."""
    return {"status": "ok", "methods": list(state["arms"])}


@app.get("/api/methods")
def methods():
    """Methods and class labels, so the frontend can build its dropdown and legend."""
    return {"methods": list(METHODS), "labels": list(state["cfg"]["labels"].values())}


@app.post("/api/predict")
def predict(body: PredictIn):
    """Classifies one piece of text with the chosen method."""
    arm = get_arm(body.method)
    try:
        result = arm.predict(body.text)
    except Exception:
        logger.exception("Prediction failed")
        raise HTTPException(500, "Prediction failed, see server logs.")
    return {"method": body.method, **to_jsonable(result)}


@app.get("/api/metrics/{method}")
def saved_metrics(method: str):
    """Returns metrics saved by a previous evaluation run, without recomputing."""
    if method not in METHODS:
        raise HTTPException(400, f"Unknown method '{method}'.")
    path = Path(state["cfg"]["paths"]["predictions_dir"]) / f"{method}_metrics.json"
    if not path.exists():
        raise HTTPException(404, f"No saved metrics for '{method}'. Run the evaluation first.")
    return json.loads(path.read_text(encoding="utf8"))


@app.post("/api/grade")
def grade(body: TextIn):
    """Grades one pledge with every loaded method and returns the score, checks and explanations."""
    try:
        validate_text(body.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    with _arms_lock:
        arms = dict(state["arms"])
    try:
        result = grade_pledge(body.text.strip(), arms, state["cfg"])
    except RuntimeError as exc:
        logger.error("Grading failed: %s", exc)
        raise HTTPException(status_code=503, detail="No method could grade this pledge. Please try again later.")

    # Adds a warning for each method that never loaded, so the screen explains the missing card.
    for method in METHODS:
        if method not in arms:
            result["warnings"].append(
                f"{METHOD_NAMES[method]} is unavailable right now, so the result uses the other methods.")
    return result


# Serves the built web app, if present. Mounted last so that the /api routes take priority.
_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if _dist.is_dir():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="frontend")
