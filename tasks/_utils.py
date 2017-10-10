import os
import os.path
import tempfile

import jinja2


def pull_image(ctx, image):
    ctx.run(f"gcloud docker -- pull gcr.io/the-psf/{image} -a")


def build_image(ctx, image, version, directory=None, build_args=None):
    if directory is None:
        directory = f"images/{image}/"

    if build_args is None:
        build_args = {}

    build_arg_str = " ".join(
        f"--build-arg {k}='{v}'"
        for k, v in build_args.items()
    )

    ctx.run(
        f"docker build -t gcr.io/the-psf/{image}:v{version} {build_arg_str} "
        f"{directory}"
    )


def push_image(ctx, image, version):
    ctx.run(f"gcloud docker -- push gcr.io/the-psf/{image}:v{version}")


def render_and_apply(ctx, template, info):
    with open(template, "r", encoding="utf8") as fp:
        jtmpl = jinja2.Template(fp.read())

    with tempfile.TemporaryDirectory() as tmpdir:
        os.makedirs(os.path.dirname(os.path.join(tmpdir, template)))

        with open(os.path.join(tmpdir, template), "w", encoding="utf8") as fp:
            fp.write(jtmpl.render(**info))

        with ctx.cd(tmpdir):
            ctx.run(f"kubectl apply -f {template}")
