import os
from unittest.mock import patch, MagicMock
from src.notifier import TelegramNotifier


def test_telegram_notifier_not_configured():
    # When no tokens exist, is_configured should be False and send_message should return False without raising
    notifier = TelegramNotifier(bot_token="", chat_id="")
    assert notifier.is_configured is False
    assert notifier.send_message("Test message") is False


def test_telegram_notifier_skips_without_error():
    notifier = TelegramNotifier(bot_token="ENTER_BOT_TOKEN", chat_id="")
    assert notifier.is_configured is False
    assert notifier.notify_reel_uploaded("Page 1", "123", "Title", "fb_456", 10) is False


@patch("requests.post")
def test_telegram_notifier_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"ok": True}
    mock_post.return_value = mock_resp

    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321")
    assert notifier.is_configured is True

    result = notifier.notify_reel_uploaded(
        page_name="StickWisdom",
        page_id="1291088570765567",
        reel_title="Great Video",
        fb_video_id="reel_111",
        stock_remaining=25,
        route="reel"
    )

    assert result is True
    assert mock_post.called
    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["json"]["chat_id"] == "987654321"
    assert "StickWisdom" in call_kwargs["json"]["text"]
    assert "Great Video" in call_kwargs["json"]["text"]


@patch("requests.post")
def test_telegram_notifier_network_failure_does_not_crash(mock_post):
    mock_post.side_effect = Exception("Connection timeout")

    notifier = TelegramNotifier(bot_token="123456:ABC-DEF", chat_id="987654321")
    # Must return False, not raise
    result = notifier.send_message("Hello")
    assert result is False

