import tkinter as tk
from tkinter import messagebox, Menu
import requests, os, sys, json, base64, hashlib, tempfile, subprocess, re, time

# --- Configuração do App ---
APP_NOME     = "Teste_Versao"
APP_VERSION  = "1.0.1"   # coloque a versão atual
OWNER        = "GibasanLima88"
REPO         = "Teste_Versao" # nome do repositório que você criou no GitHub
VERSAO_PATH  = "versao.json"
BRANCH       = "main"

TIMEOUT = (1.5, 1.5)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (auto-updater)",
    "Accept": "application/vnd.github+json",
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
}

# --- Funções do Auto-Update ---
def _version_tuple(v: str):
    nums = re.findall(r"\d+", v)
    return tuple(int(x) for x in nums) if nums else (0,)

def _baixar_json_conteudo_github(owner, repo, path, branch):
    url_api = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={branch}"
    r = requests.get(url_api, headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    content_b64 = data.get("content", "")
    raw = base64.b64decode(content_b64.replace("\n", ""))
    return json.loads(raw.decode("utf-8"))

def _sha256_arquivo(caminho):
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloco)
    return h.hexdigest()

def _download_com_progresso(url, destino):
    with requests.get(url, headers=HEADERS, stream=True, timeout=TIMEOUT) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)

def _criar_e_executar_bat_swap(caminho_atual, caminho_novo):
    bat_path = os.path.join(tempfile.gettempdir(), f"update_{int(time.time())}.bat")
    exe_nome = os.path.basename(caminho_atual)

    bat = f"""@echo off
:wait
tasklist /FI "IMAGENAME eq {exe_nome}" | find /I "{exe_nome}" >nul
if %errorlevel%==0 (
  timeout /t 1 >nul
  goto wait
)
move /Y "{caminho_novo}" "{caminho_atual}" >nul
start "" "{caminho_atual}"
del "%~f0"
"""
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(bat)

    subprocess.Popen(["cmd", "/c", bat_path], shell=False)

def verificar_e_atualizar(janela=None):
    try:
        info = _baixar_json_conteudo_github(OWNER, REPO, VERSAO_PATH, BRANCH)
        versao_remota = info.get("versao", "").strip()
        url_download  = info.get("url", "").strip()

        if not versao_remota or not url_download:
            raise ValueError("versao.json sem 'versao' ou 'url'.")

        if _version_tuple(versao_remota) <= _version_tuple(APP_VERSION):
            messagebox.showinfo("Atualização", "Você já está na versão mais recente.")
            return

        resp = messagebox.askyesno(
            "Atualização disponível",
            f"Versão atual: {APP_VERSION}\nVersão nova: {versao_remota}\n\n"
            f"Deseja atualizar agora?"
        )
        if not resp:
            return

        tmp_exe = os.path.join(tempfile.gettempdir(), f"{APP_NOME}_{versao_remota}.exe")
        _download_com_progresso(url_download, tmp_exe)

        exe_atual = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(sys.argv[0])
        messagebox.showinfo("Atualizando", "O app será fechado para instalar a nova versão.")
        _criar_e_executar_bat_swap(exe_atual, tmp_exe)

        if janela is not None:
            janela.destroy()
        os._exit(0)

    except Exception as e:
        messagebox.showerror("Erro", f"Falha ao verificar atualização:\n{e}")

# --- Interface Tkinter ---
def main():
    janela = tk.Tk()
    janela.title(f"{APP_NOME} - v{APP_VERSION}")
    janela.geometry("300x200")

    # Botão simples
    btn = tk.Button(janela, text="Clique aqui", command=lambda: messagebox.showinfo("Oi", "versao atualizada"))
    btn.pack(pady=40)

    # Menu
    menu_bar = Menu(janela)
    ajuda_menu = Menu(menu_bar, tearoff=0)
    ajuda_menu.add_command(label="Verificar atualizações...", command=lambda: verificar_e_atualizar(janela))
    menu_bar.add_cascade(label="Ajuda", menu=ajuda_menu)
    janela.config(menu=menu_bar)

    janela.mainloop()

if __name__ == "__main__":
    main()
