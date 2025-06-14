import pytest
import yaml
from unittest.mock import patch, mock_open
from claude_code_discord_agent.main import load_config, setup_logging


def test_load_config_success():
    """Test successful configuration loading."""
    mock_config = {
        'discord': {'bot_token': 'test_token', 'prefix': '!'},
        'bot': {'system_prompt': 'test', 'allowed_tools': [], 'max_turns': 2},
        'logging': {'level': 'INFO', 'format': 'test_format'}
    }
    
    with patch('builtins.open', mock_open(read_data=yaml.dump(mock_config))):
        config = load_config()
        assert config is not None
        assert config['discord']['bot_token'] == 'test_token'


def test_load_config_file_not_found():
    """Test configuration loading when file doesn't exist."""
    with patch('builtins.open', side_effect=FileNotFoundError):
        config = load_config()
        assert config is None


def test_load_config_yaml_error():
    """Test configuration loading with invalid YAML."""
    with patch('builtins.open', mock_open(read_data='invalid: yaml: content: [')):
        config = load_config()
        assert config is None


def test_setup_logging():
    """Test logging setup."""
    mock_config = {
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    with patch('logging.basicConfig') as mock_basic_config:
        setup_logging(mock_config)
        mock_basic_config.assert_called_once()


def test_import_main_module():
    """Test that the main module can be imported without errors."""
    import claude_code_discord_agent.main
    assert hasattr(claude_code_discord_agent.main, 'main')
    assert hasattr(claude_code_discord_agent.main, 'ClaudeDiscordBot')