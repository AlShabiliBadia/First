"""CSS Selectors for Mostaql website scraping.

Centralizes all selectors for easy maintenance when the website structure changes.
"""


class Selectors:
    """CSS selectors for Mostaql.com job pages."""
    
    # Job listing page selectors
    PROJECT_ROW = "tr.project-row"
    PROJECT_TITLE_LINK = "h2 a"
    
    # Job detail page selectors
    PAGE_TITLE = ".page-title h1"
    PROJECT_DETAILS_TAB = "#projectDetailsTab .text-wrapper-div"
    PROJECT_META_PANEL = "#project-meta-panel-panel"
    
    # Meta panel selectors
    DATE_PUBLISHED_ROW = ".meta-row"
    DATE_PUBLISHED_TEXT = "تاريخ النشر"  # Arabic: "Date Published"
    META_VALUE_TIME = ".meta-value time"
    BUDGET_SELECTOR = '[data-type="project-budget_range"]'
    DURATION_TEXT = "مدة التنفيذ"  # Arabic: "Execution Duration"
    META_VALUE = ".meta-value"
    
    # Owner selectors
    PROFILE_DETAILS = ".profile-details"
    OWNER_NAME = "h5"
    OWNER_TABLE = ".table tr"
    
    # Bid selector
    BID = ".bid"
    
    # URL patterns
    BASE_URL = "https://mostaql.com/projects"
    PROJECT_URL_TEMPLATE = "?category={category}&sort=latest&page=1"
    
    @classmethod
    def get_category_url(cls, category: str) -> str:
        """Generate the URL for a specific category page."""
        return f"{cls.BASE_URL}{cls.PROJECT_URL_TEMPLATE.format(category=category)}"
