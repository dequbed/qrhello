#!/usr/bin/env python

from distutils.core import setup


setup(name="QRHello",
      version="0.0.1",
      description="Zeug nutzen und abgeben via QR-Codes",
      packages=["qrhello"],
      package_dir={"qrhello": "bin"},
      )
