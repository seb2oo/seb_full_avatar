import os
from pathlib import Path
import gradio as gr
import html


import spaces

@spaces.GPU
def dummy_gpu_function():
    """Fonction inutilisée, présente pour satisfaire ZeroGPU."""
    return None


# ============================================================
# CONFIGURATION
# ============================================================

BASE_PATH = Path("/data")
LOG_PATH = BASE_PATH / "logs"

PASSWORDS = [
    p.strip()
    for p in os.environ.get("LOG_PWD", "").split(",")
    if p.strip()
]

BASE_PATH.mkdir(parents=True, exist_ok=True)
LOG_PATH.mkdir(parents=True, exist_ok=True)


# ============================================================
# FONCTIONS
# ============================================================

def authenticate(password):
    if not PASSWORDS:
        return (
            gr.update(visible=True),
            "⚠️ LOG_PWD n'est pas configuré.",
            "",
        )

    if password and password in PASSWORDS:
        return gr.update(visible=True), "✅ Connecté.", ""

    return gr.update(visible=False), "❌ Mot de passe incorrect.", ""


def get_log_files():
    """Liste les fichiers présents dans /data/logs."""
    try:
        return sorted(
            [
                str(p.relative_to(BASE_PATH))
                for p in LOG_PATH.rglob("*")
                if p.is_file() and p.is_relative_to(BASE_PATH)
            ],
            key=str.lower,
        )
    except Exception as e:
        print(f"[LOG VIEWER] Erreur de listage : {e!r}")
        return []


def refresh_files():
    files = get_log_files()
    return gr.update(choices=files, value=None), status_text()


def status_text():
    files = get_log_files()
    return (
        f"**Dossier :** `{LOG_PATH}`\n\n"
        f"**Nombre de fichiers :** {len(files)}\n\n"
        + (
            "\n".join(f"- `{name}`" for name in files)
            if files
            else "Aucun fichier trouvé dans `/data/logs`."
        )
    )


def read_log(selected_file):
    if not selected_file:
        return "", None

    try:
        # Le menu fournit un chemin relatif à /data.
        target = (BASE_PATH / selected_file).resolve()

        if not target.is_relative_to(LOG_PATH.resolve()):
            return "Chemin non autorisé.", None

        if not target.is_file():
            return "Fichier introuvable.", None

        # Évite de charger un fichier énorme en mémoire.
        max_bytes = 2 * 1024 * 1024

        with target.open("rb") as f:
            f.seek(max(0, target.stat().st_size - max_bytes))
            content = f.read().decode("utf-8", errors="replace")

        return html.escape(content), str(target)

    except Exception as e:
        return html.escape(f"Erreur de lecture : {e!r}"), None


def download_log(selected_file):
    if not selected_file:
        return None

    try:
        target = (BASE_PATH / selected_file).resolve()

        if not target.is_relative_to(LOG_PATH.resolve()):
            return None

        return str(target) if target.is_file() else None

    except Exception:
        return None


# ============================================================
# INTERFACE
# ============================================================

with gr.Blocks(title="Logs Viewer") as app:
    gr.Markdown("# 📂 Consultation des logs")

    with gr.Column():
        password = gr.Textbox(
            label="Mot de passe",
            type="password",
        )
        login_btn = gr.Button("Se connecter")
        login_status = gr.Markdown()

    with gr.Column(visible=False) as viewer:
        gr.Markdown("### Fichiers enregistrés dans `/data/logs`")

        files_dropdown = gr.Dropdown(
            choices=get_log_files(),
            label="Fichier de log",
            interactive=True,
        )

        with gr.Row():
            refresh_btn = gr.Button("🔄 Actualiser")
            download_btn = gr.Button("⬇️ Préparer le téléchargement")

        status = gr.Markdown(status_text())
        log_content = gr.Textbox(
            label="Contenu du fichier",
            lines=25,
            max_lines=40,
            interactive=False,
        )
        download_file = gr.File(label="Télécharger le log")

        # Afficher le contenu
        def display_log(filename):
            content, _ = read_log(filename)
            return html.unescape(content)

        files_dropdown.change(
            display_log,
            inputs=files_dropdown,
            outputs=log_content,
        )

        refresh_btn.click(
            refresh_files,
            inputs=[],
            outputs=[files_dropdown, status],
        )

        download_btn.click(
            download_log,
            inputs=files_dropdown,
            outputs=download_file,
        )

    login_btn.click(
        authenticate,
        inputs=password,
        outputs=[viewer, login_status, password],
    )

app.launch(ssr_mode=False)


