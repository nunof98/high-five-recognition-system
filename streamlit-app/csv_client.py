import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict


class CSVClient:
    """Client for interacting with local CSV file storage"""

    def __init__(self):
        """Initialize CSV client"""
        self.csv_file = "data/highfive_data.csv"
        self._ensure_data_file()

    def _ensure_data_file(self):
        """Ensure CSV file and directory exist"""
        os.makedirs("data", exist_ok=True)

        if not os.path.exists(self.csv_file):
            # Create empty CSV with headers
            df = pd.DataFrame(
                columns=["TokenID", "Category", "Message", "SubmittedBy", "Timestamp"]
            )
            df.to_csv(self.csv_file, index=False)

    def _load_data(self) -> pd.DataFrame:
        """Load data from CSV"""
        return pd.read_csv(self.csv_file)

    def _save_data(self, df: pd.DataFrame):
        """Save data to CSV"""
        df.to_csv(self.csv_file, index=False)

    def check_token(self, token: str) -> Optional[Dict]:
        """
        Check if a token exists in CSV

        Args:
            token: The token ID to check

        Returns:
            Dictionary with token data if found, None otherwise
        """
        try:
            df = self._load_data()

            # Find matching token
            match = df[df["TokenID"] == token]

            if not match.empty:
                return match.iloc[0].to_dict()

            return None
        except Exception as e:
            raise Exception(f"Error checking token: {str(e)}")

    def add_token(
        self, token: str, category: str, message: str, submitted_by: str
    ) -> bool:
        """
        Add a new token to CSV

        Args:
            token: The token ID
            category: The token category
            message: The recognition message
            submitted_by: Name of person submitting

        Returns:
            True if successful, False if token already exists
        """
        try:
            # Check if token already exists
            existing = self.check_token(token)
            if existing:
                return False

            # Load current data
            df = self._load_data()

            # Create new row
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            new_row = pd.DataFrame(
                [
                    {
                        "TokenID": token,
                        "Category": category,
                        "Message": message,
                        "SubmittedBy": submitted_by,
                        "Timestamp": timestamp,
                    }
                ]
            )

            # Append and save
            df = pd.concat([df, new_row], ignore_index=True)
            self._save_data(df)

            return True

        except Exception as e:
            raise Exception(f"Error adding token: {str(e)}")

    def get_all_data(self) -> pd.DataFrame:
        """Get all data for admin viewing"""
        return self._load_data()
