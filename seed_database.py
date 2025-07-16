# seed_database.py
import os
import time
from typing import Tuple, Optional

import pandas as pd
from faker import Faker
from decouple import config
from supabase import create_client, Client
from postgrest import APIResponse
from storage3.utils import StorageException

# --- 1. Constants ---
DATASET_FOLDER: str = "ResumeDataset"
CSV_FILENAME: str = "Resume.csv"
PDF_BASE_FOLDER: str = "data"
STORAGE_BUCKET: str = "cv-pdfs"
BATCH_SIZE: int = 100  # Process 100 records at a time


def initialize_clients() -> Tuple[Client, Faker]:
    """Initializes and returns the Supabase and Faker clients."""
    try:
        url: str = config("SUPABASE_URL")
        key: str = config("SUPABASE_SERVICE_KEY")
        supabase: Client = create_client(url, key)
        faker: Faker = Faker()
        print("Supabase client and Faker initialized.")
        return supabase, faker
    except Exception as e:
        print(f"CRITICAL: Error initializing clients: {e}")
        exit(1)


def clear_storage_bucket(supabase: Client):
    """Deletes all files currently in the specified storage bucket."""
    print("\n--- Clearing Storage Bucket ---")
    try:
        files_to_delete = supabase.storage.from_(STORAGE_BUCKET).list()
        if not files_to_delete:
            print("Storage bucket is already empty.")
            return

        file_paths = [file["name"] for file in files_to_delete]

        full_paths_to_delete = []
        for path in file_paths:
            is_folder = any(
                f["name"] == path and f["id"] is None for f in files_to_delete
            )
            if is_folder:
                folder_files = supabase.storage.from_(STORAGE_BUCKET).list(path)
                for file in folder_files:
                    full_paths_to_delete.append(f"{path}/{file['name']}")
            else:
                full_paths_to_delete.append(path)

        if not full_paths_to_delete:
            print("No files found to delete.")
            return

        print(
            f"Deleting {len(full_paths_to_delete)} files from bucket '{STORAGE_BUCKET}'..."
        )
        supabase.storage.from_(STORAGE_BUCKET).remove(full_paths_to_delete)
        print("Storage bucket cleared successfully.")

    except Exception as e:
        print(f"Error clearing storage bucket: {e}")
        exit(1)


def clear_database_tables(supabase: Client):
    """Deletes all records from the resumes and candidates tables."""
    print("\n--- Clearing Database Tables ---")
    try:
        print("Deleting all records from 'resumes' table...")
        supabase.table("resumes").delete().gt("id", -1).execute()

        print("Deleting all records from 'candidates' table...")
        supabase.table("candidates").delete().neq(
            "id", "00000000-0000-0000-0000-000000000000"
        ).execute()

        print("Database tables cleared successfully.")
    except Exception as e:
        print(f"Error clearing database tables: {e}")
        exit(1)


def read_resume_data(csv_path: str) -> Optional[pd.DataFrame]:
    """Reads the entire resume dataset from the CSV file."""
    if not os.path.exists(csv_path):
        print(f"CRITICAL: CSV file not found at {csv_path}.")
        return None
    try:
        df = pd.read_csv(csv_path)
        print(f"Successfully read {len(df)} total rows from {csv_path}.")
        return df
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None


def upload_and_get_url(
    supabase: Client, local_path: str, storage_path: str
) -> Optional[str]:
    """Uploads a file, handling existing files, and returns its public URL."""
    if not os.path.exists(local_path):
        print(f"PDF not found at {local_path}. Skipping file upload.")
        return None

    try:
        with open(local_path, "rb") as f:
            file_data = f.read()

        supabase.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=file_data,
            file_options={"content-type": "application/pdf", "upsert": "true"},
        )

        url_response: str = supabase.storage.from_(STORAGE_BUCKET).get_public_url(
            storage_path
        )
        print("Successfully uploaded and got public URL.")
        return url_response
    except StorageException as e:
        print(f"Storage Error during upload of {local_path}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during upload for {local_path}: {e}")
        return None


def process_resume_row(row: pd.Series, supabase: Client, faker: Faker) -> bool:
    """Processes a single row from the DataFrame."""
    try:
        candidate_name: str = faker.name()
        candidate_email: str = (
            f"{candidate_name.lower().replace(' ', '.')}{row.name}@example.com"
        )
        candidate_phone: str = faker.phone_number()

        candidate_response: APIResponse = (
            supabase.table("candidates")
            .insert(
                {
                    "full_name": candidate_name,
                    "email": candidate_email,
                    "phone_number": candidate_phone,
                }
            )
            .execute()
        )

        if not candidate_response.data:
            print(f"Failed to insert candidate. Error: {candidate_response.error}")
            return False

        new_candidate_id: str = candidate_response.data[0]["id"]
        print(f"Inserted candidate '{candidate_name}' with ID: {new_candidate_id}")

        category: str = row["Category"]
        resume_id: int = row["ID"]
        local_pdf_path: str = os.path.join(
            DATASET_FOLDER, PDF_BASE_FOLDER, category, f"{resume_id}.pdf"
        )
        storage_pdf_path: str = f"{category}/{resume_id}.pdf"

        pdf_url = upload_and_get_url(supabase, local_pdf_path, storage_pdf_path)

        resume_text: str = row["Resume_str"]
        resume_response: APIResponse = (
            supabase.table("resumes")
            .insert(
                {
                    "candidate_id": new_candidate_id,
                    "resume_text": resume_text,
                    "pdf_url": pdf_url,
                    "category": category,
                }
            )
            .execute()
        )

        if not resume_response.data:
            print(f"Failed to insert resume data. Error: {resume_response.error}")
            return False

        print(f"Successfully seeded resume for candidate '{candidate_name}'.")
        return True
    except Exception as e:
        print(f"An unexpected error occurred on row {row.name}: {e}")
        return False


def main():
    """Main coordinator function for the seeding script."""
    print("--- Database Seeding Script Initialized ---")

    supabase, faker = initialize_clients()

    # --- Clean Slate: Delete all existing data first ---
    clear_storage_bucket(supabase)
    clear_database_tables(supabase)

    # --- Read ALL data from the CSV ---
    csv_path = os.path.join(DATASET_FOLDER, CSV_FILENAME)
    df = read_resume_data(csv_path)

    if df is None:
        print("--- Seeding Aborted ---")
        return

    successful_seeds: int = 0
    total_rows: int = len(df)
    # Calculate the total number of batches needed
    num_batches: int = (total_rows + BATCH_SIZE - 1) // BATCH_SIZE

    print(f"\n--- Starting to seed {total_rows} records in {num_batches} batches ---")

    # --- Loop through the DataFrame in batches ---
    for i in range(num_batches):
        print(f"\n--- Processing Batch {i + 1}/{num_batches} ---")

        start_index = i * BATCH_SIZE
        end_index = min((i + 1) * BATCH_SIZE, total_rows)

        batch_df = df.iloc[start_index:end_index]

        for index, row in batch_df.iterrows():
            print(f"\n--- Processing record {index + 1}/{total_rows} ---")
            if process_resume_row(row, supabase, faker):
                successful_seeds += 1
            time.sleep(0.05)  # Small delay to be nice to the API

    print("\n--- Seeding Complete ---")
    print(f"Total rows processed: {total_rows}")
    print(f"Successfully seeded records: {successful_seeds}")


if __name__ == "__main__":
    main()
