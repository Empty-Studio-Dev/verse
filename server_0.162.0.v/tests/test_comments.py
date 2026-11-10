import pytest
from models import Comment


@pytest.fixture
def post(client, owner):
    r = client.post("/posts", json={"title": "T", "description": "D"},
                    headers=owner["headers"])
    assert r.status_code == 201, r.text
    return r.json()


def _comment(client, headers, post_id, text="hello"):
    return client.post(f"/posts/{post_id}/comments",
                       json={"text_comment": text}, headers=headers)


class TestCreateComment:

    def test_201_and_body(self, client, owner, post):
        r = _comment(client, owner["headers"], post["post_id"], "first!")

        assert r.status_code == 201, r.text
        d = r.json()
        assert d["text_comment"] == "first!"
        assert d["post_id"] == post["post_id"]
        assert d["user_id"] == owner["user_id"]
        assert d["user"]["name"] == owner["name"]   # autor
        assert d["comment_id"] > 0
        assert d["created_at"]

    def test_persisted(self, client, owner, post, db_session):
        cid = _comment(client, owner["headers"], post["post_id"]).json()["comment_id"]

        row = db_session.query(Comment).filter(Comment.comment_id == cid).first()
        assert row is not None
        assert row.post_id == post["post_id"]

    def test_cannot_spoof_user_id(self, client, owner, post):
        r = client.post(f"/posts/{post['post_id']}/comments",
                        json={"text_comment": "x", "user_id": 99999},
                        headers=owner["headers"])
        assert r.status_code == 201
        assert r.json()["user_id"] == owner["user_id"]

    def test_cannot_spoof_post_id_in_body(self, client, owner, post):
        r = client.post(f"/posts/{post['post_id']}/comments",
                        json={"text_comment": "x", "post_id": 99999},
                        headers=owner["headers"])
        assert r.status_code == 201
        assert r.json()["post_id"] == post["post_id"]

    def test_on_missing_post_404(self, client, owner):
        r = _comment(client, owner["headers"], 999999)
        assert r.status_code == 404
        assert r.json()["detail"] == "Post not found"

    def test_requires_auth(self, client, post):
        r = client.post(f"/posts/{post['post_id']}/comments",
                        json={"text_comment": "x"})
        assert r.status_code == 401

    @pytest.mark.parametrize("body", [
        {"text_comment": ""},                  # empty
        {},                                    # dont text
        {"text_comment": "x" * 281},           # > 280
        {"text_comment": 123},                 # type
        {"text_comment": None},                # null
    ])
    def test_validation_422(self, client, owner, post, body):
        r = client.post(f"/posts/{post['post_id']}/comments",
                        json=body, headers=owner["headers"])
        assert r.status_code == 422

    def test_boundary_280_ok(self, client, owner, post):
        r = _comment(client, owner["headers"], post["post_id"], "x" * 280)
        assert r.status_code == 201


class TestGetComments:

    def test_public_no_token(self, client, owner, post):
        _comment(client, owner["headers"], post["post_id"])

        r = client.get(f"/posts/{post['post_id']}/comments")
        assert r.status_code == 200
        assert len(r.json()) == 1

    def test_empty_list(self, client, post):
        r = client.get(f"/posts/{post['post_id']}/comments")
        assert r.status_code == 200
        assert r.json() == []

    def test_only_comments_of_this_post(self, client, owner, post):
        other = client.post("/posts", json={"title": "T2", "description": "D2"},
                            headers=owner["headers"]).json()["post_id"]

        _comment(client, owner["headers"], post["post_id"], "for this")
        _comment(client, owner["headers"], other, "for other")

        texts = [c["text_comment"] for c in
                 client.get(f"/posts/{post['post_id']}/comments").json()]
        assert texts == ["for this"]

    def test_oldest_first(self, client, owner, post):
        for i in range(3):
            _comment(client, owner["headers"], post["post_id"], f"c{i}")

        ids = [c["comment_id"] for c in
               client.get(f"/posts/{post['post_id']}/comments").json()]
        assert ids == sorted(ids)

    def test_oldest_first_with_identical_timestamps(self, client, owner, post, db_session):
        from datetime import datetime
        fixed = datetime(2026, 1, 1, 12, 0, 0)
        for t in ("a", "b", "c"):
            db_session.add(Comment(text_comment=t, user_id=owner["user_id"],
                                   post_id=post["post_id"], created_at=fixed))
        db_session.commit()

        ids = [c["comment_id"] for c in
               client.get(f"/posts/{post['post_id']}/comments").json()]
        assert ids == sorted(ids)

    def test_missing_post_404(self, client):
        assert client.get("/posts/999999/comments").status_code == 404

    def test_pagination(self, client, owner, post):
        for i in range(5):
            _comment(client, owner["headers"], post["post_id"], f"c{i}")

        r = client.get(f"/posts/{post['post_id']}/comments?limit=2&offset=1")
        assert r.status_code == 200
        assert [c["text_comment"] for c in r.json()] == ["c1", "c2"]

    def test_limit_validation(self, client, post):
        assert client.get(f"/posts/{post['post_id']}/comments?limit=0").status_code == 422
        assert client.get(f"/posts/{post['post_id']}/comments?limit=101").status_code == 422

    def test_comments_from_different_users(self, client, owner, stranger, post):
        _comment(client, owner["headers"], post["post_id"], "owner says")
        _comment(client, stranger["headers"], post["post_id"], "stranger says")

        names = [c["user"]["name"] for c in
                 client.get(f"/posts/{post['post_id']}/comments").json()]
        assert names == [owner["name"], "Stranger"]

    def test_no_n_plus_one(self, client, owner, post, db_engine):
        for i in range(5):
            _comment(client, owner["headers"], post["post_id"], f"c{i}")

        from sqlalchemy import event
        statements = []

        def _collect(conn, cursor, stmt, params, ctx, many):
            statements.append(stmt)

        event.listen(db_engine, "before_cursor_execute", _collect)
        try:
            client.get(f"/posts/{post['post_id']}/comments")
        finally:
            event.remove(db_engine, "before_cursor_execute", _collect)

        selects = [s for s in statements if s.lstrip().upper().startswith("SELECT")]
        assert len(selects) <= 2, f"too many queries: {len(selects)}\n" + "\n---\n".join(selects)