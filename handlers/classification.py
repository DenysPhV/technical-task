def classify_region(city):
    """
    Classify city by its geographic region.
    """
    region_mapping = {
        "Europe": ["Kyiv", "London", "Paris"],
        "Asia": ["Tokyo", "Beijing", "Seoul"],
        "America": ["New York", "Los Angeles", "Chicago"],
    }
    for region, cities in region_mapping.items():
        if city in cities:
            return region
    return "Other"