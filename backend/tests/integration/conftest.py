"""Integration test fixtures — requires INTEGRATION_TEST=1 and real DB."""

import os

import pytest
from sqlalchemy import text

from db.session import SessionLocal, engine

# Skip entire module if INTEGRATION_TEST env var not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("INTEGRATION_TEST"),
    reason="Set INTEGRATION_TEST=1 to run integration tests",
)


@pytest.fixture()
def db_session():
    """Provide a transactional DB session that rolls back after each test.

    Uses SAVEPOINT so that code under test can call commit() without
    actually persisting data beyond the test boundary.
    """
    assert engine is not None, "DATABASE_URL not configured"
    assert SessionLocal is not None, "SessionLocal not configured"

    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection)

    # Nested transaction (SAVEPOINT) — allows tested code to call commit()
    nested = connection.begin_nested()

    # Re-open a new SAVEPOINT each time the session commits
    @pytest.fixture(autouse=True)
    def _restart_savepoint():
        nonlocal nested
        # This is handled via event listener below
        pass

    from sqlalchemy import event

    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction_ended):
        nonlocal nested
        if not nested.is_active:
            nested = connection.begin_nested()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def clean_test_data(db_session):
    """Delete any test data rows created with asset_id starting with '__TEST'."""
    yield
    db_session.execute(
        text("DELETE FROM price_daily WHERE asset_id LIKE '__TEST%'")
    )
    db_session.execute(
        text("DELETE FROM job_run WHERE job_name LIKE '__TEST%'")
    )
    db_session.commit()
