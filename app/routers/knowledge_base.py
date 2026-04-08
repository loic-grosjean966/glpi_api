from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from app.dependencies import get_current_user, get_glpi_client
from app.core.glpi_client import GLPIClient

router = APIRouter(prefix="/kb", tags=["Base de connaissances"])

# ------------------------------------------------------------------ #
#  Schemas                                                             #
# ------------------------------------------------------------------ #

class KnowledgeBaseCategory(BaseModel):
    id: int = Field(..., description="ID de la catégorie dans GLPI")
    name: str = Field(..., description="Nom de la catégorie")
    knowbaseitemcategories_id: int | None = Field(default=None, description="ID de la catégorie parente (null si catégorie racine)")
    comment: str | None = Field(default=None, description="Commentaire de la catégorie")

class KnowledgeBaseArticle(BaseModel):
    id: int = Field(..., description="ID de l'article dans GLPI")
    name: str = Field(..., description="Titre de l'article")
    answer: str = Field(..., description="Contenu détaillé de l'article")
    is_faq: bool = Field(..., description="Indique si l'article est marqué comme FAQ")
    knowbaseitemcategories_id: int = Field(..., description="ID de la catégorie de l'article dans GLPI")
    begin_date: str | None = Field(default=None, description="Date de début de validité de l'article (format ISO 8601)")
    end_date: str | None = Field(default=None, description="Date de fin de validité de l'article (format ISO 8601)")

@router.get("/", response_model=list[KnowledgeBaseArticle])
async def list_kb_articles(
    glpi: GLPIClient = Depends(get_glpi_client),
    current_user: dict = Depends(get_current_user),
    category_id: int | None = Query(default=None, description="Filtrer par ID de catégorie"),
    is_faq: bool | None = Query(default=None, description="Filtrer par statut FAQ (`true` ou `false`)"),
):
    """Liste les articles de la base de connaissances, avec possibilité de filtrer par catégorie ou statut FAQ."""
    params = {}
    if category_id is not None:
        params["knowbaseitemcategories_id"] = category_id
    if is_faq is not None:
        params["is_faq"] = int(is_faq)  # GLPI attend 0 ou 1
    items = await glpi.get_knowbase_items(**params)
    return [KnowledgeBaseArticle(**item) for item in items]

@router.get("/faq", response_model=list[KnowledgeBaseArticle])
async def list_faqs(
    glpi: GLPIClient = Depends(get_glpi_client),
    current_user: dict = Depends(get_current_user),
):
    """Liste les articles de la base de connaissances marqués comme FAQ."""
    items = await glpi.get_knowbase_items(is_faq=1)
    return [KnowledgeBaseArticle(**item) for item in items]

@router.get("/search", response_model=list[KnowledgeBaseArticle])
async def search_kb_articles(
    glpi: GLPIClient = Depends(get_glpi_client),
    current_user: dict = Depends(get_current_user),
    q: str = Query(..., description="Terme de recherche"),
):
    """Recherche des articles dans la base de connaissances."""
    result = await glpi.search_knowbase(q)
    return [KnowledgeBaseArticle(**item) for item in result.get("data", [])]

@router.get("/categories", response_model=list[KnowledgeBaseCategory])
async def list_kb_categories(
    glpi: GLPIClient = Depends(get_glpi_client),
    current_user: dict = Depends(get_current_user),
):
    """Liste les catégories de la base de connaissances."""
    categories = await glpi.get_knowbase_categories()
    return categories

@router.get("/{item_id}", response_model=KnowledgeBaseArticle)
async def get_kb_article(
    item_id: int,
    glpi: GLPIClient = Depends(get_glpi_client),
    current_user: dict = Depends(get_current_user),
):
    """Récupère les détails d'un article de la base de connaissances par son ID."""
    item = await glpi.get_knowbase_item(item_id)
    return KnowledgeBaseArticle(**item)