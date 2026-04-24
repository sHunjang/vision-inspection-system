# 검사 이력을 SQLite DB에 저장 및 조회 모듈
import sqlite3
import os
from datetime import datetime
from pathlib import Path


class DBManager:
    """
    검사 이력 SQLite DB 저장 및 조회 클래스
    
    테이블 구조:
        inspection_log
            ├── id          : 자동 증가 기본키
            ├── timestamp   : 검사 일시
            ├── product     : 제품 종류
            ├── camera      : 카메라 이름
            ├── result      : 판정 결과 (OK / DEFECT)
            ├── score       : 이상 점수
            └── threshold   : 판정 임계값
    """
    
    def __init__(self, db_path: str = "data/inspection.db"):
        self.db_path = db_path
        
        # DB 파일이 저장될 폴더 생성
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    
    def _init_db(self):
        """DB 및 테이블 초기화. 없으면 새로 생성"""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS inspection_log (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp   TEXT    NOT NULL,
                    product     TEXT    NOT NULL,
                    camera      TEXT    NOT NULL,
                    result      TEXT    NOT NULL,
                    score       REAL    NOT NULL,
                    threshold   REAL    NOT NULL
                ) 
            """)
        print(f"[DB] 초기화 완료: {self.db_path}")
    
    
    def _connect(self) -> sqlite3.Connection:
        """DB 연결 반환"""
        return sqlite3.connect(self.db_path)

    
    def insert_log(
        self,
        product: str,
        camera: str,
        result: str,
        score: float,
        threshold: float,
    ) -> int:
        """
        검사 결과 DB에 저장
        
        return: 저장된 행의 id
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO inspection_log
                    (timestamp, product, camera, result, score, threshold)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (timestamp, product, camera, result, score, threshold)
            )
        
        return cursor.lastrowid


    def get_logs(
        self,
        limit: int = 100,
        product: str = None,
        result: str = None,
    ) -> list:
        """
        검사 이력 조회
        
        limit: 최대 조회 건수
        product: 특정 제품만 조회 (None이면 전체)
        result: 'OK' 또는 'DEFECT' 필터 (None이면 전체)
        """
        query = "SELECT * FROM inspection_log WHERE 1=1"
        params = []
        
        if product:
            query += "AND product = ?"
            params.append(product)
        
        if result:
            query += "AND result = ?"
            params.append(result)
        
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        
        
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row  # 딕셔너리 형태로 반환
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
        
    
    def get_stats(self, product: str = None) -> dict:
        """
        검사 통계 반환
        반환값: {total, ok_count, defect_count, defect_rate}
        """
        query = "SELECT result, COUNT(*) as cnt FROM inspection_log WHERE 1=1"
        params = []
        
        if product:
            query += " AND product = ?"
            params.append(product)
        
        query += " GROUP BY result"
        
        with self._connect() as conn:
            cursor = conn.execute(query, params)
            rows = {row[0]: row[1] for row in cursor.fetchall()}
        
        ok_count = rows.get("OK", 0)
        defect_count = rows.get("DEFECT", 0)
        total = ok_count + defect_count
        defect_rate = (defect_count / total * 100) if total > 0 else 0.0
        
        return {
            "total": total,
            "ok_count": ok_count,
            "defect_count": defect_count,
            "defect_rate": defect_rate,
        }