#!/usr/bin/env python3
"""Offline C5 renderer. This module has no API, shell, credential or deployment path."""
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent
STAGES = ("bootstrap", "operator", "postgres", "realm", "registry")
NS = "kaas-c5-registry"
REALM = "kaas-c5-poc"
TOKEN = re.compile(r"@@([A-Z_]+)@@")
IMAGE = re.compile(r"^[A-Za-z0-9./:_-]+@sha256:[0-9a-f]{64}$")


def load(inputs, mode="preview"):
    if mode not in {"preview", "candidate"}:
        raise ValueError("unsupported mode")
    if inputs.get("operator_package_version") != "3.3.4-r1":
        raise ValueError("only user-selected operator package 3.3.4-r1 is allowed")
    if inputs.get("realm") != REALM or inputs.get("registry_namespace") != NS:
        raise ValueError("isolated C5 realm and namespace must be preserved")
    for field in ("deployment_authorized", "registration_authorized", "tests_authorized"):
        if inputs.get(field) is not False:
            raise ValueError(f"{field} must remain the JSON boolean false")
    values = inputs["values"]
    release = json.loads((ROOT / "redhat-release-lock.json").read_text())
    for key, field in (("STARTING_CSV", "starting_csv"), ("APP_IMAGE", "app_image"), ("UI_IMAGE", "ui_image")):
        if values.get(key) != release[field]:
            raise ValueError(key + " must match the catalog-verified Red Hat release lock")
    if inputs.get("observed_operator_image") != release["operator_image"]:
        raise ValueError("operator image must match the catalog-verified Red Hat release lock")
    required = set()
    for p in (ROOT / "templates").rglob("*.template"):
        required.update(TOKEN.findall(p.read_text()))
    missing = sorted(k for k in required if not isinstance(values.get(k), str) or not values[k].strip())
    if mode == "candidate":
        if missing:
            raise ValueError("missing values: " + ", ".join(missing))
        if not re.fullmatch(r"[0-9a-f]{40}", values["SOURCE_REVISION"]):
            raise ValueError("SOURCE_REVISION must be a full Git commit SHA")
        for key in ("APP_IMAGE", "UI_IMAGE", "POSTGRES_IMAGE"):
            if not IMAGE.fullmatch(values[key]):
                raise ValueError(key + " must use an immutable sha256 image reference")
        if not values["REPO_URL"].startswith("https://"):
            raise ValueError("REPO_URL must be the reviewed HTTPS repository")
        evidence = inputs.get("promotion_evidence", {})
        expected = json.loads((ROOT / "inputs.json").read_text())["promotion_evidence"]
        if set(evidence) != set(expected) or any(
            not isinstance(v, str) or not v.strip() for v in evidence.values()
        ):
            raise ValueError("all promotion evidence references must be supplied")
    def replace(value):
        if isinstance(value, dict):
            return {k: replace(v) for k, v in value.items()}
        if isinstance(value, list):
            return [replace(v) for v in value]
        if isinstance(value, str):
            return TOKEN.sub(lambda m: values[m[1]] if m[1] not in missing else "UNRESOLVED_" + m[1], value)
        return value
    result = {}
    for stage in STAGES:
        source = ROOT / "templates" / stage / "resources.yaml.template"
        result[stage] = [replace(d) for d in yaml.safe_load_all(source.read_text()) if d]
    validate(result)
    return result, missing


def strict_fields(instance, schema, path=""):
    """Reject unknown CR fields that Kubernetes would otherwise prune silently."""
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        additional = schema.get("additionalProperties")
        if not props and (schema.get("x-kubernetes-preserve-unknown-fields") or additional is None):
            return
        for key, value in instance.items():
            if key in props:
                strict_fields(value, props[key], path + "/" + key)
            elif isinstance(additional, dict):
                strict_fields(value, additional, path + "/" + key)
            elif additional is not True:
                raise ValueError("unknown CR field " + path + "/" + key)
    elif isinstance(instance, list):
        for i, value in enumerate(instance):
            strict_fields(value, schema.get("items", {}), path + "/" + str(i))


