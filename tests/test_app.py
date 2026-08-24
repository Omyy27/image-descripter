"""Tests de los endpoints y de la lógica de Ollama."""

import io
import json

import pytest
from PIL import Image

import app as appmod
import ollama_client
from config import AVAILABLE_MODELS


@pytest.fixture
def client():
    appmod.app.config["TESTING"] = True
    return appmod.app.test_client()


# --- /api/models ---


def test_api_models(client):
    r = client.get("/api/models")
    assert r.status_code == 200
    data = r.get_json()
    assert "models" in data
    assert len(data["models"]) >= 2
    assert all("value" in m and "label" in m for m in data["models"])
    assert set(AVAILABLE_MODELS) <= {m["value"] for m in data["models"]}


# --- /api/chat validación ---


def test_chat_sin_messages(client):
    r = client.post("/api/chat", data={"messages": ""})
    assert r.status_code == 400


def test_chat_json_invalido(client):
    r = client.post("/api/chat", data={"messages": "no-json"})
    assert r.status_code == 400


def test_chat_historial_vacio(client):
    r = client.post("/api/chat", data={"messages": json.dumps([])})
    assert r.status_code == 400


def test_chat_formato_invalido(client):
    r = client.post("/api/chat", data={"messages": json.dumps([{"role": "user"}])})
    assert r.status_code == 400


def test_chat_images_invalidas(client):
    r = client.post(
        "/api/chat",
        data={"messages": json.dumps([{"role": "user", "content": "x", "images": "nope"}])},
    )
    assert r.status_code == 400


# --- /api/chat éxito ---


def test_chat_ok(client, monkeypatch):
    def fake(image_b64, messages, model="qwen2.5vl:3b", timeout=300, max_messages=20):
        return "hola", {"total_ms": 100, "eval_ms": 50, "load_ms": 40}

    monkeypatch.setattr(appmod, "chat_image", fake)
    r = client.post(
        "/api/chat",
        data={
            "model": "qwen2.5vl:3b",
            "messages": json.dumps([{"role": "user", "content": "hola"}]),
        },
    )
    assert r.status_code == 200
    data = r.get_json()
    assert data["reply"] == "hola"
    assert data["timing"]["total_ms"] == 100


def test_chat_modelo_invalido_fallback(client, monkeypatch):
    captured = {}

    def fake(image_b64, messages, model="qwen2.5vl:3b", **kw):
        captured["model"] = model
        return "ok", {"total_ms": 1, "eval_ms": 1, "load_ms": 0}

    monkeypatch.setattr(appmod, "chat_image", fake)
    client.post(
        "/api/chat",
        data={"model": "modelo-inexistente", "messages": json.dumps([{"role": "user", "content": "x"}])},
    )
    assert captured["model"] == "qwen2.5vl:3b"


# --- /describe (API legacy) ---


def test_describe_ok(client, monkeypatch):
    monkeypatch.setattr(appmod, "describe_image", lambda *a, **k: "desc")
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), (255, 0, 0)).save(buf, format="PNG")
    buf.seek(0)
    r = client.post(
        "/describe",
        data={"image": (buf, "x.png"), "context": "desc"},
        content_type="multipart/form-data",
    )
    assert r.status_code == 200
    assert r.get_json()["description"] == "desc"


def test_describe_sin_imagen(client):
    r = client.post("/describe", data={})
    assert r.status_code == 400


# --- /api/stats ---


def test_stats(client, monkeypatch):
    monkeypatch.setattr(appmod, "psutil", None)
    monkeypatch.setattr(appmod, "ping_ollama", lambda: True)
    r = client.get("/api/stats")
    assert r.status_code == 200
    d = r.get_json()
    assert "uptime" in d and "cpu" in d and "ram" in d and "ollama" in d
    assert d["cpu"] is None and d["ram"] is None
    assert d["ollama"] is True


def test_stats_con_psutil(client, monkeypatch):
    class FakeVM:
        used = 1024 * 1024 * 100
        total = 1024 * 1024 * 1000
        percent = 10

    class FakePsutil:
        @staticmethod
        def cpu_percent(interval=None):
            return 25.0

        @staticmethod
        def virtual_memory():
            return FakeVM()

    monkeypatch.setattr(appmod, "psutil", FakePsutil)
    monkeypatch.setattr(appmod, "ping_ollama", lambda: True)
    d = client.get("/api/stats").get_json()
    assert d["cpu"] == 25
    assert d["ram"]["percent"] == 10


# --- ollama_client.chat_image (guard + timing) ---


def test_chat_image_guard(monkeypatch):
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {
                "message": {"content": "ok"},
                "total_duration": 1_000_000_000,
                "eval_duration": 100_000_000,
                "load_duration": 0,
            }

    def fake_post(url, **kw):
        captured["url"] = url
        captured["payload"] = kw["json"]
        return FakeResp()

    monkeypatch.setattr(ollama_client.requests, "post", fake_post)
    msgs = [{"role": "user", "content": "A", "images": ["x"]}] + [
        {"role": r, "content": str(i)} for i in range(40) for r in ("user", "assistant")
    ]
    content, timing = ollama_client.chat_image(None, msgs)
    assert content == "ok"
    assert timing["total_ms"] == 1000
    payload = captured["payload"]
    assert len(payload["messages"]) == 20
    assert payload["messages"][0]["images"] == ["x"]


def test_chat_image_image_b64_fallback(monkeypatch):
    captured = {}

    class FakeResp:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": "ok"}, "total_duration": 0, "eval_duration": 0, "load_duration": 0}

    def fake_post(url, **kw):
        captured["payload"] = kw["json"]
        return FakeResp()

    monkeypatch.setattr(ollama_client.requests, "post", fake_post)
    ollama_client.chat_image("BASE64", [{"role": "user", "content": "hola"}])
    first = captured["payload"]["messages"][0]
    assert first["images"] == ["BASE64"]


# --- comandos de reinicio/detención ---


def test_restart_linux(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(appmod, "_is_windows", lambda: False)
    monkeypatch.setattr(appmod, "_detach", lambda cmd: captured.update(cmd=cmd))
    r = client.post("/api/restart")
    assert r.status_code == 200
    assert "kill" in captured["cmd"] and "app.py" in captured["cmd"]


def test_stop_linux(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(appmod, "_is_windows", lambda: False)
    monkeypatch.setattr(appmod, "_detach", lambda cmd: captured.update(cmd=cmd))
    r = client.post("/api/stop")
    assert r.status_code == 200
    assert "kill" in captured["cmd"] and "Stop-Process" not in captured["cmd"]


def test_restart_windows(client, monkeypatch):
    captured = {}
    monkeypatch.setattr(appmod, "_is_windows", lambda: True)
    monkeypatch.setattr(appmod, "_detach", lambda cmd: captured.update(cmd=cmd))
    r = client.post("/api/restart")
    assert r.status_code == 200
    assert "powershell" in captured["cmd"] and "Stop-Process" in captured["cmd"]


# --- ping_ollama ---


def test_ping_ollama_ok(monkeypatch):
    class FakeResp:
        def raise_for_status(self):
            pass

    monkeypatch.setattr(ollama_client.requests, "get", lambda *a, **k: FakeResp())
    assert ollama_client.ping_ollama() is True


def test_ping_ollama_error(monkeypatch):
    def boom(*a, **k):
        raise ollama_client.requests.RequestException

    monkeypatch.setattr(ollama_client.requests, "get", boom)
    assert ollama_client.ping_ollama() is False