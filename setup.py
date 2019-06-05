from setuptools import setup, find_packages

setup(
    name="postgrest",
    author="james-callahan",
    author_email="james@konghq.com",
    url="https://github.com/Kong/py-postgrest/",
    description="A client for PostgREST APIs",
    long_description=open("README.md").read(),
    project_urls={
        "Homepage": "https://github.com/Kong/py-postgrest/",
        "Source": "https://github.com/Kong/py-postgrest/",
        "Tracker": "https://github.com/Kong/py-postgrest/issues",
    },
    long_description_content_type="text/markdown",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries",
    ],
    keywords=[
        "postgrest",
        "http",
        "client",
    ],
    setup_requires=["setuptools_scm"],
    use_scm_version=True,
    packages=find_packages(),
    zip_safe=True,
    install_requires=["aiohttp"],
)
