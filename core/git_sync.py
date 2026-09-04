"""Render'daki canlı web servisinin, kendi yazdığı bir dosyayı (subscriptions.json)
git deposuna geri commit'lemesi için. GitHub Actions'ın aksine Render bir git
checkout'u içinde koşmuyor olabilir (Docker imajı build-time'da kopyalanmış bir
kod anlık görüntüsü) - bu yüzden `git commit`/`git push` yerine GitHub'ın REST
Contents API'si kullanılıyor (tek dosyayı base64 ile doğrudan günceller,
yerel bir git deposuna ihtiyaç duymuyor).

GITHUB_PAT ortam değişkeni yoksa (örn. yerel geliştirme) sessizce atlanıyor -
bu opsiyonel bir senkronizasyon adımı, olmadan da API çalışmaya devam eder,
sadece değişiklik GitHub Actions'ın bir sonraki taramasına yansımaz.
"""
import base64
import os

import requests

GITHUB_REPO = "toprakkulekcioglu/fiyat-takip-otomasyonu"
GITHUB_BRANCH = "main"


def push_file(local_path, repo_path: str, message: str) -> bool:
    """`local_path`teki dosyayı depoda `repo_path`e commit'ler. Token yoksa veya
    istek başarısız olursa False döner (çağıran taraf bunu FATAL saymamalı -
    API kullanıcıya normal cevabını vermeye devam etmeli)."""
    token = os.environ.get("GITHUB_PAT")
    if not token:
        print("[git_sync] GITHUB_PAT tanımlı değil, GitHub'a push atlanıyor.", flush=True)
        return False

    api_url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{repo_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        current = requests.get(api_url, headers=headers, params={"ref": GITHUB_BRANCH}, timeout=15)
        sha = current.json().get("sha") if current.status_code == 200 else None

        content_b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
        body = {"message": message, "content": content_b64, "branch": GITHUB_BRANCH}
        if sha:
            body["sha"] = sha

        response = requests.put(api_url, headers=headers, json=body, timeout=15)
        if response.status_code not in (200, 201):
            print(f"[git_sync] PUSH BAŞARISIZ ({response.status_code}): {response.text[:300]}", flush=True)
            return False
        return True
    except Exception as e:
        print(f"[git_sync] PUSH HATASI: {type(e).__name__}: {e}", flush=True)
        return False
