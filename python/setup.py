import pathlib
from setuptools import setup, find_packages

README = (pathlib.Path(__file__).parent / "README.md").read_text(encoding="utf-8")

setup(
    name="cookielessaudiences",
    version="1.0.0",
    description="Python client for the Cookieless Audiences API: page-level audience segmentation (demographics, interests, purchase intent, B2B firmographics, personas) and IAB content categorization for any URL, with no cookies and no PII.",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Alpha Quantum",
    author_email="info@alpha-quantum.com",
    url="https://www.cookielessaudiences.com",
    project_urls={
        "Homepage": "https://www.cookielessaudiences.com",
        "Documentation": "https://www.cookielessaudiences.com/api.php",
        "Source": "https://github.com/explainableaixai/cookielessaudiences",
        "Mirror": "https://gitlab.com/url-classifications/cookielessaudiences",
        "Tracker": "https://www.cookielessaudiences.com/contact.php",
        "Pricing": "https://www.cookielessaudiences.com/pricing.php",
    },
    license="MIT",
    packages=find_packages(exclude=("tests", "test")),
    python_requires=">=3.7",
    install_requires=["requests>=2.20.0"],
    keywords=["cookieless", "audience segmentation", "iab audience taxonomy", "iab categorization", "contextual targeting",
              "seller defined audiences", "purchase intent", "adtech", "media planning", "inventory curation",
              "audience data", "privacy-safe advertising", "domain audience data"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.12",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Scientific/Engineering :: Information Analysis",
    ],
)
