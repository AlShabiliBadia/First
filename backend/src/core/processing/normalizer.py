"""Data normalization utilities for scraped job data."""

import re
from typing import Dict, List, Optional
from datetime import datetime


# Arabic month name mappings
ARABIC_MONTHS: Dict[str, str] = {
    "يناير": "01", "فبراير": "02", "مارس": "03", "أبريل": "04",
    "مايو": "05", "يونيو": "06", "يوليو": "07", "أغسطس": "08",
    "سبتمبر": "09", "أكتوبر": "10", "نوفمبر": "11", "ديسمبر": "12"
}


def parse_arabic_date(date_str: Optional[str]) -> Optional[datetime]:
    """
    Parse an Arabic date string to a datetime object.
    
    Args:
        date_str: Date string in Arabic format (e.g., "15 يناير 2024").
        
    Returns:
        Parsed datetime object, or None if parsing fails.
    """
    if not isinstance(date_str, str):
        return None
        
    for arabic_month, month_num in ARABIC_MONTHS.items():
        if arabic_month in date_str:
            date_str = date_str.replace(arabic_month, month_num)
            break
    
    try:
        return datetime.strptime(date_str, "%d %m %Y")
    except ValueError:
        return None


def clean_duration(duration_str: Optional[str]) -> str:
    """
    Extract and format duration from Arabic duration string.
    
    Args:
        duration_str: Duration string potentially containing Arabic text.
        
    Returns:
        Cleaned duration string (e.g., "5 Days" or "1 Day").
    """
    if not isinstance(duration_str, str):
        return "0 Days"
        
    match = re.search(r"\d+", duration_str)
    days = int(match.group()) if match else 0

    if days == 1:
        return "1 Day"
    return f"{days} Days"


async def normalize_data(
    data: Dict[str, List[Dict[str, str]]]
) -> Dict[str, List[Dict[str, str]]]:
    """
    Normalize scraped job data.
    
    Processes dates and durations into standardized formats.
    
    Args:
        data: Dictionary mapping categories to lists of job dictionaries.
        
    Returns:
        Normalized data in the same structure.
    """
    payload: Dict[str, List[Dict[str, str]]] = {}

    for category, projects in data.items():
        payload[category] = []
        
        for project in projects:
            # Normalize date
            parsed_date = parse_arabic_date(project.get("project_date_published"))
            project["project_date_published"] = (
                parsed_date.isoformat() if parsed_date else project.get("project_date_published", "N/A")
            )
            
            # Normalize duration
            project["project_duration"] = clean_duration(project.get("project_duration"))
            
            payload[category].append(project)

    return payload
