import pytest
from models import Like


def _like(client, headers, pid):
    return client.post(f"/posts/{pid}/like", headers=headers)


class TestTogglePostLike:

    def test_like_then_unlike(self, client, owner, post):
        r1 = _like(client, owner["headers"], post["post_id"])
        assert r1.status_code == 200
        assert r1.json() == {"liked": True, "likes_count": 1}

        r2 = _like(client, owner["headers"], post["post_id"])
        assert r2.status_code == 200
        assert r2.json() == {"liked": False, "likes_count": 0}

    def test_persisted_in_db(self, client, owner, post, db_session):
        _like(client, owner["headers"], post["post_id"])

        row = db_session.query(Like).filter(Like.post_id == post["post_id"]).first()
        assert row is not None
        assert row.user_id == owner["user_id"]
        assert row.book_id is None

    def test_two_users_count_two(self, client, owner, stranger, post):
        _like(client, owner["headers"], post["post_id"])
        r = _like(client, stranger["headers"], post["post_id"])

        assert r.json() == {"liked": True, "likes_count": 2}

    def test_unlike_only_removes_own(self, client, owner, stranger, post):
        _like(client, owner["headers"], post["post_id"])
        _like(client, stranger["headers"], post["post_id"])

        r = _like(client, owner["headers"], post["post_id"])   # owner
        assert r.json() == {"liked": False, "likes_count": 1}

    def test_missing_post_404(self, client, owner):
        assert _like(client, owner["headers"], 999999).status_code == 404

    def test_requires_auth(self, client, post):
        assert client.post(f"/posts/{post['post_id']}/like").status_code == 401

    def test_double_like_no_duplicate_row(self, client, owner, post, db_session):

        _like(client, owner["headers"], post["post_id"])
        _like(client, owner["headers"], post["post_id"])
        _like(client, owner["headers"], post["post_id"])

        rows = db_session.query(Like).filter(
            Like.post_id == post["post_id"],
            Like.user_id == owner["user_id"],
        ).all()
        assert len(rows) == 1


class TestLikeStatus:

    def test_status_reflects_state(self, client, owner, post):
        url = f"/posts/{post['post_id']}/like"

        assert client.get(url, headers=owner["headers"]).json() == {
            "liked": False, "likes_count": 0}

        _like(client, owner["headers"], post["post_id"])

        assert client.get(url, headers=owner["headers"]).json() == {
            "liked": True, "likes_count": 1}


class TestMyLikes:

    def test_returns_only_my_posts(self, client, owner, stranger):
        p1 = client.post("/posts", json={"title": "A", "description": "a"},
                         headers=owner["headers"]).json()["post_id"]
        p2 = client.post("/posts", json={"title": "B", "description": "b"},
                         headers=stranger["headers"]).json()["post_id"]

        _like(client, owner["headers"], p1)
        _like(client, stranger["headers"], p2)

        titles = [p["title"] for p in
                  client.get("/users/me/likes/posts", headers=owner["headers"]).json()]
        assert titles == ["A"]

    def test_empty_when_nothing_liked(self, client, owner):
        r = client.get("/users/me/likes/posts", headers=owner["headers"])
        assert r.status_code == 200
        assert r.json() == []

    def test_unliked_disappears(self, client, owner, post):
        _like(client, owner["headers"], post["post_id"])
        assert len(client.get("/users/me/likes/posts", headers=owner["headers"]).json()) == 1

        _like(client, owner["headers"], post["post_id"])
        assert client.get("/users/me/likes/posts", headers=owner["headers"]).json() == []

    def test_newest_like_first(self, client, owner):
        ids = []
        for t in ("A", "B", "C"):
            ids.append(client.post("/posts", json={"title": t, "description": "d"},
                                   headers=owner["headers"]).json()["post_id"])

        for pid in ids:
            _like(client, owner["headers"], pid)

        got = [p["title"] for p in
               client.get("/users/me/likes/posts", headers=owner["headers"]).json()]
        assert got == ["C", "B", "A"]

    def test_requires_auth(self, client):
        assert client.get("/users/me/likes/posts").status_code == 401


class TestConstraints:

    def test_check_constraint_rejects_two_targets(self, db_session, owner, post):
        from sqlalchemy.exc import IntegrityError

        db_session.add(Like(user_id=owner["user_id"],
                            post_id=post["post_id"], book_id=1))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()

    def test_check_constraint_rejects_zero_targets(self, db_session, owner):
        from sqlalchemy.exc import IntegrityError

        db_session.add(Like(user_id=owner["user_id"], post_id=None, book_id=None))
        with pytest.raises(IntegrityError):
            db_session.commit()
        db_session.rollback()