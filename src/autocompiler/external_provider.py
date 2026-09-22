from __future__ import annotations
import hashlib, json, os, platform, stat, subprocess, urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from .change_plan import Change, ChangePlan, ApplyEngine
from .environment_manifest import register

@dataclass(frozen=True)
class ExternalRelease:
    provider: str
    capability: str
    version: str
    source: str
    sha256: str
    license: str
    platform: str
    architecture: str
    install_scope: str = "user"
    requires_admin: bool = False
    rollback: str = "delete-owned-provider"
    verification: str = "--version"

    def validate(self) -> None:
        if not self.source.startswith("https://"):
            raise ValueError("external acquisition requires HTTPS")
        if len(self.sha256) != 64:
            raise ValueError("external acquisition requires SHA-256")
        if not self.version or not self.license or not self.rollback or not self.verification:
            raise ValueError("incomplete external provenance")

def sha256(path: str | Path) -> str:
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda:f.read(65536),b""): h.update(chunk)
    return h.hexdigest()

def jq_182_release() -> ExternalRelease:
    machine=platform.machine().lower()
    system=platform.system().lower()
    if machine not in {"amd64","x86_64"}:
        raise ValueError(f"jq E-030 proof supports x64 only, got {machine}")
    if system=="windows":
        return ExternalRelease("jq-1.8.2","json.query","1.8.2",
          "https://github.com/jqlang/jq/releases/download/jq-1.8.2/jq-windows-amd64.exe",
          "a6fc67fedaf9128a3309a1e2ebb8b986aeccf70122ee46d2cb4849e423f0c627","MIT","windows","x64")
    if system=="linux":
        return ExternalRelease("jq-1.8.2","json.query","1.8.2",
          "https://github.com/jqlang/jq/releases/download/jq-1.8.2/jq-linux-amd64",
          "b1c22172dd303f3be49e935aa56aa48a8b7a46e0bc838b4997d3bb451495870f","MIT","linux","x64")
    raise ValueError(f"unsupported E-030 platform: {system}")

def plan_external_release(intent: str, release: ExternalRelease, install_dir: str | Path, consumer: str) -> ChangePlan:
    release.validate()
    name="jq.exe" if release.platform=="windows" else "jq"
    target=Path(install_dir)/name
    return ChangePlan(intent,[Change("download",str(target),f"Acquire {release.capability}",True,{
        **asdict(release),"consumer":consumer
    })],{"zero_cost":True,"no_admin":not release.requires_admin,"no_recurring_ai":True})

def apply_external_plan(plan: ChangePlan, manifest_path: str | Path, authorized: bool=False) -> dict[str,Any]:
    def execute(change: Change) -> bool:
        m=change.metadata; target=Path(change.target)
        try:
            target.parent.mkdir(parents=True,exist_ok=True)
            tmp=target.with_suffix(target.suffix+".download")
            with urllib.request.urlopen(m["source"],timeout=60) as response, tmp.open("wb") as out:
                while True:
                    chunk=response.read(65536)
                    if not chunk: break
                    out.write(chunk)
            if sha256(tmp)!=m["sha256"]:
                tmp.unlink(missing_ok=True); return False
            tmp.replace(target)
            if os.name!="nt": target.chmod(target.stat().st_mode | stat.S_IXUSR)
            return True
        except Exception:
            target.unlink(missing_ok=True)
            return False
    def verify(change: Change) -> bool:
        try:
            if sha256(change.target)!=change.metadata["sha256"]: return False
            p=subprocess.run([change.target,"--version"],text=True,capture_output=True,timeout=10)
            return p.returncode==0 and "jq-1.8.2" in (p.stdout+p.stderr)
        except Exception: return False
    result=ApplyEngine(execute,verify).apply(plan,authorized)
    if result.get("ok"):
        for c in plan.changes:
            m=c.metadata
            register(manifest_path,m["provider"],m["capability"],"autocompiler",m["consumer"])
    return result

def remove_external_provider(plan: ChangePlan, manifest_path: str | Path, consumer: str) -> dict[str,Any]:
    manifest_path=Path(manifest_path)
    data=json.loads(manifest_path.read_text(encoding="utf-8"))
    for change in plan.changes:
        m=change.metadata; entry=data["providers"].get(m["provider"])
        if not entry or entry.get("installed_by")!="autocompiler":
            return {"ok":False,"status":"not_owned"}
        consumers=[x for x in entry.get("consumers",[]) if x!=consumer]
        if consumers:
            entry["consumers"]=consumers
            manifest_path.write_text(json.dumps(data,indent=2),encoding="utf-8")
            return {"ok":True,"status":"retained_for_other_consumers","consumers":consumers}
        Path(change.target).unlink(missing_ok=True)
        del data["providers"][m["provider"]]
    manifest_path.write_text(json.dumps(data,indent=2),encoding="utf-8")
    return {"ok":True,"status":"removed"}

def compile_jq_consumer(provider: str | Path, output_dir: str | Path) -> Path:
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    program=out/"automation.py"; provider=str(Path(provider).resolve())
    program.write_text(
      "import json, subprocess\n"+f"JQ={provider!r}\n"+
      "payload=json.dumps({'items':[1,2,3],'name':'AutoCompiler'})\n"+
      "p=subprocess.run([JQ,'-c','.items | map(. * 2)'],input=payload,text=True,capture_output=True)\n"+
      "print(json.dumps({'ok':p.returncode==0,'result':p.stdout.strip(),'autocompiler_runtime_used':False,'recurring_ai_used':False}))\n"+
      "raise SystemExit(p.returncode)\n",encoding="utf-8")
    return program
