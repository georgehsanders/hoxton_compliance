# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the Hotel Compliance Tracker."""

import os

block_cipher = None
ROOT = os.path.abspath(".")

a = Analysis(
    ["run.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[
        (os.path.join("app", "templates"), os.path.join("app", "templates")),
        (os.path.join("app", "static"), os.path.join("app", "static")),
        (os.path.join("app", "stubs"), os.path.join("app", "stubs")),
        ("migrations", "migrations"),
    ],
    hiddenimports=[
        "app",
        "app.compliance",
        "app.models",
        "app.scheduler",
        "app.routes",
        "app.routes.audit",
        "app.routes.dashboard",
        "app.routes.employees",
        "app.routes.export",
        "app.routes.groups",
        "app.routes.managers",
        "app.routes.permits",
        "app.routes.settings",
        "app.stubs",
        "app.stubs.adp_import",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HoxtonCompliance",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
)
