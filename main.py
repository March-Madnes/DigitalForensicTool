from PIL import Image
from PIL.ExifTags import TAGS
import filetype
import yara
from flask import Flask, jsonify, request
from werkzeug.utils import secure_filename
import zipfile, os

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "./uploads"
app.config["EXTRACT_FOLDER"] = "./extracted_files"
rules_file = "./rules.yar"


def detect_file_type(file_path):
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    file_kind = filetype.guess(file_bytes)

    if file_kind:
        return {"file_extension": file_kind.extension, "file_mime_type": file_kind.mime}
    else:
        return {"file_extension": None, "file_mime_type": None}


def search_for_signatures(file_path):
    signatures = {
        b"\xFF\xD8\xFF": "JPEG image",
        b"\x89PNG\r\n\x1a\n": "PNG image",
        b"\x47\x49\x46\x38": "GIF image",
        b"\x42\x4D": "BMP image",
        b"\x00\x00\x01\x00": "ICO image",
        b"\x25\x50\x44\x46": "PDF document",
        b"\x50\x4B\x03\x04": "ZIP archive or Microsoft Office Open XML (DOCX, XLSX, PPTX)",
        b"\x1F\x8B": "GZIP archive",
        b"\x42\x5A\x68": "BZIP2 archive",
        b"\x37\x7A\xBC\xAF\x27\x1C": "7-Zip archive",
        b"\x75\x73\x74\x61\x72": "TAR archive",
        b"\xD0\xCF\x11\xE0": "Microsoft Office document (OLE)",
        b"\x00\x01\xBA": "MPEG video",
        b"\x00\x00\x01\xB3": "MPEG video",
        b"\x1A\x45\xDF\xA3": "Matroska video (MKV)",
        b"\x66\x74\x79\x70": "MP4 video",
        b"\x4F\x67\x67\x53": "OGG audio/video",
        b"\x52\x49\x46\x46": "AVI or WAV file",
        b"\x49\x44\x33": "MP3 audio",
        b"\x25\x21": "PostScript document",
        b"\x3C\x3F\x78\x6D\x6C\x20": "XML document",
        b"\x7B\x5C\x72\x74\x66": "Rich Text Format (RTF)",
        b"\xED\xAB\xEE\xDB": "RPM Package",
        b"\x4D\x5A": "Windows Executable (EXE)",
        b"\x7F\x45\x4C\x46": "Linux ELF Executable",
        b"\xCA\xFE\xBA\xBE": "Java class file",
        b"\x6D\x6F\x6F\x76": "QuickTime movie (MOV)",
        b"\xFF\xFB": "MP3 audio file",
    }

    def find_signatures(file_data):
        matched = []
        for signature, file_type in signatures.items():
            if file_data.startswith(signature):
                matched.append(file_type)
        return matched

    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
    except Exception as e:
        return {"error": str(e)}

    matched_signatures = find_signatures(file_data)

    return {"embedded_files": matched_signatures}


def extract_exif(image_path):
    file_type = detect_file_type(image_path)
    exif_details = {}  # Initialize exif_details here
    if file_type["file_mime_type"] and file_type["file_mime_type"].startswith("image"):
        image = Image.open(image_path)
        exif_data = image._getexif()

        if not exif_data:
            return {"exif_data": exif_details}

        for tag, value in exif_data.items():
            tag_name = TAGS.get(tag, tag)
            if isinstance(value, bytes):
                value = value.decode(errors="ignore")
            elif isinstance(value, (list, tuple)):
                value = [str(v) for v in value]
            else:
                value = str(value)
            exif_details[tag_name] = value

        return {"exif_data": exif_details}
    else:
        return {"exif_data": exif_details}


def apply_yara_rules(file_path):
    # Compile YARA rules from the file
    rules = yara.compile(filepath=rules_file)

    # Apply the YARA rules to the file and get matches
    matches = rules.match(file_path)

    # Check for matches
    if matches:
        matched_rules = [match.rule for match in matches]
        return {"matched_yara_rules": matched_rules}
    else:
        return {"matched_yara_rules": None}


def extract_zip(zip_path, extract_to):
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        zip_file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(zip_file_path)

        # Extract the zip file
        extract_to = app.config["EXTRACT_FOLDER"]
        extract_zip(zip_file_path, extract_to)

        results = []
        for root, _, files in os.walk(extract_to):
            for file in files:
                file_path = os.path.join(root, file)
                file_results = {}
                file_results["file_name"] = file
                file_results.update(detect_file_type(file_path))
                file_results.update(search_for_signatures(file_path))
                file_results.update(extract_exif(file_path))
                file_results.update(apply_yara_rules(file_path))
                results.append(file_results)

        return jsonify(results)


if __name__ == "__main__":
    app.run()
