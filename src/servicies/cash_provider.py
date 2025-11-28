import hashlib

from sqlalchemy.orm import Session

from src.orm.html_cash import HTMLCash


class CashProvider():

    @staticmethod
    def get_metric(content, db_session: Session):
        cash = hashlib.sha256(content.decode('utf-8').encode('utf-8')).hexdigest()
        line = db_session.query(HTMLCash).filter_by(code=cash).first()
        if line:
            return line.metric
        return None

    @staticmethod
    def put_metric(content, metric: float, db_session: Session):
        cash = hashlib.sha256(content.decode('utf-8').encode('utf-8')).hexdigest()
        line = HTMLCash(code=cash, metric=metric)
        db_session.add(line)
        db_session.commit()
