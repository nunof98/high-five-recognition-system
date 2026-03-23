import io
from datetime import datetime
from typing import Optional

import pandas as pd
import streamlit as st
from cryptography.fernet import Fernet

import github_storage as gh

COLUMNS = ["TokenID", "Category", "Message", "SubmittedBy", "Timestamp"]


def _fernet() -> Fernet:
    key = st.secrets["encryption"]["key"]
    return Fernet(key.encode() if isinstance(key, str) else key)


def _encrypt(df: pd.DataFrame) -> bytes:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return _fernet().encrypt(csv_bytes)


def _decrypt(data: bytes) -> pd.DataFrame:
    csv_bytes = _fernet().decrypt(data)
    return pd.read_csv(io.StringIO(csv_bytes.decode("utf-8")))


class EncryptedCSVClient:
    """Persistent storage backed by an AES-encrypted CSV in GitHub."""

    def __init__(self):
        self._file_path: str = st.secrets["github"]["file_path"]
        self._df: pd.DataFrame = pd.DataFrame(columns=COLUMNS)
        self._sha: Optional[str] = None
        self._load_from_github()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_from_github(self):
        """Fetch and decrypt the remote file (once on startup)."""
        try:
            raw, sha = gh.get_file(self._file_path)
            self._df = _decrypt(raw)
            self._sha = sha
        except FileNotFoundError:
            # First run — no file yet; start with empty DataFrame
            self._df = pd.DataFrame(columns=COLUMNS)
            self._sha = None

    def _save_to_github(self, df: pd.DataFrame, commit_message: str = "Update high-five data"):
        """Encrypt df and push to GitHub, retrying once on SHA conflict."""
        encrypted = _encrypt(df)
        try:
            new_sha = gh.put_file(
                self._file_path, encrypted, self._sha, commit_message
            )
            self._df = df.reset_index(drop=True)
            self._sha = new_sha
        except Exception as exc:
            # On 409 Conflict, refresh SHA and retry once
            if "409" in str(exc) or "422" in str(exc):
                try:
                    _, fresh_sha = gh.get_file(self._file_path)
                    self._sha = fresh_sha
                    new_sha = gh.put_file(
                        self._file_path, encrypted, self._sha, commit_message
                    )
                    self._df = df.reset_index(drop=True)
                    self._sha = new_sha
                except Exception as retry_exc:
                    raise Exception(f"Failed to save data after retry: {retry_exc}") from retry_exc
            else:
                raise

    # ------------------------------------------------------------------
    # Public API (mirrors CSVClient)
    # ------------------------------------------------------------------

    def check_token(self, token: str) -> Optional[dict]:
        """Return row dict if token exists, else None."""
        match = self._df[self._df["TokenID"] == token]
        return match.iloc[0].to_dict() if not match.empty else None

    def add_token(
        self, token: str, category: str, message: str, submitted_by: str
    ) -> bool:
        """Add a new token. Returns False if token already exists."""
        if self.check_token(token):
            return False

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
        updated = pd.concat([self._df, new_row], ignore_index=True)
        self._save_to_github(updated, f"Add token {token}")
        return True

    def get_all_data(self) -> pd.DataFrame:
        """Return a copy of all stored data."""
        return self._df.copy()

    def delete_rows(self, indices: list):
        """Delete rows by DataFrame index and persist."""
        updated = self._df.drop(indices).reset_index(drop=True)
        self._save_to_github(updated, f"Delete {len(indices)} record(s)")

    def delete_all(self):
        """Wipe all data and persist an empty file."""
        empty = pd.DataFrame(columns=COLUMNS)
        self._save_to_github(empty, "Delete all records")


@st.cache_resource
def get_client() -> EncryptedCSVClient:
    """Return a singleton EncryptedCSVClient (loaded once per server process)."""
    return EncryptedCSVClient()
