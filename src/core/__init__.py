"""
AMI - Active Monitor of Internet
Core modules: paths, config, models
"""

from .paths import get_base_path, get_user_data_dir, get_user_config_dir, get_config_path
from .config import load_config, save_config

__all__ = [
    'get_base_path',
    'get_user_data_dir',
    'get_user_config_dir',
    'get_config_path',
    'load_config',
    'save_config',
]
