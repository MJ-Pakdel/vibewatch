#!/usr/bin/env python3
"""
Convert one sample entry from cleaned Hulu/Disney+ CSV to JSON format.

This script:
1. Loads the cleaned CSV file
2. Takes one sample entry
3. Converts all fields to proper JSON format
4. Saves to a new JSON file
"""

import os
import json
import pandas as pd
from typing import Dict, Any

def convert_sample_to_json(input_file: str, output_file: str, sample_index: int = 0):
    """
    Convert one sample entry from CSV to JSON format.
    
    Args:
        input_file: Path to cleaned CSV file
        output_file: Path to output JSON file
        sample_index: Index of the sample to convert (default: 0)
    """
    print(f"📖 Loading cleaned catalog from {input_file}...")
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Load the CSV file
    df = pd.read_csv(input_file)
    
    if sample_index >= len(df):
        print(f"❌ Sample index {sample_index} is out of range. File has {len(df)} entries.")
        return
    
    print(f"🎬 Converting sample entry at index {sample_index}...")
    
    # Get the sample entry
    sample_entry = df.iloc[sample_index]
    
    # Convert to dictionary
    sample_data = {}
    
    # Process each column
    for column in df.columns:
        value = sample_entry[column]
        
        # Handle NaN values
        if pd.isna(value):
            sample_data[column] = None
            continue
        
        # Handle JSON fields
        json_fields = ['genres', 'spoken_languages', 'production_companies', 
                      'production_countries', 'origin_country', 'languages', 
                      'external_ids', 'keywords', 'watch_providers', 'credits', 
                      'videos', 'images', 'translations', 'release_dates', 
                      'content_ratings']
        
        if column in json_fields and value != '':
            try:
                sample_data[column] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                sample_data[column] = value
        else:
            # Handle numeric fields
            if column in ['tmdb_id', 'vote_count', 'budget', 'revenue']:
                try:
                    sample_data[column] = int(value) if pd.notna(value) else None
                except (ValueError, TypeError):
                    sample_data[column] = value
            elif column in ['runtime', 'episode_run_time', 'popularity', 'vote_average']:
                try:
                    sample_data[column] = float(value) if pd.notna(value) else None
                except (ValueError, TypeError):
                    sample_data[column] = value
            else:
                sample_data[column] = value
    
    # Save to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Sample entry converted and saved to {output_file}")
    print(f"🎬 Title: {sample_data.get('title', 'N/A')}")
    print(f"📊 TMDB ID: {sample_data.get('tmdb_id', 'N/A')}")
    print(f"📺 Service: {sample_data.get('service', 'N/A')}")
    print(f"🎭 Media Type: {sample_data.get('media_type', 'N/A')}")
    
    # Show poster info if available
    if 'images' in sample_data and sample_data['images']:
        try:
            if isinstance(sample_data['images'], str):
                images_data = json.loads(sample_data['images'])
            else:
                images_data = sample_data['images']
            
            if 'posters' in images_data and images_data['posters']:
                poster = images_data['posters'][0]
                print(f"🖼️  Poster: {poster.get('full_url', 'N/A')}")
                print(f"📏 Size: {poster.get('width', 'N/A')}x{poster.get('height', 'N/A')}")
        except:
            print("🖼️  Poster info: Available but could not parse")
    
    print(f"📁 File size: {len(json.dumps(sample_data, indent=2))} characters")

def main():
    """Main function to run the conversion."""
    input_file = "data/hulu_disneyplus_us_cleaned.csv"
    output_file = "sample_hulu_disneyplus_cleaned.json"
    
    # Convert the first sample (index 0)
    convert_sample_to_json(input_file, output_file, sample_index=0)
    
    print(f"\n🎉 Conversion complete!")
    print(f"📁 Input: {input_file}")
    print(f"📁 Output: {output_file}")

if __name__ == "__main__":
    main() 