"""Arma datos.js del portal leyendo los atlas YA publicados (GitHub Pages).

Uso:  py tools/construir.py
Baja el datos.js de cada atlas, saca título, grupos y láminas, y crea una
miniatura propia (img/mini/<atlas>-<n>.webp) para que el portal cargue rápido.
"""
import io, json, os, subprocess, sys, urllib.request
from PIL import Image

BASE = "https://canazachyub.github.io/"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ATLAS = [
    {"id": "semio", "repo": "atlas-semiologia-unap", "curso": "Semiología", "icono": "🩺", "color": "#1d6f8a"},
    {"id": "pato", "repo": "atlas-patologia-especial-unap", "curso": "Patología especial", "icono": "🔬", "color": "#9a3b5a"},
    {"id": "inmuno", "repo": "atlas-inmunologia-unap", "curso": "Inmunología", "icono": "🛡️", "color": "#4b5bb8"},
]
EXTRAS = [
    {"id": "memo", "url": BASE + "memo-semiologia/", "curso": "Memo Semiología", "icono": "🧠", "color": "#7a4fd0",
     "desc": "Valores de la historia clínica con técnicas de memoria, ciudad-palacio de Puno, facies y repaso espaciado.",
     "portada": "img/memo.webp", "tipo": "Memorizar"},
    {"id": "anato", "url": BASE + "atlas-anatomico-interactivo/", "curso": "Anatomía", "icono": "🦴", "color": "#b86a2b",
     "desc": "Estructuras anatómicas por temas y subtemas, con visor de imagen y revelado progresivo de nombres.",
     "portada": None, "tipo": "Atlas"},
]


def bajar(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def leer_atlas(repo):
    js = bajar(BASE + repo + "/datos.js").decode("utf-8")
    out = subprocess.run(["node", "-e", "global.window={};eval(require('fs').readFileSync(0,'utf8'));"
                          "process.stdout.write(JSON.stringify(window.ATLAS))"],
                         input=js, capture_output=True, text=True, encoding="utf-8", check=True)
    return json.loads(out.stdout)


def mini(url, destino, ancho=360):
    if os.path.exists(destino):
        return
    im = Image.open(io.BytesIO(bajar(url))).convert("RGB")
    im.thumbnail((ancho, ancho * 2))
    im.save(destino, "WEBP", quality=72, method=6)


def main():
    salida = {"atlas": [], "extras": EXTRAS}
    for a in ATLAS:
        A = leer_atlas(a["repo"])
        grupos = {g["id"]: g for g in A.get("grupos", [])}
        url = BASE + a["repo"] + "/"
        laminas = []
        for l in A["laminas"]:
            src = l.get("mini") or l["img"]
            nombre = f"{a['id']}-{l['n']:02d}.webp"
            mini(url + src, os.path.join(RAIZ, "img", "mini", nombre))
            g = grupos.get(l.get("grupo"), {})
            laminas.append({"n": l["n"], "t": l["titulo"], "s": l.get("subtitulo", ""),
                            "g": g.get("nombre", ""), "gi": g.get("icono", ""),
                            "q": len(l.get("preguntas") or []), "m": "img/mini/" + nombre})
        salida["atlas"].append({**{k: a[k] for k in ("id", "curso", "icono", "color")},
                                "url": url, "titulo": A.get("titulo", ""), "marca": A.get("marca", ""),
                                "desc": A.get("descripcion", ""), "laminas": laminas,
                                "preguntas": sum(x["q"] for x in laminas),
                                "grupos": [{"id": g["id"], "nombre": g.get("nombre", ""), "icono": g.get("icono", "")}
                                           for g in A.get("grupos", [])]})
        print(f"{a['curso']}: {len(laminas)} láminas, {salida['atlas'][-1]['preguntas']} preguntas")
    with open(os.path.join(RAIZ, "datos.js"), "w", encoding="utf-8") as f:
        f.write("window.PORTAL=" + json.dumps(salida, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print("datos.js listo")


if __name__ == "__main__":
    sys.exit(main())