def validate(stages):
    docs = [d for stage in STAGES for d in stages[stage]]
    identities = set()
    allowed = {
        "Namespace", "AppProject", "Application", "OperatorGroup", "Subscription",
        "ServiceAccount", "PersistentVolumeClaim", "Service", "ConfigMap", "Deployment",
        "NetworkPolicy", "KeycloakRealmImport", "ApicurioRegistry3", "Route", "Role", "RoleBinding",
    }
    for d in docs:
        kind = d["kind"]
        m = d["metadata"]
        key = (d["apiVersion"], kind, m.get("namespace"), m["name"])
        if key in identities or kind not in allowed:
            raise ValueError("duplicate or disallowed resource: " + repr(key))
        identities.add(key)
        if kind == "Namespace":
            if m["name"] != NS:
                raise ValueError("cannot manage existing namespaces")
        elif kind in {"AppProject", "Application"}:
            if m.get("namespace") != "openshift-gitops" or not m["name"].startswith("kaas-c5-"):
                raise ValueError("invalid C5 GitOps identity")
        elif kind == "KeycloakRealmImport":
            if m.get("namespace") != "keycloak" or m["name"] != "kaas-c5-poc-import":
                raise ValueError("invalid realm import identity")
        elif m.get("namespace") != NS:
            raise ValueError("resource outside isolated registry namespace")
        if kind == "Application":
            if m.get("finalizers") or "automated" in d["spec"].get("syncPolicy", {}):
                raise ValueError("automatic sync/pruning/deletion is forbidden")
        if kind == "Subscription" and d["spec"]["installPlanApproval"] != "Manual":
            raise ValueError("manual OLM approval required")
        if kind == "Role":
            host_create = {"apiGroups": ["route.openshift.io"],
                           "resources": ["routes/custom-host"], "verbs": ["create"]}
            for rule in d["rules"]:
                if "secrets" in rule["resources"] or "*" in rule["resources"] or any(
                    verb not in {"get", "list", "watch", "create", "update", "patch"} for verb in rule["verbs"]
                ):
                    raise ValueError("registry bootstrap role cannot grant Secret/wildcard/delete access")
                if "routes/custom-host" in rule["resources"] and rule != host_create:
                    raise ValueError("custom-host access must grant only namespace-scoped create")
            if m["name"] == "kaas-c5-registry-gitops" and host_create not in d["rules"]:
                raise ValueError("registry bootstrap role requires custom-host create for fixed Route hosts")
        if kind in {"ApicurioRegistry3", "KeycloakRealmImport"}:
            fn = "apicurio-redhat-3.3.4-r1.json" if kind == "ApicurioRegistry3" else "keycloak-redhat-served-26.4.18.json"
            schema_path = ROOT / "validation" / "schemas" / fn
            if kind == "ApicurioRegistry3":
                release = json.loads((ROOT / "redhat-release-lock.json").read_text())
                if hashlib.sha256(schema_path.read_bytes()).hexdigest() != release["crd_schema_sha256"]:
                    raise ValueError("Red Hat bundle schema checksum mismatch")
            schema = json.loads(schema_path.read_text())
            # Only CR spec is asserted here; metadata is validated by later server checks.
            spec_schema = schema["properties"]["spec"]
            jsonschema.Draft7Validator(spec_schema).validate(d["spec"])
            strict_fields(d["spec"], spec_schema, "/spec")
    ri = next(d for d in docs if d["kind"] == "KeycloakRealmImport")
    realm = ri["spec"]["realm"]
    if ri["spec"]["keycloakCRName"] != "keycloak" or realm["realm"] != REALM or realm["id"] != REALM:
        raise ValueError("cannot import or modify existing SSO realms")
    if realm.get("identityProviders") or realm.get("components"):
        raise ValueError("federation/import providers are outside this PoC")
    if {c["clientId"] for c in realm["clients"]} != {"c5-registry-api", "c5-registry-ui", "c5-registry-publisher"}:
        raise ValueError("realm may contain only C5 registry clients")
    reg = next(d for d in docs if d["kind"] == "ApicurioRegistry3")
    auth = reg["spec"]["app"]["auth"]
    if auth["enabled"] is not True or auth["authz"]["enabled"] is not True or auth["anonymousReadsEnabled"] is not False:
        raise ValueError("registry must require authentication and authorization")
    if not auth["authServerUrl"].endswith("/realms/" + REALM) or auth["tls"]["tlsVerificationType"] != "required":
        raise ValueError("registry must trust only the selected HTTPS realm with TLS validation")
    if "sslmode=verify-full" not in reg["spec"]["app"]["storage"]["sql"]["dataSource"]["url"]:
        raise ValueError("database certificate verification required")
    env = {e["name"]: e.get("value") for e in reg["spec"]["app"]["env"]}
    if env.get("QUARKUS_OIDC_TOKEN_AUDIENCE") != "c5-registry-api":
        raise ValueError("registry token audience must be explicit")
    clients = {c["clientId"]: c for c in realm["clients"]}
    for client_id in ("c5-registry-ui", "c5-registry-publisher"):
        audiences = [m.get("config", {}).get("included.client.audience") for m in clients[client_id]["protocolMappers"]]
        if "c5-registry-api" not in audiences:
            raise ValueError("OIDC clients must request the registry API audience")
    if clients["c5-registry-ui"].get("attributes", {}).get("pkce.code.challenge.method") != "S256":
        raise ValueError("UI authorization-code flow requires S256 PKCE")
    if any(c.get("directAccessGrantsEnabled") is not False for c in clients.values()):
        raise ValueError("password grant must remain disabled")
    for d in docs:
        if d["kind"] == "PersistentVolumeClaim" and "Prune=false,Delete=false" != d["metadata"].get("annotations", {}).get("argocd.argoproj.io/sync-options"):
            raise ValueError("registry PVC must be retained")


def render(inputs, out, mode):
    stages, missing = load(inputs, mode)
    if out.exists():
        raise ValueError("output path exists; use a fresh directory")
    out.mkdir(parents=True)
    for stage, docs in stages.items():
        folder = out / stage
        folder.mkdir()
        (folder / "resources.yaml").write_text(
            "# OFFLINE C5 " + mode.upper() + "; NOT AUTHORIZED TO APPLY\n" + yaml.safe_dump_all(docs, sort_keys=False)
        )
        (folder / "kustomization.yaml").write_text(yaml.safe_dump({
            "apiVersion": "kustomize.config.k8s.io/v1beta1", "kind": "Kustomization", "resources": ["resources.yaml"]
        }, sort_keys=False))
    receipt = {"mode": mode, "resource_count": sum(map(len, stages.values())), "missing_values": missing,
               "deployment_authorized": False, "registration_authorized": False, "tests_authorized": False,
               "validation_scope": "exact Red Hat3.3.4-r1 Registry CR spec/strict fields; served Keycloak26.4.18 RealmImport spec; C5 policy; no admission/runtime validation"}
    (out / "render-result.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", type=Path, default=ROOT / "inputs.json")
    parser.add_argument("--mode", choices=["preview", "candidate"], default="preview")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(render(json.loads(args.inputs.read_text()), args.out, args.mode), indent=2))
    except (ValueError, KeyError, jsonschema.ValidationError) as error:
        parser.exit(2, str(error) + "\n")


if __name__ == "__main__":
    main()
