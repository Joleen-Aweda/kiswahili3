#!/usr/bin/env python3
"""Rebuild the generated inline fetch fallback used by the offline ADT reader."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "offline-preloader.js"
LANGUAGES = ("sw", "sw-TZ")
I18N_FILES = (
    "texts.json", "audios.json", "videos.json", "images.json", "glossary.json",
    "timecode/timecode_output.json",
)


def load_value(relative_path: str):
    path = ROOT / relative_path.removeprefix("./")
    if path.suffix == ".json":
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def main() -> None:
    pages = json.loads((ROOT / "content/pages.json").read_text(encoding="utf-8"))
    paths = [
        "./assets/config.json",
        "./content/pages.json",
        "./content/toc.json",
        "./content/navigation/nav.html",
    ]
    paths.extend(f"./{page['href']}" for page in pages)
    for language in LANGUAGES:
        paths.append(f"./assets/interface_translations/{language}/interface_translations.json")
        paths.extend(f"./content/i18n/{language}/{name}" for name in I18N_FILES)

    unique_paths = list(dict.fromkeys(paths))
    inline = {path: load_value(path) for path in unique_paths}
    payload = json.dumps(inline, ensure_ascii=False, separators=(",", ":"))
    javascript = f'''// offline-preloader.js — auto-generated, do not edit by hand
(function () {{
  var INLINE = {payload};
  var BASE_DIR = (function () {{
    var href = location.href.split("?")[0].split("#")[0];
    return href.slice(0, href.lastIndexOf("/") + 1);
  }})();
  function lookup(url) {{
    var clean = String(url).split("?")[0].split("#")[0];
    if (BASE_DIR && clean.indexOf(BASE_DIR) === 0) clean = clean.slice(BASE_DIR.length);
    if (clean.indexOf("./") === 0) clean = clean.slice(2);
    var withDot = "./" + clean;
    if (Object.prototype.hasOwnProperty.call(INLINE, withDot)) return withDot;
    if (Object.prototype.hasOwnProperty.call(INLINE, clean)) return clean;
    return null;
  }}
  var _realFetch = window.fetch.bind(window);
  window.fetch = function (url, opts) {{
    var raw = (url && typeof url === "object" && typeof url.url === "string") ? url.url : url;
    var key = lookup(raw);
    if (key !== null) {{
      var data = INLINE[key];
      var isJson = key.slice(-5) === ".json";
      var body = isJson ? JSON.stringify(data) : data;
      var contentType = isJson ? "application/json" : "text/html; charset=utf-8";
      return Promise.resolve(new Response(body, {{status: 200, headers: {{"Content-Type": contentType}}}}));
    }}
    return _realFetch(url, opts);
  }};
  if (location.protocol === "file:") {{
    new MutationObserver(function (mutations) {{
      mutations.forEach(function (mutation) {{
        mutation.addedNodes.forEach(function (node) {{
          if (node.nodeType === 1 && node.tagName === "LINK" && node.rel === "manifest") {{
            node.parentNode.removeChild(node);
          }}
        }});
      }});
    }}).observe(document.documentElement, {{childList: true, subtree: true}});
  }}
}})();
'''
    OUTPUT.write_text(javascript, encoding="utf-8")
    print(f"Embedded {len(inline)} quiz-free reader resources in {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
