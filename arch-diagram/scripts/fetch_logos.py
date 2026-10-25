#!/usr/bin/env python3
"""Download official brand/project logos that the `diagrams` icon set does not ship, as 512px PNGs.

Usage:
    python3 fetch_logos.py [out_dir]            # default: <skill>/logos
    python3 fetch_logos.py --list               # show every logo and its source

Sources (all public): simple-icons + @iconify-json/logos npm tarballs, and the projects' own GitHub repos /
CNCF artwork. Logos are trademarks of their owners — use them only to identify the product in diagrams.
Add a new logo by appending one line to SOURCES.
"""
import io
import json
import os
import re
import sys
import tarfile
import urllib.request

import cairosvg

HERE = os.path.dirname(os.path.abspath(__file__))
GH = "https://raw.githubusercontent.com"
NPM_SI = "https://registry.npmjs.org/simple-icons/-/simple-icons-16.35.0.tgz"
NPM_LOGOS = "https://registry.npmjs.org/@iconify-json/logos/-/logos-1.2.17.tgz"

# name -> (kind, ref)
#   si:<slug>        simple-icons mono SVG, filled with the brand colour from simple-icons data
#   iconify:<key>    @iconify-json/logos full-colour SVG
#   url:<url>        direct SVG or PNG
SOURCES = {
    # supply chain / security
    "sonatype":     ("si", "sonatype"),
    "coverity":     ("iconify", "coverity"),
    "blackduck":    ("url", f"{GH}/blackducksoftware/blackduck-alert/master/ui/src/main/img/BlackDuckIcon.png"),
    "cosign":       ("url", f"{GH}/sigstore/community/main/artwork/cosign/icons/color/sigstore_cosign-icon-color.png"),
    "kyverno":      ("url", f"{GH}/kyverno/kyverno/main/img/logo.png"),
    "tetragon":     ("url", f"{GH}/cilium/tetragon/main/docs/static/favicons/favicon-1024.png"),
    "keycloak":     ("si", "keycloak"),
    # kubernetes / networking / compute
    "gateway-api":  ("url", f"{GH}/kubernetes-sigs/gateway-api/main/site/static/images/logo/logo.svg"),
    "cilium":       ("url", f"{GH}/cilium/cilium/main/Documentation/images/logo-solo.svg"),
    "karpenter":    ("url", f"{GH}/aws/karpenter-provider-aws/main/website/static/favicon.svg"),
    "keda":         ("url", f"{GH}/cncf/artwork/main/projects/keda/icon/color/keda-icon-color.png"),
    "nvidia":       ("si", "nvidia"),
    # observability
    "alloy":        ("url", f"{GH}/grafana/alloy/main/docs/sources/assets/alloy_icon_orange.svg"),
    # AI
    "agentgateway": ("url", f"{GH}/agentgateway/agentgateway/main/ui/src/assets/agw-icon.svg"),
    "modelcontextprotocol": ("si", "modelcontextprotocol"),
    "vllm":         ("si", "vllm"),
    "langgraph":    ("si", "langgraph"),
    "openai":       ("iconify", "openai-icon"),
    "anthropic":    ("iconify", "anthropic-icon"),
    "claude":       ("iconify", "claude-icon"),
    "langchain":    ("iconify", "langchain-icon"),
    "crewai":       ("iconify", "crewai"),
    # collaboration
    "jira":         ("iconify", "jira"),
    "confluence":   ("iconify", "confluence"),
}
# Known gaps (no public official asset found): Seeker IAST, Bottlerocket — use c.placeholder() / text.


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def tar_member(blob, suffix):
    with tarfile.open(fileobj=io.BytesIO(blob)) as t:
        for m in t.getmembers():
            if m.name.endswith(suffix):
                return t.extractfile(m).read()
    raise KeyError(suffix)


def to_png(data, out, is_svg):
    if is_svg:
        cairosvg.svg2png(bytestring=data, write_to=out, output_width=512)
    else:
        open(out, "wb").write(data)


def main():
    if "--list" in sys.argv:
        for k, (kind, ref) in SOURCES.items():
            print(f"{k:22s} {kind:8s} {ref}")
        return
    out_dir = next((a for a in sys.argv[1:] if not a.startswith("-")), os.path.join(HERE, "..", "logos"))
    os.makedirs(out_dir, exist_ok=True)
    si_tgz = logos_tgz = si_hex = iconify = None
    ok, failed = [], []
    for name, (kind, ref) in SOURCES.items():
        dst = os.path.join(out_dir, name + ".png")
        try:
            if kind == "si":
                if si_tgz is None:
                    si_tgz = get(NPM_SI)
                    data = json.loads(tar_member(si_tgz, "data/simple-icons.json"))
                    data = data if isinstance(data, list) else data.get("icons", data)
                    slug = lambda t: re.sub(r"[^a-z0-9]", "", t.lower().replace("+", "plus").replace(".", "dot"))
                    si_hex = {i.get("slug", slug(i["title"])): i["hex"] for i in data}
                svg = tar_member(si_tgz, f"icons/{ref}.svg").decode()
                svg = svg.replace("<path ", f'<path fill="#{si_hex.get(ref, "333333")}" ', 1)
                cairosvg.svg2png(bytestring=svg.encode(), write_to=dst, output_width=512, output_height=512)
            elif kind == "iconify":
                if iconify is None:
                    logos_tgz = get(NPM_LOGOS)
                    iconify = json.loads(tar_member(logos_tgz, "icons.json"))
                ic = iconify["icons"][ref]
                w = ic.get("width", iconify.get("width", 256))
                h = ic.get("height", iconify.get("height", 256))
                svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
                       f'width="{w}" height="{h}">{ic["body"]}</svg>')
                cairosvg.svg2png(bytestring=svg.encode(), write_to=dst, output_width=512)
            else:
                to_png(get(ref), dst, ref.lower().endswith(".svg"))
            ok.append(name)
        except Exception as e:  # keep going; report at the end
            failed.append(f"{name}: {e}")
    print(f"{len(ok)} logos -> {os.path.abspath(out_dir)}")
    for f in failed:
        print("FAILED", f)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
