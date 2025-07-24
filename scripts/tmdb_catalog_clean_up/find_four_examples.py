#!/usr/bin/env python3
"""
Find 4 examples from cleaned Hulu/Disney+ catalog:
1. Disney+ movie
2. Disney+ TV
3. Hulu movie
4. Hulu TV

This script:
1. Loads the cleaned CSV file
2. Finds one example for each service/media_type combination
3. Converts them to JSON format
4. Saves all 4 examples to a new file
"""

import os
import json
import pandas as pd
from typing import Dict, Any, List

def convert_entry_to_json(entry) -> Dict[str, Any]:
    """
    Convert a pandas Series entry to JSON format.
    
    Args:
        entry: Pandas Series containing the entry data
        
    Returns:
        Dictionary with properly formatted JSON data
    """
    sample_data = {}
    
    # Process each column
    for column in entry.index:
        value = entry[column]
        
        # Handle NaN values
        if pd.isna(value):
            sample_data[column] = None
            continue
        
        # Handle JSON fields
        json_fields = ['genres', 'keywords', 'images', 'content_ratings']
        
        if column in json_fields and value != '':
            try:
                sample_data[column] = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                sample_data[column] = value
        else:
            # Handle numeric fields
            if column in ['tmdb_id', 'vote_count', 'budget', 'revenue', 'number_of_seasons', 'number_of_episodes']:
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
    
    return sample_data

def find_four_examples(input_file: str, output_file: str):
    """
    Find 4 examples (one for each service/media_type combination) and save to JSON.
    
    Args:
        input_file: Path to cleaned CSV file
        output_file: Path to output JSON file
    """
    print(f"📖 Loading cleaned catalog from {input_file}...")
    
    # Check if file exists
    if not os.path.exists(input_file):
        print(f"❌ Input file not found: {input_file}")
        return
    
    # Load the CSV file
    df = pd.read_csv(input_file)
    
    print(f"🔍 Finding examples for each service/media_type combination...")
    
    # Define the combinations we want to find
    combinations = [
        ('Disney+', 'movie'),
        ('Disney+', 'tv'),
        ('Hulu', 'movie'),
        ('Hulu', 'tv')
    ]
    
    examples = {}
    
    for service, media_type in combinations:
        # Filter for the specific combination
        filtered_df = df[(df['service'] == service) & (df['media_type'] == media_type)]
        
        if len(filtered_df) > 0:
            # Take the first example
            example_entry = filtered_df.iloc[0]
            example_data = convert_entry_to_json(example_entry)
            
            key = f"{service}_{media_type}"
            examples[key] = example_data
            
            print(f"✅ Found {service} {media_type}: {example_data.get('title', 'N/A')}")
        else:
            print(f"❌ No examples found for {service} {media_type}")
    
    # Save all examples to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(examples, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ All examples saved to {output_file}")
    print(f"📊 Total examples found: {len(examples)}")
    
    # Print summary of each example
    print(f"\n📋 EXAMPLES SUMMARY:")
    print("=" * 50)
    for key, data in examples.items():
        service, media_type = key.split('_')
        title = data.get('title', 'N/A')
        tmdb_id = data.get('tmdb_id', 'N/A')
        vote_avg = data.get('vote_average', 'N/A')
        
        print(f"🎬 {service} {media_type.upper()}:")
        print(f"   Title: {title}")
        print(f"   TMDB ID: {tmdb_id}")
        print(f"   Rating: {vote_avg}/10")
        
        # Show poster info if available
        if 'images' in data and data['images']:
            try:
                if isinstance(data['images'], str):
                    images_data = json.loads(data['images'])
                else:
                    images_data = data['images']
                
                if 'posters' in images_data and images_data['posters']:
                    poster = images_data['posters'][0]
                    print(f"   Poster: {poster.get('full_url', 'N/A')}")
            except:
                print(f"   Poster: Available")
        
        print()

def main():
    """Main function to run the example finding process."""
    input_file = "data/hulu_disneyplus_us_cleaned.csv"
    output_file = "four_examples.json"
    
    # Find the four examples
    find_four_examples(input_file, output_file)
    
    print(f"🎉 Process complete!")
    print(f"📁 Input: {input_file}")
    print(f"📁 Output: {output_file}")

if __name__ == "__main__":
    main() 