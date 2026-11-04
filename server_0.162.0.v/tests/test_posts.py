import os
from datetime import datetime, timedelta
import pytest
from jose import jwt
from models import Post

# helpers

def _login_headers(client, email: str, password: str = "TestPass123!") -> dict:
    r = client.post("/login", data={"username": email, "password": password})
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text}"
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def _make_post(client, headers: dict, **overrides) -> dict:
    body = {
        "title": "Test post",
        "description": "Test description",
        "post_img": ["https://example.com/a.jpg"],
        "file": None,
    }
    body.update(overrides)
    r = client.post("/posts", json=body, headers=headers)
    assert r.status_code == 201, f"create failed: {r.status_code} {r.text}"
    return r.json()


def _expired_token(user_id: int) -> str:
    payload = {
        "user_id": str(user_id),
        "exp": datetime.utcnow() - timedelta(minutes=1),
    }
    return jwt.encode(payload, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))

@pytest.fixture
def owner(client, test_user, auth_headers):
    return {**test_user, "headers": auth_headers}


@pytest.fixture
def stranger(client):
    email = "stranger@example.com"
    r = client.post("/users", json={
        "name": "Stranger",
        "email": email,
        "password": "TestPass123!",
    })
    assert r.status_code == 201, r.text
    return {**r.json(), "headers": _login_headers(client, email)}


@pytest.fixture
def post(client, owner):
    return _make_post(client, owner["headers"], title="Seed post", description="Seed desc")

class TestCreate:

    def test_returns_201_with_full_body(self, client, owner):
        r = client.post("/posts", json={
            "title": "Hello",
            "description": "World",
            "post_img": ["a.jpg", "b.jpg"],
            "file": "doc.pdf",
        }, headers=owner["headers"])

        assert r.status_code == 201, r.text
        d = r.json()
        assert d["title"] == "Hello"
        assert d["description"] == "World"
        assert d["post_img"] == ["a.jpg", "b.jpg"]
        assert d["file"] == "doc.pdf"
        assert d["user_id"] == owner["user_id"]
        assert d["post_id"] > 0
        assert d["created_at"]

    def test_minimal_payload(self, client, owner):
        r = client.post("/posts", json={
            "title": "Only required",
            "description": "No images",
        }, headers=owner["headers"])

        assert r.status_code == 201, r.text
        assert r.json()["post_img"] is None
        assert r.json()["file"] is None

    def test_cannot_spoof_user_id(self, client, owner):
        r = client.post("/posts", json={
            "title": "Spoof",
            "description": "Try to steal",
            "user_id": 99999,
        }, headers=owner["headers"])

        assert r.status_code == 201, r.text
        assert r.json()["user_id"] == owner["user_id"]

    def test_persisted_in_db(self, client, owner, db_session):
        created = _make_post(client, owner["headers"], title="Persisted")

        row = db_session.query(Post).filter(Post.post_id == created["post_id"]).first()
        assert row is not None
        assert row.title == "Persisted"
        assert row.user_id == owner["user_id"]

    def test_empty_post_img_list(self, client, owner):
        r = client.post("/posts", json={
            "title": "Empty imgs",
            "description": "d",
            "post_img": [],
        }, headers=owner["headers"])

        assert r.status_code == 201, r.text
        assert r.json()["post_img"] == []

