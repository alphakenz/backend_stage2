from PIL import Image, ImageDraw, ImageFont
from typing import List
from datetime import datetime
import os

class SummaryImageGenerator:
    def __init__(self):
        self.cache_dir = "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
    def generate_image(self, total_countries: int, top_countries: List, last_refreshed_at: datetime):
        """Generate summary image with country data"""
        # Create a new image with white background
        width, height = 600, 400
        image = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(image)
        
        # Try to use a nice font, fallback to default
        try:
            title_font = ImageFont.truetype("arial.ttf", 24)
            header_font = ImageFont.truetype("arial.ttf", 18)
            text_font = ImageFont.truetype("arial.ttf", 14)
        except:
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Title
        draw.text((width//2, 30), "Country Data Summary", fill='black', font=title_font, anchor="mm")
        
        # Total countries
        draw.text((50, 80), f"Total Countries: {total_countries:,}", fill='black', font=header_font)
        
        # Top 5 countries by GDP
        draw.text((50, 120), "Top 5 Countries by Estimated GDP:", fill='black', font=header_font)
        
        y_position = 150
        for i, country in enumerate(top_countries[:5]):
            name = country['name']
            gdp = country['estimated_gdp'] or 0
            gdp_text = f"${gdp:,.2f}" if gdp else "N/A"
            draw.text((70, y_position), f"{i+1}. {name}: {gdp_text}", fill='black', font=text_font)
            y_position += 25
        
        # Last refresh timestamp
        refresh_text = f"Last Refreshed: {last_refreshed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
        draw.text((50, height - 50), refresh_text, fill='gray', font=text_font)
        
        # Save image
        image_path = os.path.join(self.cache_dir, "summary.png")
        image.save(image_path)
        return image_path

image_generator = SummaryImageGenerator()