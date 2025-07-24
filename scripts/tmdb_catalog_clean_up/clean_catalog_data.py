#!/usr/bin/env python3
"""
Clean up Hulu/Disney+ catalog CSV file by filtering images.

This script:
1. Loads the original CSV file
2. Filters images to only keep posters
3. For each poster section, keeps only top 5 English ones
4. Adds full URLs to the metadata
5. Saves a cleaned version
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List

# TMDB image base URL
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

def clean_images_data(images_json: str, tmdb_id: int = None) -> Dict[str, Any]:
    """
    Clean images data to only keep top 5 English posters with full URLs.
    
    Args:
        images_json: JSON string containing images data
        
    Returns:
        Cleaned images dictionary
    """
    if not images_json or pd.isna(images_json):
        return {}
    
    try:
        images_data = json.loads(images_json)
    except (json.JSONDecodeError, TypeError):
        return {}
    
    cleaned_images = {}
    
    # Only process posters
    if 'posters' in images_data:
        posters = images_data['posters']
        
        # Filter for English posters and sort by popularity (vote_average)
        english_posters = []
        for poster in posters:
            # Check if it's English (iso_639_1 == 'en' or language == 'en')
            if (poster.get('iso_639_1') == 'en' or 
                poster.get('language') == 'en' or
                poster.get('iso_639_1') is None):  # Some posters don't have language specified
                english_posters.append(poster)
        
        # Sort by vote_average (popularity) in descending order
        english_posters.sort(key=lambda x: x.get('vote_average', 0), reverse=True)
        
        # Take top 1
        top_1_poster = english_posters[:1]
        
        # Add full URLs and tmdb_id to each poster, remove file_path
        for poster in top_1_poster:
            if poster.get('file_path'):
                poster['full_url'] = TMDB_IMAGE_BASE + poster['file_path']
                poster['tmdb_id'] = int(tmdb_id) if tmdb_id is not None else None  # Add tmdb_id to poster
                poster.pop('file_path', None)  # Remove file_path
        
        cleaned_images['posters'] = top_1_poster
    
    return cleaned_images

def clean_catalog_file(input_file: str, output_file: str):
    """
    Clean the entire catalog file by processing all rows.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
    """
    print(f"📖 Loading catalog from {input_file}...")
    df = pd.read_csv(input_file)
    
    # Remove specified columns
    columns_to_remove = [
        'status', 'spoken_languages', 'production_companies', 'production_countries', 
        'languages', 'watch_providers', 'credits', 'videos', 'translations', 'release_dates',
        'external_ids', 'homepage', 'in_production'
    ]
    
    for col in columns_to_remove:
        if col in df.columns:
            df = df.drop(columns=[col])
            print(f"🗑️  Removed column: {col}")
    
    print(f"🧹 Cleaning images for {len(df)} entries...")
    
    # Process images column
    cleaned_images = []
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"   Processed {idx}/{len(df)} entries...")
        
        cleaned_img = clean_images_data(row['images'], row['tmdb_id'])
        cleaned_images.append(json.dumps(cleaned_img, ensure_ascii=False))
    
    # Replace the images column
    df['images'] = cleaned_images
    
    print(f"💾 Saving cleaned catalog to {output_file}...")
    df.to_csv(output_file, index=False)
    
    print(f"✅ Cleaned catalog saved! {len(df)} entries processed.")
    
    # Print some statistics
    total_posters = 0
    for img_json in cleaned_images:
        try:
            img_data = json.loads(img_json)
            if 'posters' in img_data:
                total_posters += len(img_data['posters'])
        except:
            pass
    
    print(f"📊 Statistics:")
    print(f"   - Total entries: {len(df)}")
    print(f"   - Total posters kept: {total_posters}")
    print(f"   - Average posters per entry: {total_posters/len(df):.1f}")
    print(f"   - Note: Only top 1 poster per entry kept")

def create_sample_entry(input_file: str, output_file: str):
    """
    Create a sample cleaned entry for inspection.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output JSON file
    """
    print(f"🎬 Creating sample entry from {input_file}...")
    
    # Load first entry
    df = pd.read_csv(input_file)
    first_entry = df.iloc[0]
    
    # Clean the images
    cleaned_images = clean_images_data(first_entry['images'], first_entry['tmdb_id'])
    
    # Create sample data
    sample_data = {
        'service': first_entry['service'],
        'media_type': first_entry['media_type'],
        'tmdb_id': int(first_entry['tmdb_id']),
        'title': first_entry['title'],
        'original_title': first_entry['original_title'],
        'overview': first_entry['overview'],
        'tagline': first_entry['tagline'],
        'release_date': first_entry['release_date'],
        'runtime': float(first_entry['runtime']) if pd.notna(first_entry['runtime']) else None,
        'original_language': first_entry['original_language'],
        'popularity': float(first_entry['popularity']) if pd.notna(first_entry['popularity']) else None,
        'vote_average': float(first_entry['vote_average']) if pd.notna(first_entry['vote_average']) else None,
        'vote_count': int(first_entry['vote_count']) if pd.notna(first_entry['vote_count']) else None,
        'images': cleaned_images
    }
    
    # Parse other JSON fields for completeness
    json_fields = ['genres']
    for field in json_fields:
        if pd.notna(first_entry[field]) and first_entry[field] != '':
            try:
                sample_data[field] = json.loads(first_entry[field])
            except:
                sample_data[field] = first_entry[field]
        else:
            sample_data[field] = None
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sample cleaned entry saved to {output_file}")
    print(f"🎬 Movie: {sample_data['title']}")
    print(f"📊 TMDB ID: {sample_data['tmdb_id']}")
    print(f"🖼️  Posters kept: {len(cleaned_images.get('posters', []))} (top 1 only)")

def main():
    """Main function to run the cleaning process."""
    input_file = "data/hulu_disneyplus_us.csv"
    cleaned_file = "data/hulu_disneyplus_us_cleaned.csv"
    sample_file = "sample_cleaned_movie_entry.json"
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    print("🧹 Hulu/Disney+ Catalog Cleaner")
    print("=" * 40)
    
    # Create sample entry first
    create_sample_entry(input_file, sample_file)
    
    print("\n" + "=" * 40)
    
    # Clean the entire file
    clean_catalog_file(input_file, cleaned_file)
    
    print("\n🎉 Cleaning complete!")
    print(f"📁 Original file: {input_file}")
    print(f"📁 Cleaned file: {cleaned_file}")
    print(f"📁 Sample entry: {sample_file}")

if __name__ == "__main__":
    main() 