class TestAuth:

    def test_create_without_token_is_401(self, client):
        r = client.post("/posts", json={"title": "x", "description": "y"})
        assert r.status_code == 401

    def test_create_garbage_token_is_401(self, client):
        r = client.post("/posts",
                        json={"title": "x", "description": "y"},
                        headers={"Authorization": "Bearer not-a-jwt"})
        assert r.status_code == 401

    def test_create_expired_token_is_401(self, client, owner):
        r = client.post("/posts",
                        json={"title": "x", "description": "y"},
                        headers={"Authorization": f"Bearer {_expired_token(owner['user_id'])}"})
        assert r.status_code == 401

    def test_token_without_user_id_is_401(self, client):
        from jose import jwt as _j
        tok = _j.encode({"exp": datetime.utcnow() + timedelta(minutes=5)},
                        os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM"))
        r = client.post("/posts",
                        json={"title": "x", "description": "y"},
                        headers={"Authorization": f"Bearer {tok}"})
        assert r.status_code == 401

    def test_scheme_prefix_is_required(self, client, owner):
        raw = owner["headers"]["Authorization"].split(" ", 1)[1]
        r = client.post("/posts",
                        json={"title": "x", "description": "y"},
                        headers={"Authorization": raw})
        assert r.status_code == 401

class TestValidation:

    @pytest.mark.parametrize("body,case", [
        ({"description": "no title"},                       "title missing"),
        ({"title": "no desc"},                              "description missing"),
        ({"title": "", "description": "ok"},                "title empty"),
        ({"title": "x", "description": ""},                 "description empty"),
        ({"title": "x" * 101, "description": "ok"},         "title > 100"),
        ({"title": "ok", "description": "x" * 221},         "description > 220"),
        ({"title": "ok", "description": "ok", "post_img": "not-a-list"}, "post_img not list"),
        ({"title": "ok", "description": "ok", "post_img": [123]},        "post_img items not str"),
        ({"title": 123, "description": "ok"},               "title wrong type"),
        ({"title": None, "description": "ok"},              "title null"),
        ({"title": "ok", "description": "ok", "file": 42},  "file wrong type"),
    ])
    def test_invalid_body_is_422(self, client, owner, body, case):
        r = client.post("/posts", json=body, headers=owner["headers"])
        assert r.status_code == 422, f"{case}: got {r.status_code} {r.text}"

    def test_title_boundary_100_ok(self, client, owner):
        r = client.post("/posts",
                        json={"title": "x" * 100, "description": "ok"},
                        headers=owner["headers"])
        assert r.status_code == 201

    def test_description_boundary_220_ok(self, client, owner):
        r = client.post("/posts",
                        json={"title": "ok", "description": "x" * 220},
                        headers=owner["headers"])
        assert r.status_code == 201

    def test_broken_json_is_422(self, client, owner):
        r = client.post("/posts",
                        content='{"title":"a","description":"b",}',
                        headers={**owner["headers"], "Content-Type": "application/json"})
        assert r.status_code == 422

class TestReadAll:

    def test_public_no_token(self, client, owner):
        _make_post(client, owner["headers"])
        r = client.get("/posts")
        assert r.status_code == 200
        assert isinstance(r.json(), list)
        assert len(r.json()) == 1

    def test_empty_when_no_posts(self, client):
        r = client.get("/posts")
        assert r.status_code == 200
        assert r.json() == []

    def test_shows_posts_of_all_users(self, client, owner, stranger):
        _make_post(client, owner["headers"], title="owner post")
        _make_post(client, stranger["headers"], title="stranger post")

        titles = {p["title"] for p in client.get("/posts").json()}
        assert titles == {"owner post", "stranger post"}

    def test_newest_first(self, client, owner):
        for i in range(3):
            _make_post(client, owner["headers"], title=f"post {i}")

        ids = [p["post_id"] for p in client.get("/posts").json()]
        assert ids == sorted(ids, reverse=True)

    def test_no_password_leak(self, client, owner):
        _make_post(client, owner["headers"])
        assert "password" not in client.get("/posts").text.lower()

    def test_has_all_expected_keys(self, client, owner):
        _make_post(client, owner["headers"])
        item = client.get("/posts").json()[0]

        assert set(item) == {
            "post_id", "title", "description", "post_img",
            "file", "user_id", "created_at",
        }

class TestReadOne:

    def test_public_no_token(self, client, post):
        r = client.get(f"/posts/{post['post_id']}")
        assert r.status_code == 200
        assert r.json()["post_id"] == post["post_id"]

    def test_stranger_can_read(self, client, post, stranger):
        r = client.get(f"/posts/{post['post_id']}", headers=stranger["headers"])
        assert r.status_code == 200

    def test_not_found_404(self, client):
        r = client.get("/posts/999999")
        assert r.status_code == 404
        assert r.json()["detail"] == "Post not found"

    def test_non_integer_id_422(self, client):
        assert client.get("/posts/abc").status_code == 422

    def test_negative_id_404(self, client):
        assert client.get("/posts/-1").status_code == 404

class TestPut:

    def test_replaces_fields(self, client, owner, post):
        r = client.put(f"/posts/{post['post_id']}", json={
            "title": "Replaced",
            "description": "Replaced desc",
            "post_img": ["new.jpg"],
            "file": "new.pdf",
        }, headers=owner["headers"])

        assert r.status_code == 200, r.text
        assert r.json()["title"] == "Replaced"
        assert r.json()["post_img"] == ["new.jpg"]

    def test_clears_omitted_optional_fields(self, client, owner, post):
        r = client.put(f"/posts/{post['post_id']}",
                       json={"title": "T2", "description": "D2"},
                       headers=owner["headers"])

        assert r.status_code == 200
        assert r.json()["post_img"] is None
        assert r.json()["file"] is None

    def test_requires_mandatory_fields(self, client, owner, post):
        r = client.put(f"/posts/{post['post_id']}",
                       json={"title": "only title"},
                       headers=owner["headers"])
        assert r.status_code == 422

    def test_foreign_post_403(self, client, post, stranger):
        r = client.put(f"/posts/{post['post_id']}",
                       json={"title": "hack", "description": "hack"},
                       headers=stranger["headers"])
        assert r.status_code == 403

    def test_foreign_post_not_modified(self, client, post, stranger, db_session):
        client.put(f"/posts/{post['post_id']}",
                   json={"title": "hack", "description": "hack"},
                   headers=stranger["headers"])

        db_session.expire_all()
        row = db_session.query(Post).filter(Post.post_id == post["post_id"]).first()
        assert row.title == post["title"]

    def test_missing_post_404(self, client, owner):
        r = client.put("/posts/999999",
                       json={"title": "a", "description": "b"},
                       headers=owner["headers"])
        assert r.status_code == 404

    def test_requires_auth(self, client, post):
        r = client.put(f"/posts/{post['post_id']}",
                       json={"title": "a", "description": "b"})
        assert r.status_code == 401

    def test_does_not_change_owner(self, client, owner, post):
        r = client.put(f"/posts/{post['post_id']}",
                       json={"title": "t", "description": "d", "user_id": 99999},
                       headers=owner["headers"])
        assert r.status_code == 200
        assert r.json()["user_id"] == owner["user_id"]

class TestPatch:

    def test_changes_only_sent_field(self, client, owner, post):
        r = client.patch(f"/posts/{post['post_id']}",
                         json={"title": "Patched"},
                         headers=owner["headers"])

        assert r.status_code == 200
        assert r.json()["title"] == "Patched"
        assert r.json()["description"] == post["description"]
        assert r.json()["post_img"] == post["post_img"]

    def test_empty_body_changes_nothing(self, client, owner, post):
        r = client.patch(f"/posts/{post['post_id']}", json={}, headers=owner["headers"])
        assert r.status_code == 200
        assert r.json()["title"] == post["title"]
        assert r.json()["description"] == post["description"]

    def test_explicit_null_clears_field(self, client, owner, post):
        """null ≠ отсутствие поля."""
        r = client.patch(f"/posts/{post['post_id']}",
                         json={"post_img": None},
                         headers=owner["headers"])
        assert r.status_code == 200
        assert r.json()["post_img"] is None

    def test_multiple_fields(self, client, owner, post):
        r = client.patch(f"/posts/{post['post_id']}",
                         json={"title": "T3", "file": "f.pdf"},
                         headers=owner["headers"])
        assert r.status_code == 200
        assert r.json()["title"] == "T3"
        assert r.json()["file"] == "f.pdf"

    def test_invalid_value_422(self, client, owner, post):
        r = client.patch(f"/posts/{post['post_id']}",
                         json={"title": ""},
                         headers=owner["headers"])
        assert r.status_code == 422

    def test_foreign_post_403(self, client, post, stranger):
        r = client.patch(f"/posts/{post['post_id']}",
                         json={"title": "hack"},
                         headers=stranger["headers"])
        assert r.status_code == 403

    def test_missing_post_404(self, client, owner):
        r = client.patch("/posts/999999", json={"title": "x"}, headers=owner["headers"])
        assert r.status_code == 404

    def test_requires_auth(self, client, post):
        assert client.patch(f"/posts/{post['post_id']}", json={"title": "x"}).status_code == 401

    def test_cannot_change_owner(self, client, owner, post):
        r = client.patch(f"/posts/{post['post_id']}",
                         json={"user_id": 99999},
                         headers=owner["headers"])
        assert r.status_code == 200
        assert r.json()["user_id"] == owner["user_id"]

class TestDelete:

    def test_returns_204_empty_body(self, client, owner, post):
        r = client.delete(f"/posts/{post['post_id']}", headers=owner["headers"])
        assert r.status_code == 204
        assert r.content == b""

    def test_removed_from_db(self, client, owner, post, db_session):
        pid = post["post_id"]
        client.delete(f"/posts/{pid}", headers=owner["headers"])

        db_session.expire_all()
        assert db_session.query(Post).filter(Post.post_id == pid).first() is None

    def test_get_after_delete_404(self, client, owner, post):
        pid = post["post_id"]
        client.delete(f"/posts/{pid}", headers=owner["headers"])
        assert client.get(f"/posts/{pid}").status_code == 404

    def test_delete_twice_second_is_404(self, client, owner, post):
        pid = post["post_id"]
        assert client.delete(f"/posts/{pid}", headers=owner["headers"]).status_code == 204
        assert client.delete(f"/posts/{pid}", headers=owner["headers"]).status_code == 404

    def test_foreign_post_403(self, client, post, stranger):
        r = client.delete(f"/posts/{post['post_id']}", headers=stranger["headers"])
        assert r.status_code == 403

    def test_foreign_delete_keeps_post(self, client, post, stranger, db_session):
        client.delete(f"/posts/{post['post_id']}", headers=stranger["headers"])

        db_session.expire_all()
        assert db_session.query(Post).filter(Post.post_id == post["post_id"]).first() is not None

    def test_requires_auth(self, client, post):
        assert client.delete(f"/posts/{post['post_id']}").status_code == 401

class TestPermissionMatrix:

    @pytest.mark.parametrize("method,body", [
        ("put",   {"title": "a", "description": "b"}),
        ("patch", {"title": "a"}),
        ("delete", None),
    ])
    def test_no_token_401(self, client, post, method, body):
        url = f"/posts/{post['post_id']}"
        r = getattr(client, method)(url, json=body) if body else getattr(client, method)(url)
        assert r.status_code == 401

    @pytest.mark.parametrize("method,body", [
        ("put",   {"title": "a", "description": "b"}),
        ("patch", {"title": "a"}),
        ("delete", None),
    ])
    def test_foreign_403(self, client, post, stranger, method, body):
        url = f"/posts/{post['post_id']}"
        r = (getattr(client, method)(url, json=body, headers=stranger["headers"])
             if body else getattr(client, method)(url, headers=stranger["headers"]))
        assert r.status_code == 403

    def test_owner_can_do_everything(self, client, owner):
        pid = _make_post(client, owner["headers"])["post_id"]

        assert client.patch(f"/posts/{pid}", json={"title": "p"},
                            headers=owner["headers"]).status_code == 200
        assert client.put(f"/posts/{pid}", json={"title": "u", "description": "u"},
                          headers=owner["headers"]).status_code == 200
        assert client.delete(f"/posts/{pid}", headers=owner["headers"]).status_code == 204