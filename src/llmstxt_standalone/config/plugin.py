"""MkDocs plugin configuration helpers."""

from __future__ import annotations

from typing import Any


def get_llmstxt_config(raw: dict[str, Any]) -> dict[str, Any] | None:
    """Extract llmstxt plugin config from mkdocs.yml plugins.

    MkDocs supports two plugin config styles:

    List form:
        plugins:
          - llmstxt:
              sections: ...

    Mapping form:
        plugins:
          llmstxt:
            sections: ...
    """
    plugins = raw.get("plugins")
    if plugins is None:
        return None

    # Mapping form: plugins is a dict with plugin names as keys
    if isinstance(plugins, dict):
        if "llmstxt" in plugins:
            config = plugins["llmstxt"]
            # Plugin with no options is represented as empty dict or None
            return config if isinstance(config, dict) else {}
        return None

    # List form: plugins is a list of strings or dicts
    for plugin in plugins:
        if isinstance(plugin, dict) and "llmstxt" in plugin:
            config = plugin["llmstxt"]
            return config if isinstance(config, dict) else {}
        if plugin == "llmstxt":
            return {}
    return None
