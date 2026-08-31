"""Product, privacy, and runtime information for PDFSilo."""

from __future__ import annotations

import platform

import pymupdf
from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from pdfsilo.ui.metadata import APPLICATION_VERSION
from pdfsilo.ui.resources import application_icon
from pdfsilo.ui.theme import SPACE_LG, SPACE_MD, SPACE_SM, SPACE_XL

HOMEPAGE_URL = "https://pdfsilo.com/"
SUPPORT_URL = "https://pdfsilo.com/faq/"


def _feature_card(
    title: str,
    description: str,
    parent: QWidget,
) -> QFrame:
    card = QFrame(parent)
    card.setObjectName("aboutFeatureCard")
    layout = QVBoxLayout(card)
    layout.setContentsMargins(SPACE_MD, SPACE_MD, SPACE_MD, SPACE_MD)
    layout.setSpacing(SPACE_SM)

    title_label = QLabel(title, card)
    title_label.setObjectName("aboutFeatureTitle")
    description_label = QLabel(description, card)
    description_label.setObjectName("aboutFeatureDescription")
    description_label.setWordWrap(True)

    layout.addWidget(title_label)
    layout.addWidget(description_label)
    layout.addStretch(1)
    return card


class AboutDialog(QDialog):
    """A useful About surface instead of a generic message box."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("aboutDialog")
        self.setWindowTitle("About PDFSilo")
        self.setWindowIcon(application_icon())
        self.setModal(False)
        self.setMinimumSize(660, 570)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(SPACE_XL, SPACE_XL, SPACE_XL, SPACE_LG)
        layout.setSpacing(SPACE_LG)

        hero = QFrame(self)
        hero.setObjectName("aboutHero")
        hero_layout = QHBoxLayout(hero)
        hero_layout.setContentsMargins(
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
            SPACE_LG,
        )
        hero_layout.setSpacing(SPACE_MD)

        self.icon_label = QLabel(hero)
        self.icon_label.setObjectName("aboutIcon")
        self.icon_label.setFixedSize(72, 72)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        identity = QWidget(hero)
        identity_layout = QVBoxLayout(identity)
        identity_layout.setContentsMargins(0, 0, 0, 0)
        identity_layout.setSpacing(3)
        product_name = QLabel("PDFSilo", identity)
        product_name.setObjectName("aboutProductName")
        version = QLabel(f"Version {APPLICATION_VERSION}", identity)
        version.setObjectName("aboutVersion")
        tagline = QLabel(
            "Private, practical PDF tools for your desktop.",
            identity,
        )
        tagline.setObjectName("aboutTagline")
        identity_layout.addWidget(product_name)
        identity_layout.addWidget(version)
        identity_layout.addWidget(tagline)

        hero_layout.addWidget(self.icon_label)
        hero_layout.addWidget(identity, 1)

        features = QGridLayout()
        features.setContentsMargins(0, 0, 0, 0)
        features.setHorizontalSpacing(SPACE_MD)
        features.setVerticalSpacing(SPACE_MD)
        feature_content = (
            (
                "Organize documents",
                "Merge, split, reorder, rotate, and extract pages with visual "
                "review before saving.",
            ),
            (
                "Transform content",
                "Compress PDFs, render pages, extract images, add images, and "
                "build PDFs from image files.",
            ),
            (
                "Protect sensitive files",
                "Encrypt, decrypt, and watermark documents locally with "
                "password-aware workflows.",
            ),
        )
        for column, (title, description) in enumerate(feature_content):
            features.addWidget(
                _feature_card(title, description, self),
                0,
                column,
            )
            features.setColumnStretch(column, 1)

        privacy = QFrame(self)
        privacy.setObjectName("aboutPrivacyCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(
            SPACE_LG,
            SPACE_MD,
            SPACE_LG,
            SPACE_MD,
        )
        privacy_layout.setSpacing(SPACE_SM)
        privacy_title = QLabel("Privacy by design", privacy)
        privacy_title.setObjectName("aboutPrivacyTitle")
        privacy_text = QLabel(
            "Documents are processed on this device—no uploads, accounts, or "
            "telemetry. Passwords are kept only for the active operation and "
            "are never written to application settings.",
            privacy,
        )
        privacy_text.setObjectName("aboutPrivacyText")
        privacy_text.setWordWrap(True)
        privacy_layout.addWidget(privacy_title)
        privacy_layout.addWidget(privacy_text)

        runtime_details = QLabel(
            f"PyMuPDF {pymupdf.__version__}  |  "
            f"PySide6 {PYSIDE_VERSION}  |  "
            f"Python {platform.python_version()} on {platform.system()}",
            self,
        )
        runtime_details.setObjectName("aboutRuntimeDetails")
        runtime_details.setWordWrap(True)

        footer = QHBoxLayout()
        footer.setContentsMargins(0, 0, 0, 0)
        footer.setSpacing(SPACE_SM)

        homepage_button = QPushButton("Website", self)
        homepage_button.setObjectName("aboutHomepageButton")
        homepage_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(HOMEPAGE_URL))
        )
        issues_button = QPushButton("Help & FAQ", self)
        issues_button.setObjectName("aboutIssuesButton")
        issues_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl(SUPPORT_URL))
        )
        license_label = QLabel("BSD 2-Clause license", self)
        license_label.setObjectName("aboutLicenseLabel")

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Close,
            parent=self,
        )
        buttons.setObjectName("aboutButtonBox")
        buttons.rejected.connect(self.close)

        footer.addWidget(homepage_button)
        footer.addWidget(issues_button)
        footer.addWidget(license_label)
        footer.addStretch(1)
        footer.addWidget(buttons)

        layout.addWidget(hero)
        layout.addLayout(features)
        layout.addWidget(privacy)
        layout.addWidget(runtime_details)
        layout.addStretch(1)
        layout.addLayout(footer)
        self.set_dark_mode(False)

    def set_dark_mode(self, dark: bool) -> None:
        """Update theme-sensitive identity assets."""
        icon = application_icon(dark=dark)
        self.setWindowIcon(icon)
        self.icon_label.setPixmap(icon.pixmap(64, 64))


__all__ = ["AboutDialog", "HOMEPAGE_URL", "SUPPORT_URL"]
