import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from base_bot import BaseBot


class ConcreteBot(BaseBot):
    def on_startup(self):
        pass

    def on_run_loop(self):
        pass

    def on_shutdown(self):
        pass


class TestBaseBotArguments:

    def test_default_arguments(self):
        bot = ConcreteBot([])
        assert bot.run_every == 60
        assert bot.delay == 0
        assert bot.rig_id == ""
        assert bot.run_less_at_night is False
        assert bot.run_less_at_night_start == 1
        assert bot.run_less_at_night_end == 11

    def test_custom_run_every(self):
        bot = ConcreteBot(["--run-every", "300"])
        assert bot.run_every == 300

    def test_custom_delay(self):
        bot = ConcreteBot(["--delay", "10"])
        assert bot.delay == 10

    def test_custom_rig_id(self):
        bot = ConcreteBot(["--rig-id", "test-bot-1"])
        assert bot.rig_id == "test-bot-1"

    def test_run_less_at_night_flag(self):
        bot = ConcreteBot(["--run-less-at-night"])
        assert bot.run_less_at_night is True

    def test_custom_night_hours(self):
        bot = ConcreteBot([
            "--run-less-at-night-start", "22",
            "--run-less-at-night-end", "6"
        ])
        assert bot.run_less_at_night_start == 22
        assert bot.run_less_at_night_end == 6


class TestNightModeLogic:

    @patch('base_bot.datetime')
    def test_night_mode_disabled_by_default(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 3, 0, 0)  # 3 AM UTC
        bot = ConcreteBot([])
        assert bot.is_run_less_at_night_mode() is False

    @patch('base_bot.datetime')
    def test_night_mode_active_during_night_hours(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 3, 0, 0)  # 3 AM UTC
        bot = ConcreteBot(["--run-less-at-night"])
        assert bot.is_run_less_at_night_mode() is True

    @patch('base_bot.datetime')
    def test_night_mode_inactive_outside_night_hours(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 15, 0, 0)  # 3 PM UTC
        bot = ConcreteBot(["--run-less-at-night"])
        assert bot.is_run_less_at_night_mode() is False

    @patch('base_bot.datetime')
    def test_night_mode_boundary_start(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 1, 0, 0)  # 1 AM UTC (start)
        bot = ConcreteBot(["--run-less-at-night"])
        assert bot.is_run_less_at_night_mode() is True

    @patch('base_bot.datetime')
    def test_night_mode_boundary_end(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 11, 0, 0)  # 11 AM UTC (end)
        bot = ConcreteBot(["--run-less-at-night"])
        assert bot.is_run_less_at_night_mode() is True

    @patch('base_bot.datetime')
    def test_custom_night_hours(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 14, 0, 0)  # 2 PM UTC
        bot = ConcreteBot([
            "--run-less-at-night",
            "--run-less-at-night-start", "12",
            "--run-less-at-night-end", "18"
        ])
        assert bot.is_run_less_at_night_mode() is True


class TestKillSwitch:

    def test_no_remote_config(self):
        bot = ConcreteBot([])
        assert bot.is_kill_switch_called() is False

    def test_kill_switch_active(self):
        bot = ConcreteBot([])
        bot.remote_config = Mock(kill_switch=True)
        assert bot.is_kill_switch_called() is True

    def test_kill_switch_inactive(self):
        bot = ConcreteBot([])
        bot.remote_config = Mock(kill_switch=False)
        assert bot.is_kill_switch_called() is False


class TestUpdateLoop:

    @patch('log.logging')
    def test_update_loop_skip_on_kill_switch(self, mock_logging):
        bot = ConcreteBot([])
        bot.get_remote_config = Mock(return_value=Mock(kill_switch=True))
        bot.on_run_loop = Mock()
        bot.save_remote_status = Mock()

        bot._update_loop()

        bot.on_run_loop.assert_not_called()
        bot.save_remote_status.assert_not_called()

    @patch('log.logging')
    @patch('base_bot.datetime')
    def test_update_loop_skip_during_night_mode(self, mock_datetime, mock_logging):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 1, 3, 0, 0)
        bot = ConcreteBot(["--run-less-at-night"])
        bot.on_run_loop = Mock()
        bot.save_remote_status = Mock()

        bot._update_loop()

        bot.on_run_loop.assert_not_called()
        bot.save_remote_status.assert_not_called()

    @patch('log.logging')
    def test_update_loop_executes_normally(self, mock_logging):
        bot = ConcreteBot([])
        bot.on_run_loop = Mock()
        bot.save_remote_status = Mock()

        bot._update_loop()

        bot.on_run_loop.assert_called_once()
        bot.save_remote_status.assert_called_once()


class TestAbstractMethods:

    def test_cannot_instantiate_base_bot(self):
        with pytest.raises(TypeError):
            BaseBot([])

    def test_concrete_implementation_required(self):
        class IncompleteBot(BaseBot):
            pass

        with pytest.raises(TypeError):
            IncompleteBot([])


class TestUtilityMethods:

    @patch('base_bot.datetime')
    def test_get_current_datetime_format(self, mock_datetime):
        mock_datetime.utcnow.return_value = datetime(2025, 1, 15, 10, 30, 45)
        result = BaseBot.get_current_datetime()
        assert result == "2025-01-15T10:30:45Z"
