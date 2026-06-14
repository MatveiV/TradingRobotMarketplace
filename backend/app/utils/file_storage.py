import os
import shutil
from typing import Optional
from app.config import config

class FileStorage:
    def __init__(self):
        self.upload_dir = config.UPLOAD_DIR
        os.makedirs(self.upload_dir, exist_ok=True)
    
    async def save_file(self, file, strategy_id: int, file_type: str) -> str:
        strategy_dir = os.path.join(self.upload_dir, str(strategy_id))
        os.makedirs(strategy_dir, exist_ok=True)
        
        extension = os.path.splitext(file.filename)[1]
        filename = f"{file_type}{extension}"
        filepath = os.path.join(strategy_dir, filename)
        
        with open(filepath, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        return filepath
    
    def delete_strategy_files(self, strategy_id: int):
        strategy_dir = os.path.join(self.upload_dir, str(strategy_id))
        if os.path.exists(strategy_dir):
            shutil.rmtree(strategy_dir)

file_storage = FileStorage()