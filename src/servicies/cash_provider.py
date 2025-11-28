import hashlib

from sqlalchemy.orm import Session

from src.orm.html_cash import HTMLCash


class CashProvider():

    @staticmethod
    def get_metric(content, db_session: Session):
        cash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        line = db_session.query(HTMLCash).filter_by(code=cash).first()
        if line:
            return line.position, line.word, line.citation, line.score
        return None

    @staticmethod
    def put_metric(content, pos, word, citation_quality, total_score: float, db_session: Session):
        cash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        line = HTMLCash(
            code=cash,
            position=pos,
            word=word,
            citation=citation_quality,
            score=total_score
        )
        db_session.add(line)
        db_session.commit()
