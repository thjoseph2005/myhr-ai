from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/readyz")
async def readiness() -> dict[str, str]:
    return {"status": "ready"}


@router.get("/healthz")
async def healthcheck_compat() -> dict[str, str]:
    return {"status": "ok"}
