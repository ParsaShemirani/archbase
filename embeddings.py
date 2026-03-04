from pathlib import Path
from typing_extensions import Annotated

from sqlalchemy import select
from tabulate import tabulate
import typer
import requests

from env_vars import EMBEDDINGS_PATH
from connection import Session
from models import File, Bundle, Tag
from vector_math import cosine_similarity

# 1. Centralized Configuration Map
# This maps our file prefixes to their respective database models and display names.
TARGETS = {
    "f": {"model": File, "name": "File"},
    "b": {"model": Bundle, "name": "Bundle"},
    "t": {"model": Tag, "name": "Tag"},
}

def get_sorted_files(dir_path: Path) -> list[Path]:
    """Returns a sorted list of files, or an empty list if none exist."""
    return sorted(
        [f for f in dir_path.glob("*") if not f.name.startswith(".") and f.is_file()]
    )

def generate_embedding(text: str) -> list[float]:
    """Hits the local embedding server to generate a vector."""
    response = requests.post(
        "http://127.0.0.1:8000/embed",
        json={"text": text}
    )
    response.raise_for_status()
    return response.json()['embedding']

def update_embeddings() -> None:
    """Generates missing CSV embeddings for Files, Bundles, and Tags."""
    embedding_paths = get_sorted_files(EMBEDDINGS_PATH)
    
    with Session() as session:
        for prefix, config in TARGETS.items():
            model = config["model"]
            display_name = config["name"]
            
            # Find IDs that already have a CSV file generated
            existing_ids = {
                int(ep.stem[1:]) for ep in embedding_paths if ep.name.startswith(prefix)
            }
            
            # Query all records for this model
            records = session.scalars(select(model)).all()
            
            for record in records:
                if record.id not in existing_ids and record.description:
                    embedding = generate_embedding(record.description)
                    csv_embedding = ",".join(str(x) for x in embedding)
                    
                    output_file_path = EMBEDDINGS_PATH / f"{prefix}{record.id}.csv"
                    output_file_path.write_text(csv_embedding)
                    
                    print(f"Completed {display_name}: ID {record.id}")

def searcher() -> None:
    """Searches embeddings and returns the top 3 closest matches."""
    search_text = input("\nEnter the search text: ").strip()
    if not search_text:
        print("Search text cannot be empty.")
        return

    print("Searching...")
    search_embedding = generate_embedding(search_text)
    embedding_paths = get_sorted_files(EMBEDDINGS_PATH)
    
    similarities = []
    
    # Step 1: Calculate similarities purely from local files (No DB queries here!)
    for ep in embedding_paths:
        prefix = ep.name[0]
        if prefix not in TARGETS:
            continue # Skip unknown files
            
        record_id = int(ep.stem[1:])
        saved_embedding = [float(x) for x in ep.read_text().split(",")]
        
        sim_score = cosine_similarity(search_embedding, saved_embedding)
        similarities.append((sim_score, prefix, record_id))
            
    # Step 2: Sort and grab only the top 3 matches
    top_matches = sorted(similarities, key=lambda x: x[0], reverse=True)[:3]
    
    # Step 3: Fetch descriptions from the DB for ONLY the top 3 results
    results_for_display = []
    with Session() as session:
        for sim_score, prefix, record_id in top_matches:
            model = TARGETS[prefix]["model"]
            display_name = TARGETS[prefix]["name"]
            
            record = session.scalar(select(model).where(model.id == record_id))
            if record:
                results_for_display.append(
                    (display_name, record.id, round(sim_score, 4), record.description)
                )
                
    # Step 4: Output to terminal
    print("\n" + tabulate(
        results_for_display, 
        headers=["Type", "ID", "Similarity Score", "Description"], 
        tablefmt="grid", 
        maxcolwidths=[None, None, None, 50]
    ))

def main(
    update: Annotated[bool, typer.Option("--update", "-u", help="Generate missing embeddings")] = False,
    search: Annotated[bool, typer.Option("--search", "-s", help="Search existing embeddings")] = False
):
    if not update and not search:
        print("Please provide an argument: --update or --search")
        raise typer.Exit()

    if update:
        update_embeddings()

    if search:
        searcher()

if __name__ == "__main__":
    typer.run(main)