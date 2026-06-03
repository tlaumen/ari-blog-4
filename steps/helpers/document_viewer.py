from __future__ import annotations

from html import escape


def markdown_to_html(markdown: str) -> str:
    html: list[str] = []
    in_list = False

    for raw_line in markdown.splitlines():
        line = raw_line.strip()

        if not line:
            if in_list:
                html.append("</ul>")
                in_list = False
            continue

        if line.startswith("# "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h1>{escape(line[2:])}</h1>")
        elif line.startswith("## "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h2>{escape(line[3:])}</h2>")
        elif line.startswith("### "):
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<h3>{escape(line[4:])}</h3>")
        elif line.startswith("- "):
            if not in_list:
                html.append("<ul>")
                in_list = True
            html.append(f"<li>{escape(line[2:])}</li>")
        else:
            if in_list:
                html.append("</ul>")
                in_list = False
            html.append(f"<p>{escape(line)}</p>")

    if in_list:
        html.append("</ul>")

    return "\n".join(html)


class DocumentViewer:
    def __init__(self, title: str, markdown: str) -> None:
        self.title = title
        self.markdown = markdown

    def render_html(self) -> str:
        title = escape(self.title)
        body = markdown_to_html(self.markdown)
        return f"""
        <div style='font-family: sans-serif; max-width: 900px; margin: 0 auto; line-height: 1.5;'>
          <h2>{title}</h2>
          <article style='border: 1px solid #ddd; border-radius: 8px; padding: 16px; background: #fafafa;'>
            {body}
          </article>
          <button id='verder' style='margin-top: 12px;'>Verder</button>
        </div>
        <script>
          document.getElementById('verder').addEventListener('click', function () {{
            window.parent.postMessage({{ value: true, summary: 'Document bekeken' }}, '*');
          }});
        </script>
        """
