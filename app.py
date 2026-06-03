from io import BytesIO
from pathlib import Path
import zipfile

from flask import Flask, redirect, render_template_string, request, send_file, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_DIR"] = Path(__file__).resolve().parent / "uploads"


def upload_dir() -> Path:
    directory = Path(app.config["UPLOAD_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def safe_target_name(filename: str) -> str | None:
    base_name = secure_filename(filename)
    if not base_name:
        return None

    directory = upload_dir()
    candidate = base_name
    stem = Path(base_name).stem
    suffix = Path(base_name).suffix
    counter = 1

    while (directory / candidate).exists():
        candidate = f"{stem}_{counter}{suffix}"
        counter += 1

    return candidate


@app.get("/")
def index():
    files = sorted([entry.name for entry in upload_dir().iterdir() if entry.is_file()])
    return render_template_string(
        """
<!doctype html>
<html lang="de">
  <head>
    <meta charset="utf-8">
    <title>Simple Upload</title>
  </head>
  <body>
    <h1>Dateien hochladen</h1>
    <form action="{{ url_for('upload_files') }}" method="post" enctype="multipart/form-data">
      <input type="file" name="files" multiple required>
      <button type="submit">Hochladen</button>
    </form>

    <h2>Vorhandene Dateien</h2>
    {% if files %}
      <ul>
        {% for file in files %}
          <li>{{ file }}</li>
        {% endfor %}
      </ul>
      <a href="{{ url_for('download_all') }}">Alle als ZIP herunterladen</a>
    {% else %}
      <p>Noch keine Dateien hochgeladen.</p>
    {% endif %}
  </body>
</html>
        """,
        files=files,
    )


@app.post("/upload")
def upload_files():
    for file_storage in request.files.getlist("files"):
        target_name = safe_target_name(file_storage.filename)
        if not target_name:
            continue
        file_storage.save(upload_dir() / target_name)

    return redirect(url_for("index"))


@app.get("/download")
def download_all():
    buffer = BytesIO()

    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for file_path in sorted(upload_dir().iterdir()):
            if file_path.is_file():
                archive.write(file_path, arcname=file_path.name)

    buffer.seek(0)
    return send_file(
        buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="uploads.zip",
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
