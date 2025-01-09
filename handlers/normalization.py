def normalize_city_name(city):
    """
    Normalize and correct city names to a standard format.
    """
    corrections = {
        "Киев": "Kyiv",
        "Londn": "London",
        "Токио": "Tokyo"
    }
    return corrections.get(city, city)