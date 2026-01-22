from fastapi import APIRouter
from app.glpi.client import GLPIClient

router = APIRouter(prefix="/glpi", tags=["GLPI"])

@router.get("/test")
def test_glpi_connection():
    client = GLPIClient()
    session = client.init_session()
    profile = client.get_my_profile()

    return {
        "session": session,
        "profile": profile
    }
    try:
        items = client.get_items("Computer")
        return {"status": "success", "data": items}
    except Exception as e:
        return {"status": "error", "message": str(e)}