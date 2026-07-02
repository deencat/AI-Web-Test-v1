"""
Unit tests for test categories — Sprint 2 Test Navigator backend.

Covers CRUD, ownership isolation, duplicate names, delete uncategorize,
GET /tests filter, PATCH /tests/batch/category, and test_category_id on tests.
"""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import MagicMock

from app.api import deps
from app.api.v1.endpoints import test_categories as categories_module
from app.api.v1.endpoints import tests as tests_module
from app.crud import test_case as test_crud
from app.crud import test_category as category_crud
from app.db.base import Base
from app.models.test_case import TestCase, TestType, Priority, TestStatus
from app.models.test_category import TestCategory
from app.models.user import User
from app.schemas.test_case import TestCaseCreate, TestCaseUpdate
from app.schemas.test_category import TestCategoryCreate, TestCategoryUpdate


# ---------------------------------------------------------------------------
# DB fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def db():
    """In-memory SQLite database with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def user_a(db: Session) -> User:
    user = User(
        email="usera@example.com",
        username="usera",
        hashed_password="hash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def user_b(db: Session) -> User:
    user = User(
        email="userb@example.com",
        username="userb",
        hashed_password="hash",
        role="user",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_test_case(
    db: Session,
    user_id: int,
    title: str = "Sample test",
    test_category_id: int | None = None,
) -> TestCase:
    payload = TestCaseCreate(
        title=title,
        description="Description",
        test_type=TestType.E2E,
        priority=Priority.MEDIUM,
        status=TestStatus.PENDING,
        steps=["Step 1"],
        expected_result="Expected",
        test_category_id=test_category_id,
    )
    return test_crud.create_test_case(db=db, test_case=payload, user_id=user_id)


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def _mock_user(user_id: int = 1, role: str = "user") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.role = role
    return user


@pytest.fixture
def categories_app(db: Session) -> FastAPI:
    app = FastAPI()
    app.include_router(categories_module.router, prefix="/test-categories")
    app.dependency_overrides[deps.get_db] = lambda: db
    return app


@pytest.fixture
def tests_app(db: Session) -> FastAPI:
    app = FastAPI()
    app.include_router(tests_module.router, prefix="/tests")
    app.dependency_overrides[deps.get_db] = lambda: db
    return app


# ---------------------------------------------------------------------------
# CRUD tests
# ---------------------------------------------------------------------------

class TestCategoryCRUD:
    def test_create_list_get_update_delete(self, db: Session, user_a: User):
        created = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Billing", color="#FF0000"),
            user_id=user_a.id,
        )
        assert created.id is not None
        assert created.color == "#FF0000"

        categories = category_crud.get_test_categories(db=db, user_id=user_a.id)
        assert len(categories) == 1
        assert categories[0].name == "Billing"

        fetched = category_crud.get_test_category(
            db=db, category_id=created.id, user_id=user_a.id
        )
        assert fetched is not None

        updated = category_crud.update_test_category(
            db=db,
            category_id=created.id,
            user_id=user_a.id,
            updates=TestCategoryUpdate(name="Billing Updated"),
        )
        assert updated.name == "Billing Updated"

        deleted = category_crud.delete_test_category(
            db=db, category_id=created.id, user_id=user_a.id
        )
        assert deleted is True
        assert category_crud.get_test_category(db=db, category_id=created.id, user_id=user_a.id) is None

    def test_test_count_per_category(self, db: Session, user_a: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="QA"),
            user_id=user_a.id,
        )
        _make_test_case(db, user_a.id, test_category_id=category.id)
        _make_test_case(db, user_a.id, test_category_id=category.id)
        _make_test_case(db, user_a.id)

        assert category_crud.get_test_count_for_category(db=db, category_id=category.id) == 2

    def test_delete_nullifies_test_category_id(self, db: Session, user_a: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Temp"),
            user_id=user_a.id,
        )
        test_case = _make_test_case(db, user_a.id, test_category_id=category.id)
        assert test_case.test_category_id == category.id

        category_crud.delete_test_category(db=db, category_id=category.id, user_id=user_a.id)
        db.refresh(test_case)
        assert test_case.test_category_id is None

    def test_ownership_isolation(self, db: Session, user_a: User, user_b: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Private"),
            user_id=user_a.id,
        )
        assert category_crud.get_test_category(db=db, category_id=category.id, user_id=user_b.id) is None
        assert category_crud.delete_test_category(db=db, category_id=category.id, user_id=user_b.id) is False

    def test_duplicate_name_same_user_raises_on_second_create(self, db: Session, user_a: User):
        category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Dup"),
            user_id=user_a.id,
        )
        with pytest.raises(Exception):
            category_crud.create_test_category(
                db=db,
                category=TestCategoryCreate(name="Dup"),
                user_id=user_a.id,
            )

    def test_same_name_different_users_allowed(self, db: Session, user_a: User, user_b: User):
        category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Shared Name"),
            user_id=user_a.id,
        )
        other = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Shared Name"),
            user_id=user_b.id,
        )
        assert other.id is not None


# ---------------------------------------------------------------------------
# Test case filter + assignment
# ---------------------------------------------------------------------------

class TestTestCaseCategoryIntegration:
    def test_filter_by_test_category_id(self, db: Session, user_a: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Filter Cat"),
            user_id=user_a.id,
        )
        in_cat = _make_test_case(db, user_a.id, title="In", test_category_id=category.id)
        _make_test_case(db, user_a.id, title="Out")

        items, total = test_crud.get_test_cases(
            db=db, user_id=user_a.id, test_category_id=category.id
        )
        assert total == 1
        assert items[0].id == in_cat.id

    def test_filter_uncategorized_with_zero(self, db: Session, user_a: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Has Tests"),
            user_id=user_a.id,
        )
        _make_test_case(db, user_a.id, title="Categorized", test_category_id=category.id)
        uncategorized = _make_test_case(db, user_a.id, title="Uncategorized")

        items, total = test_crud.get_test_cases(
            db=db, user_id=user_a.id, test_category_id=0
        )
        assert total == 1
        assert items[0].id == uncategorized.id

    def test_filter_uncategorized_flag(self, db: Session, user_a: User):
        _make_test_case(db, user_a.id, title="Only uncategorized")

        items, total = test_crud.get_test_cases(
            db=db, user_id=user_a.id, uncategorized=True
        )
        assert total == 1

    def test_create_and_update_test_category_id(self, db: Session, user_a: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Assign"),
            user_id=user_a.id,
        )
        created = _make_test_case(db, user_a.id, test_category_id=category.id)
        assert created.test_category_id == category.id

        updated = test_crud.update_test_case(
            db=db,
            test_case_id=created.id,
            updates=TestCaseUpdate(test_category_id=None),
        )
        assert updated.test_category_id is None

    def test_batch_assign_category(self, db: Session, user_a: User, user_b: User):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Bulk"),
            user_id=user_a.id,
        )
        owned = _make_test_case(db, user_a.id, title="Owned")
        foreign = _make_test_case(db, user_b.id, title="Foreign")

        updated, failed = category_crud.batch_assign_test_category(
            db=db,
            test_ids=[owned.id, foreign.id],
            test_category_id=category.id,
            user_id=user_a.id,
        )
        assert updated == 1
        assert failed == [foreign.id]

        db.refresh(owned)
        assert owned.test_category_id == category.id


# ---------------------------------------------------------------------------
# Endpoint tests
# ---------------------------------------------------------------------------

class TestCategoryEndpoints:
    def test_list_includes_test_count(self, categories_app: FastAPI, db: Session, user_a: User):
        categories_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Counted"),
            user_id=user_a.id,
        )
        _make_test_case(db, user_a.id, test_category_id=category.id)

        client = TestClient(categories_app)
        resp = client.get("/test-categories")
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"][0]["test_count"] == 1

    def test_duplicate_name_returns_409(self, categories_app: FastAPI, db: Session, user_a: User):
        categories_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        client = TestClient(categories_app)

        payload = {"name": "Duplicate", "color": "#3B82F6"}
        assert client.post("/test-categories", json=payload).status_code == 201
        resp = client.post("/test-categories", json=payload)
        assert resp.status_code == 409

    def test_user_cannot_access_other_users_category(
        self, categories_app: FastAPI, db: Session, user_a: User, user_b: User
    ):
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Secret"),
            user_id=user_a.id,
        )
        categories_app.dependency_overrides[deps.get_current_user] = lambda: user_b
        client = TestClient(categories_app)

        assert client.get(f"/test-categories/{category.id}").status_code == 404
        assert client.put(
            f"/test-categories/{category.id}",
            json={"name": "Hijack"},
        ).status_code == 404
        assert client.delete(f"/test-categories/{category.id}").status_code == 404


class TestTestsCategoryEndpoints:
    def test_get_tests_filter_by_category(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="API Filter"),
            user_id=user_a.id,
        )
        _make_test_case(db, user_a.id, title="Match", test_category_id=category.id)
        _make_test_case(db, user_a.id, title="No Match")

        client = TestClient(tests_app)
        resp = client.get("/tests", params={"test_category_id": category.id})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["test_category"]["name"] == "API Filter"

    def test_get_tests_uncategorized_filter(
        self, tests_app: FastAPI, db: Session, user_a: User
    ):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Filled"),
            user_id=user_a.id,
        )
        _make_test_case(db, user_a.id, title="Has Cat", test_category_id=category.id)
        _make_test_case(db, user_a.id, title="No Cat")

        client = TestClient(tests_app)
        resp = client.get("/tests", params={"test_category_id": 0})
        assert resp.status_code == 200
        assert resp.json()["total"] == 1
        assert resp.json()["items"][0]["title"] == "No Cat"

    def test_patch_batch_category(self, tests_app: FastAPI, db: Session, user_a: User):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="Batch"),
            user_id=user_a.id,
        )
        test_one = _make_test_case(db, user_a.id, title="One")
        test_two = _make_test_case(db, user_a.id, title="Two")

        client = TestClient(tests_app)
        resp = client.patch(
            "/tests/batch/category",
            json={"test_ids": [test_one.id, test_two.id], "test_category_id": category.id},
        )
        assert resp.status_code == 200
        assert resp.json()["updated"] == 2
        assert resp.json()["failed"] == []

    def test_create_test_with_category_id(self, tests_app: FastAPI, db: Session, user_a: User):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="On Create"),
            user_id=user_a.id,
        )

        client = TestClient(tests_app)
        resp = client.post(
            "/tests",
            json={
                "title": "New Test",
                "description": "Desc",
                "test_type": "e2e",
                "priority": "medium",
                "steps": ["Go"],
                "expected_result": "Done",
                "test_category_id": category.id,
            },
        )
        assert resp.status_code == 201
        assert resp.json()["test_category_id"] == category.id

    def test_update_test_category_id(self, tests_app: FastAPI, db: Session, user_a: User):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        category = category_crud.create_test_category(
            db=db,
            category=TestCategoryCreate(name="On Update"),
            user_id=user_a.id,
        )
        test_case = _make_test_case(db, user_a.id)

        client = TestClient(tests_app)
        resp = client.put(
            f"/tests/{test_case.id}",
            json={"test_category_id": category.id},
        )
        assert resp.status_code == 200
        assert resp.json()["test_category_id"] == category.id

    def test_invalid_category_on_create_returns_400(
        self, tests_app: FastAPI, user_a: User
    ):
        tests_app.dependency_overrides[deps.get_current_user] = lambda: user_a
        client = TestClient(tests_app)
        resp = client.post(
            "/tests",
            json={
                "title": "Bad Cat",
                "description": "Desc",
                "test_type": "e2e",
                "priority": "medium",
                "steps": ["Go"],
                "expected_result": "Done",
                "test_category_id": 9999,
            },
        )
        assert resp.status_code == 400


class TestTestCategoryModel:
    def test_model_columns(self):
        columns = {col.key for col in TestCategory.__table__.columns}
        assert columns == {
            "id",
            "name",
            "description",
            "color",
            "sort_order",
            "user_id",
            "created_at",
            "updated_at",
        }

    def test_unique_user_name_constraint(self):
        constraint_names = {
            constraint.name for constraint in TestCategory.__table__.constraints
        }
        assert "uq_test_categories_user_name" in constraint_names
