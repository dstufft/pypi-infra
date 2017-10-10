import base64
import os

import invoke
import kubernetes
import kubernetes.client
import kubernetes.client.rest

from . import _utils


VAULT_NAMESPACE = "vault"

CONSUL_GOSSIP_SECRET = "consul-gossip-secret"
CONSUL_VERSION = "0.9.3"


def _consul_image(ctx):
    _utils.pull_image(ctx, "consul")
    _utils.build_image(ctx, "consul", CONSUL_VERSION,
                       build_args={"CONSUL_VERSION": CONSUL_VERSION})
    _utils.push_image(ctx, "consul", CONSUL_VERSION)


@invoke.task
def images(ctx):
    _consul_image(ctx)


@invoke.task
def namespace(ctx):
    ctx.run("kubectl apply -f namespaces/vault.yml")


@invoke.task(namespace)
def consul_secrets(ctx):
    api = kubernetes.client.CoreV1Api()

    # We need to determine if we already have a secret created for consul's
    # gossip layer or not. If not then we want to write one out.
    try:
        api.read_namespaced_secret(CONSUL_GOSSIP_SECRET, VAULT_NAMESPACE)
    except kubernetes.client.rest.ApiException as exc:
        if exc.status != 404:
            raise

        # If we're here then that means we need to create a secret for our
        # consul cluster to use to encrypt the gossip protocol.
        api.create_namespaced_secret(
            VAULT_NAMESPACE,
            kubernetes.client.V1Secret(
                metadata=kubernetes.client.V1ObjectMeta(
                    name=CONSUL_GOSSIP_SECRET,
                    namespace=VAULT_NAMESPACE,
                ),
                string_data={
                    "key": base64.b64encode(os.urandom(16)).decode("ascii"),
                },
            ),
        )


@invoke.task(namespace)
def consul_service(ctx):
    ctx.run("kubectl apply -f services/vault/consul.yml")


@invoke.task(namespace)
def consul_config(ctx):
    ctx.run("kubectl apply -f configmaps/vault/consul.yml")


@invoke.task(namespace, consul_secrets, consul_service, consul_config)
def consul(ctx):
    _utils.render_and_apply(
        ctx,
        "statefulsets/vault/consul.tmpl.yml",
        {
            "image": f"gcr.io/the-psf/consul:v{CONSUL_VERSION}",
        }
    )


@invoke.task(default=True)
def deploy(ctx):
    pass
